// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Libraries/LibAsset.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ICorrectSwap.sol";
import "../Interfaces/IStargate.sol";
import "../Interfaces/IStargateFactory.sol";
import "../Interfaces/IStargatePool.sol";
import "../Interfaces/IStargateFeeLibrary.sol";
import "../Interfaces/IStargateReceiver.sol";
import "../Libraries/LibDiamond.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Errors/GenericErrors.sol";
import "../Helpers/Swapper.sol";
import "../Interfaces/IStargateEthVault.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibBytes.sol";

/// @title Stargate Facet
/// @author SoOmnichain
/// @notice Provides functionality for bridging through Stargate
contract StargateFacet is ISo, Swapper, ReentrancyGuard, IStargateReceiver {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"2bd10e5dcb5694caec513d6d8fa1fd90f6a026e0e9320d7b6e2f8e49b93270d1"; //keccak256("com.so.facets.stargate");

    struct Storage {
        address stargate; // stargate route address
        uint16 srcStargateChainId; // The stargate chain id of the source/current chain
    }

    /// Types ///

    struct StargateData {
        uint256 srcStargatePoolId; // The stargate pool id of the source chain
        uint16 dstStargateChainId; // The stargate chain id of the destination chain
        uint256 dstStargatePoolId; // The stargate pool id of the destination chain
        uint256 minAmount; // The stargate min amount
        uint256 dstGasForSgReceive; // destination gas for sgReceive
        address payable dstSoDiamond; // destination SoDiamond address
    }

    /// Events ///

    event StargateInitialized(address stargate, uint256 chainId);

    /// Init ///

    /// @notice Initializes local variables for the Stargate facet
    /// @param _stargate address of the canonical Stargate router contract
    /// @param _chainId chainId of this deployed contract
    function initStargate(address _stargate, uint16 _chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (_stargate == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.stargate = _stargate;
        s.srcStargateChainId = _chainId;
        emit StargateInitialized(_stargate, _chainId);
    }

    /// External Methods ///

    /// @notice Bridges tokens via Stargate
    /// @param _soDataNo Data for tracking cross-chain transactions and a
    ///                portion of the accompanying cross-chain messages
    /// @param _swapDataSrcNo Contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param _stargateData Data used to call Stargate's router for swap
    /// @param _swapDataDstNo Contains a set of Swap transaction data executed
    ///                     on the target chain.
    function soSwapViaStargate(
        ISo.NormalizedSoData calldata _soDataNo,
        LibSwap.NormalizedSwapData[] calldata _swapDataSrcNo,
        StargateData calldata _stargateData,
        LibSwap.NormalizedSwapData[] calldata _swapDataDstNo
    ) external payable nonReentrant {
        bool _hasSourceSwap;
        bool _hasDestinationSwap;
        uint256 _bridgeAmount;

        ISo.SoData memory _soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory _swapDataSrc = LibCross.denormalizeSwapData(
            _swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            LibAsset.depositAsset(_soData.sendingAssetId, _soData.amount);
        }
        if (_swapDataSrc.length == 0) {
            deposit(
                _soData.sendingAssetId,
                _getStargateTokenByPoolId(_stargateData.srcStargatePoolId),
                _soData.amount
            );
            _bridgeAmount = _soData.amount;
            _hasSourceSwap = false;
        } else {
            require(
                _soData.amount == _swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            _bridgeAmount = this.executeAndCheckSwaps(_soData, _swapDataSrc);
            deposit(
                _swapDataSrc[_swapDataSrc.length - 1].receivingAssetId,
                _getStargateTokenByPoolId(_stargateData.srcStargatePoolId),
                _bridgeAmount
            );
            _hasSourceSwap = true;
        }
        uint256 _stargateValue = _getStargateValue(_soData);
        bytes memory _payload = encodeStargatePayload(
            _soDataNo,
            _swapDataDstNo
        );

        if (_swapDataDstNo.length > 0) {
            _hasDestinationSwap = true;
        }

        _startBridge(_stargateData, _stargateValue, _bridgeAmount, _payload);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            _hasSourceSwap,
            _hasDestinationSwap,
            _soData
        );
    }

    /// @dev Overload sgReceive of IStargateReceiver, called by stargate router
    function sgReceive(
        uint16,
        bytes memory,
        uint256,
        address _token,
        uint256 _amount,
        bytes memory _payload
    ) external {
        if (LibAsset.getOwnBalance(_token) < _amount) {
            require(
                !IStargateEthVault(_token).noUnwrapTo(address(this)),
                "Token error"
            );
            require(
                LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID) >= _amount,
                "Not enough"
            );
            _token = LibAsset.NATIVE_ASSETID;
        }

        (
            ISo.NormalizedSoData memory _soDataNo,
            LibSwap.NormalizedSwapData[] memory _swapDataDstNo
        ) = decodeStargatePayload(_payload);

        ISo.SoData memory _soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory _swapDataDst = LibCross.denormalizeSwapData(
            _swapDataDstNo
        );

        if (gasleft() < getTransferGas()) revert("Not enough gas!");

        uint256 _swapGas = gasleft().sub(getTransferGas());
        try
            this.remoteSoSwap{gas: _swapGas}(
                _token,
                _amount,
                _soData,
                _swapDataDst
            )
        {} catch Error(string memory revertReason) {
            withdraw(_token, _token, _amount, _soData.receiver);
            emit SoTransferFailed(
                _soData.transactionId,
                revertReason,
                bytes(""),
                _soData
            );
        } catch (bytes memory returnData) {
            withdraw(_token, _token, _amount, _soData.receiver);
            emit SoTransferFailed(
                _soData.transactionId,
                "",
                returnData,
                _soData
            );
        }
    }

    /// @dev convenient for sgReceive to catch exceptions
    function remoteSoSwap(
        address _token,
        uint256 _amount,
        ISo.SoData calldata _soData,
        LibSwap.SwapData[] memory _swapDataDst
    ) external {
        uint256 _soFee = getSoFee(_amount);
        if (_soFee < _amount) {
            _amount = _amount.sub(_soFee);
        }

        if (_swapDataDst.length == 0) {
            if (_soFee > 0) {
                withdraw(
                    _token,
                    _soData.receivingAssetId,
                    _soFee,
                    LibDiamond.contractOwner()
                );
            }
            withdraw(
                _token,
                _soData.receivingAssetId,
                _amount,
                _soData.receiver
            );
            emit SoTransferCompleted(
                _soData.transactionId,
                _soData.receivingAssetId,
                _soData.receiver,
                _amount,
                block.timestamp,
                _soData
            );
        } else {
            if (_soFee > 0) {
                withdraw(
                    _token,
                    _swapDataDst[0].sendingAssetId,
                    _soFee,
                    LibDiamond.contractOwner()
                );
            }
            withdraw(
                _token,
                _swapDataDst[0].sendingAssetId,
                _amount,
                address(this)
            );

            _swapDataDst[0].fromAmount = _amount;

            address _correctSwap = appStorage.correctSwapRouterSelectors;

            if (_correctSwap != address(0)) {
                _swapDataDst[0].callData = ICorrectSwap(_correctSwap)
                    .correctSwap(
                        _swapDataDst[0].callData,
                        _swapDataDst[0].fromAmount
                    );
            }

            uint256 _amountFinal = this.executeAndCheckSwaps(
                _soData,
                _swapDataDst
            );
            withdraw(
                _swapDataDst[_swapDataDst.length - 1].receivingAssetId,
                _soData.receivingAssetId,
                _amountFinal,
                _soData.receiver
            );
            emit SoTransferCompleted(
                _soData.transactionId,
                _soData.receivingAssetId,
                _soData.receiver,
                _amountFinal,
                block.timestamp,
                _soData
            );
        }
    }

    /// @dev Simplifies evaluation of the target chain calls sgReceive's
    ///      gas to facilitate building applications in the upper layers.
    function sgReceiveForGas(
        ISo.NormalizedSoData calldata _soDataNo,
        uint256 _dstStargatePoolId,
        LibSwap.NormalizedSwapData[] calldata _swapDataDstNo
    ) external {
        address _token = _getStargateTokenByPoolId(_dstStargatePoolId);
        uint256 _amount = LibAsset.getOwnBalance(_token);
        if (_amount == 0) {
            require(
                !IStargateEthVault(_token).noUnwrapTo(address(this)),
                "Token error"
            );
            _amount = LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID);
        }

        require(_amount > 0, "sgReceiveForGas need a little amount token!");
        bytes memory _payload = getSgReceiveForGasPayload(
            _soDataNo,
            _swapDataDstNo
        );

        // monitor sgReceive
        if (LibAsset.getOwnBalance(_token) < _amount) {
            require(
                !IStargateEthVault(_token).noUnwrapTo(address(this)),
                "Token error"
            );
            require(
                LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID) >= _amount,
                "Not enough"
            );
            _token = LibAsset.NATIVE_ASSETID;
        }

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeStargatePayload(_payload);

        ISo.SoData memory _soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory _swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        if (gasleft() < getTransferGas()) revert("Not enough gas!");

        uint256 _swapGas = gasleft().sub(getTransferGas());

        this.remoteSoSwap{gas: _swapGas}(
            _token,
            _amount,
            _soData,
            _swapDataDst
        );
    }

    /// @dev Used to obtain stargate cross-chain fee
    function getStargateFee(
        ISo.NormalizedSoData calldata _soDataNo,
        StargateData calldata _stargateData,
        LibSwap.NormalizedSwapData[] calldata _swapDataDstNo
    ) external view returns (uint256) {
        bytes memory _payload = encodeStargatePayload(
            _soDataNo,
            _swapDataDstNo
        );

        Storage storage s = getStorage();
        IStargate.lzTxObj memory _lzTxParams = IStargate.lzTxObj(
            _stargateData.dstGasForSgReceive,
            0,
            bytes("")
        );
        (uint256 _stargateFee, ) = IStargate(s.stargate).quoteLayerZeroFee(
            _stargateData.dstStargateChainId,
            1,
            abi.encodePacked(_stargateData.dstSoDiamond),
            _payload,
            _lzTxParams
        );
        return _stargateFee;
    }

    /// @dev Estimate the number of tokens that stargate can get
    function estimateStargateFinalAmount(
        StargateData calldata _stargateData,
        uint256 _amount
    ) external view returns (uint256) {
        uint256 _amountSD = _convertStargateLDToSDByPoolId(
            _stargateData.srcStargatePoolId,
            _amount
        );
        IStargatePool.SwapObj memory _swapObj = IStargateFeeLibrary(
            _getStargateFeeLibraryByPoolId(_stargateData.srcStargatePoolId)
        ).getFees(
                _stargateData.srcStargatePoolId,
                _stargateData.dstStargatePoolId,
                _stargateData.dstStargateChainId,
                address(0x0),
                _amountSD
            );
        uint256 _estimateAmountSD = _amountSD
            .sub(_swapObj.eqFee)
            .sub(_swapObj.protocolFee)
            .sub(_swapObj.lpFee)
            .add(_swapObj.eqReward);
        return
            _convertStargateSDToLDByPoolId(
                _stargateData.srcStargatePoolId,
                _estimateAmountSD
            );
    }

    /// Public Methods ///

    /// @dev Get so fee
    function getSoFee(uint256 _amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address _soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (_soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(_soFee).getFees(_amount);
        }
    }

    /// @dev Get amount from stargate before so fee
    function getAmountBeforeSoFee(uint256 _amount)
        public
        view
        returns (uint256)
    {
        Storage storage s = getStorage();
        address _soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (_soFee == address(0x0)) {
            return _amount;
        } else {
            return ILibSoFee(_soFee).getRestoredAmount(_amount);
        }
    }

    /// @dev Get remain gas for transfer
    function getTransferGas() public view returns (uint256) {
        Storage storage s = getStorage();
        address _soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (_soFee == address(0x0)) {
            return 30000;
        } else {
            return ILibSoFee(_soFee).getTransferForGas();
        }
    }

    /// @dev Get SgReceive for gas payload
    function getSgReceiveForGasPayload(
        ISo.NormalizedSoData calldata _soDataNo,
        LibSwap.NormalizedSwapData[] calldata _swapDataDstNo
    ) public pure returns (bytes memory) {
        return encodeStargatePayload(_soDataNo, _swapDataDstNo);
    }

    function encodeStargatePayload(
        ISo.NormalizedSoData memory _soData,
        LibSwap.NormalizedSwapData[] memory _swapDataDst
    ) public pure returns (bytes memory) {
        bytes memory d1 = LibCross.encodeNormalizedSoData(_soData);
        bytes memory d2 = LibCross.encodeNormalizedSwapData(_swapDataDst);
        return abi.encodePacked(uint64(d1.length), d1, uint64(d2.length), d2);
    }

    function decodeStargatePayload(bytes memory _stargatePayload)
        public
        pure
        returns (
            ISo.NormalizedSoData memory _soData,
            LibSwap.NormalizedSwapData[] memory _swapDataDst
        )
    {
        uint256 index = 0;
        uint256 nextLen = 0;

        nextLen = uint256(_stargatePayload.toUint64(index));
        index += 8;

        _soData = LibCross.decodeNormalizedSoData(
            _stargatePayload.slice(index, nextLen)
        );
        index += nextLen;
        nextLen = uint256(_stargatePayload.toUint64(index));
        index += 8;
        if (index < _stargatePayload.length) {
            _swapDataDst = LibCross.decodeNormalizedSwapData(
                _stargatePayload.slice(index, nextLen)
            );
            index += nextLen;
        }

        require(index == _stargatePayload.length, "Length error");
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via Stargate
    function _startBridge(
        StargateData calldata _stargateData,
        uint256 _stargateValue,
        uint256 _bridgeAmount,
        bytes memory _payload
    ) private {
        Storage storage s = getStorage();
        address bridge = s.stargate;

        // Do Stargate stuff
        if (s.srcStargateChainId == _stargateData.dstStargateChainId)
            revert CannotBridgeToSameNetwork();

        // Give Stargate approval to bridge tokens
        LibAsset.maxApproveERC20(
            IERC20(_getStargateTokenByPoolId(_stargateData.srcStargatePoolId)),
            bridge,
            _bridgeAmount
        );
        IStargate.lzTxObj memory _lzTxParams = IStargate.lzTxObj(
            _stargateData.dstGasForSgReceive,
            0,
            bytes("")
        );
        bytes memory _to = abi.encodePacked(_stargateData.dstSoDiamond);
        IStargate(bridge).swap{value: _stargateValue}(
            _stargateData.dstStargateChainId,
            _stargateData.srcStargatePoolId,
            _stargateData.dstStargatePoolId,
            payable(msg.sender),
            _bridgeAmount,
            _stargateData.minAmount,
            _lzTxParams,
            _to,
            _payload
        );
    }

    /// @dev Calculate the fee for paying the stargate bridge
    function _getStargateValue(SoData memory _soData)
        private
        view
        returns (uint256)
    {
        if (LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            require(
                msg.value > _soData.amount,
                "Stargate value is not enough!"
            );
            return msg.value.sub(_soData.amount);
        } else {
            return msg.value;
        }
    }

    /// @dev Get stargate pool address by poolId
    function _getStargatePoolByPoolId(uint256 _poolId)
        private
        view
        returns (address)
    {
        Storage storage s = getStorage();
        address _factory = IStargate(s.stargate).factory();
        return IStargateFactory(_factory).getPool(_poolId);
    }

    /// @dev Get stargate bridge token address by poolId
    function _getStargateTokenByPoolId(uint256 _poolId)
        private
        view
        returns (address)
    {
        return IStargatePool(_getStargatePoolByPoolId(_poolId)).token();
    }

    /// @dev Get stargate bridge fee library address by poolId
    function _getStargateFeeLibraryByPoolId(uint256 _poolId)
        private
        view
        returns (address)
    {
        return IStargatePool(_getStargatePoolByPoolId(_poolId)).feeLibrary();
    }

    /// @dev Get stargate convert rate by poolId
    function _getStargateConvertRateByPoolId(uint256 _poolId)
        private
        view
        returns (uint256)
    {
        return IStargatePool(_getStargatePoolByPoolId(_poolId)).convertRate();
    }

    /// @dev Get stargate convert LD to SD poolId
    function _convertStargateLDToSDByPoolId(uint256 _poolId, uint256 _amount)
        private
        view
        returns (uint256)
    {
        return _amount.div(_getStargateConvertRateByPoolId(_poolId));
    }

    /// @dev Get stargate convert SD to LD poolId
    function _convertStargateSDToLDByPoolId(uint256 _poolId, uint256 _amount)
        private
        view
        returns (uint256)
    {
        return _amount.mul(_getStargateConvertRateByPoolId(_poolId));
    }

    /// @dev fetch local storage
    function getStorage() private pure returns (Storage storage s) {
        bytes32 namespace = NAMESPACE;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            s.slot := namespace
        }
    }
}
