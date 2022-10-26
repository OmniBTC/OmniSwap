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
/// @author OmniBTC
/// @notice Provides functionality for bridging through Stargate
contract StargateFacet is ISo, Swapper, ReentrancyGuard, IStargateReceiver {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"2bd10e5dcb5694caec513d6d8fa1fd90f6a026e0e9320d7b6e2f8e49b93270d1"; //keccak256("com.so.facets.stargate");

    struct Storage {
        address stargate; // The stargate route address
        uint16 srcStargateChainId; // The stargate chain id of the source/current chain
        mapping(address => bool) allowedList; // Permission to allow calls to sgReceive
        mapping(address => uint256) approveAmount; // Use less than the amount of the transaction fee to estimate the dst gas
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
    event SetApproveAmount(address token, uint256 amount);
    event SetAllowedList(address router, bool isAllowed);

    /// Init ///

    /// @notice Initializes local variables for the Stargate facet
    /// @param stargate address of the canonical Stargate router contract
    /// @param chainId chainId of this deployed contract
    function initStargate(address stargate, uint16 chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (stargate == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.stargate = stargate;
        s.srcStargateChainId = chainId;
        s.allowedList[stargate] = true;
        s.allowedList[msg.sender] = true;
        emit StargateInitialized(stargate, chainId);
    }

    /// @dev Add a withdrawal limit for a token to prevent the interface
    ///      used to estimate fees from being used for withdrawals.
    /// @param token token address
    /// @param amount approved amount
    function setApproveAmount(address token, uint256 amount) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.approveAmount[token] = amount;
        emit SetApproveAmount(token, amount);
    }

    /// @dev Set permissions to control calls to sgReceive
    function setAllowedAddress(address router, bool isAllowed) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.allowedList[router] = isAllowed;
        emit SetAllowedList(router, isAllowed);
    }

    /// External Methods ///

    /// @notice Bridges tokens via Stargate
    /// @param soDataNo Data for tracking cross-chain transactions and a
    ///                portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param stargateData Data used to call Stargate's router for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    ///                     on the target chain.
    function soSwapViaStargate(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        StargateData calldata stargateData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        bool hasSourceSwap;
        bool hasDestinationSwap;
        uint256 bridgeAmount;

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }
        if (swapDataSrc.length == 0) {
            deposit(
                soData.sendingAssetId,
                _getStargateTokenByPoolId(stargateData.srcStargatePoolId),
                soData.amount
            );
            bridgeAmount = soData.amount;
            hasSourceSwap = false;
        } else {
            require(
                soData.amount == swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            deposit(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                _getStargateTokenByPoolId(stargateData.srcStargatePoolId),
                bridgeAmount
            );
            hasSourceSwap = true;
        }
        uint256 stargateValue = _getStargateValue(soData);
        bytes memory payload = encodeStargatePayload(soDataNo, swapDataDstNo);

        if (swapDataDstNo.length > 0) {
            hasDestinationSwap = true;
        }

        _startBridge(stargateData, stargateValue, bridgeAmount, payload);

        emit SoTransferStarted(
            soData.transactionId,
            "Stargate",
            hasSourceSwap,
            hasDestinationSwap,
            soData
        );
    }

    /// @dev Overload sgReceive of IStargateReceiver, called by stargate router
    function sgReceive(
        uint16,
        bytes memory,
        uint256,
        address token,
        uint256 amount,
        bytes memory payload
    ) external {
        Storage storage s = getStorage();
        require(s.allowedList[msg.sender], "No permission");

        if (LibAsset.getOwnBalance(token) < amount) {
            require(
                !IStargateEthVault(token).noUnwrapTo(address(this)),
                "Token error"
            );
            require(
                LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID) >= amount,
                "Not enough"
            );
            token = LibAsset.NATIVE_ASSETID;
        }

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeStargatePayload(payload);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        if (gasleft() < getTransferGas()) revert("Not enough gas!");

        uint256 swapGas = gasleft().sub(getTransferGas());
        try
            this.remoteSoSwap{gas: swapGas}(token, amount, soData, swapDataDst)
        {} catch Error(string memory revertReason) {
            withdraw(token, token, amount, soData.receiver);
            emit SoTransferFailed(
                soData.transactionId,
                revertReason,
                bytes(""),
                soData
            );
        } catch (bytes memory returnData) {
            withdraw(token, token, amount, soData.receiver);
            emit SoTransferFailed(soData.transactionId, "", returnData, soData);
        }
    }

    /// @dev For internal calls only, do not add it to DiamondCut,
    ///      convenient for sgReceive to catch exceptions
    function remoteSoSwap(
        address token,
        uint256 amount,
        ISo.SoData calldata soData,
        LibSwap.SwapData[] memory swapDataDst
    ) external {
        uint256 soFee = getSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
            if (soFee > 0) {
                withdraw(
                    token,
                    soData.receivingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            withdraw(token, soData.receivingAssetId, amount, soData.receiver);
            emit SoTransferCompleted(
                soData.transactionId,
                soData.receivingAssetId,
                soData.receiver,
                amount,
                block.timestamp,
                soData
            );
        } else {
            if (soFee > 0) {
                withdraw(
                    token,
                    swapDataDst[0].sendingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            withdraw(
                token,
                swapDataDst[0].sendingAssetId,
                amount,
                address(this)
            );

            swapDataDst[0].fromAmount = amount;

            address correctSwap = appStorage.correctSwapRouterSelectors;

            if (correctSwap != address(0)) {
                swapDataDst[0].callData = ICorrectSwap(correctSwap).correctSwap(
                    swapDataDst[0].callData,
                    swapDataDst[0].fromAmount
                );
            }

            uint256 amountFinal = this.executeAndCheckSwaps(
                soData,
                swapDataDst
            );
            withdraw(
                swapDataDst[swapDataDst.length - 1].receivingAssetId,
                soData.receivingAssetId,
                amountFinal,
                soData.receiver
            );
            emit SoTransferCompleted(
                soData.transactionId,
                soData.receivingAssetId,
                soData.receiver,
                amountFinal,
                block.timestamp,
                soData
            );
        }
    }

    /// @dev Simplifies evaluation of the target chain calls sgReceive's
    ///      gas to facilitate building applications in the upper layers.
    function sgReceiveForGas(
        ISo.NormalizedSoData calldata soDataNo,
        uint256 dstStargatePoolId,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external {
        address token = _getStargateTokenByPoolId(dstStargatePoolId);
        uint256 amount = LibAsset.getOwnBalance(token);

        if (amount == 0) {
            require(
                !IStargateEthVault(token).noUnwrapTo(address(this)),
                "Token error"
            );
            token = LibAsset.NATIVE_ASSETID;
            amount = LibAsset.getOwnBalance(token);
        }

        Storage storage s = getStorage();
        uint256 approveAmount = s.approveAmount[token];
        amount = approveAmount < amount && approveAmount > 0
            ? approveAmount
            : amount;

        require(amount > 0, "sgReceiveForGas need a little amount token!");
        bytes memory payload = getSgReceiveForGasPayload(
            soDataNo,
            swapDataDstNo
        );

        // monitor sgReceive
        if (LibAsset.getOwnBalance(token) < amount) {
            require(
                !IStargateEthVault(token).noUnwrapTo(address(this)),
                "Token error"
            );
            require(
                LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID) >= amount,
                "Not enough"
            );
            token = LibAsset.NATIVE_ASSETID;
        }

        (
            ISo.NormalizedSoData memory _soDataNo,
            LibSwap.NormalizedSwapData[] memory _swapDataDstNo
        ) = decodeStargatePayload(payload);

        ISo.SoData memory soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            _swapDataDstNo
        );

        if (gasleft() < getTransferGas()) revert("Not enough gas!");

        uint256 swapGas = gasleft().sub(getTransferGas());

        this.remoteSoSwap{gas: swapGas}(token, amount, soData, swapDataDst);
    }

    /// @dev Used to obtain stargate cross-chain fee
    function getStargateFee(
        ISo.NormalizedSoData calldata soDataNo,
        StargateData calldata stargateData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external view returns (uint256) {
        bytes memory payload = encodeStargatePayload(soDataNo, swapDataDstNo);

        Storage storage s = getStorage();
        IStargate.lzTxObj memory lzTxParams = IStargate.lzTxObj(
            stargateData.dstGasForSgReceive,
            0,
            bytes("")
        );
        (uint256 stargateFee, ) = IStargate(s.stargate).quoteLayerZeroFee(
            stargateData.dstStargateChainId,
            1,
            abi.encodePacked(stargateData.dstSoDiamond),
            payload,
            lzTxParams
        );
        return stargateFee;
    }

    /// @dev Estimate the number of tokens that stargate can get
    function estimateStargateFinalAmount(
        StargateData calldata stargateData,
        uint256 amount
    ) external view returns (uint256) {
        uint256 amountSD = _convertStargateLDToSDByPoolId(
            stargateData.srcStargatePoolId,
            amount
        );
        IStargatePool.SwapObj memory swapObj = IStargateFeeLibrary(
            _getStargateFeeLibraryByPoolId(stargateData.srcStargatePoolId)
        ).getFees(
                stargateData.srcStargatePoolId,
                stargateData.dstStargatePoolId,
                stargateData.dstStargateChainId,
                address(0x0),
                amountSD
            );
        uint256 estimateAmountSD = amountSD
            .sub(swapObj.eqFee)
            .sub(swapObj.protocolFee)
            .sub(swapObj.lpFee)
            .add(swapObj.eqReward);
        return
            _convertStargateSDToLDByPoolId(
                stargateData.srcStargatePoolId,
                estimateAmountSD
            );
    }

    /// Public Methods ///

    /// @dev Get so fee
    function getSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(soFee).getFees(amount);
        }
    }

    /// @dev Get amount from stargate before so fee
    function getAmountBeforeSoFee(uint256 amount)
        public
        view
        returns (uint256)
    {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (soFee == address(0x0)) {
            return amount;
        } else {
            return ILibSoFee(soFee).getRestoredAmount(amount);
        }
    }

    /// @dev Get remain gas for transfer
    function getTransferGas() public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.stargate];
        if (soFee == address(0x0)) {
            return 30000;
        } else {
            return ILibSoFee(soFee).getTransferForGas();
        }
    }

    /// @dev Get SgReceive for gas payload
    function getSgReceiveForGasPayload(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) public pure returns (bytes memory) {
        return encodeStargatePayload(soDataNo, swapDataDstNo);
    }

    function encodeStargatePayload(
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst
    ) public pure returns (bytes memory) {
        bytes memory d1 = LibCross.encodeNormalizedSoData(soData);
        bytes memory d2 = LibCross.encodeNormalizedSwapData(swapDataDst);
        if (d2.length > 0) {
            return
                abi.encodePacked(uint64(d1.length), d1, uint64(d2.length), d2);
        } else {
            return abi.encodePacked(uint64(d1.length), d1);
        }
    }

    function decodeStargatePayload(bytes memory stargatePayload)
        public
        pure
        returns (
            ISo.NormalizedSoData memory soData,
            LibSwap.NormalizedSwapData[] memory swapDataDst
        )
    {
        uint256 index = 0;
        uint256 nextLen = 0;

        nextLen = uint256(stargatePayload.toUint64(index));
        index += 8;

        soData = LibCross.decodeNormalizedSoData(
            stargatePayload.slice(index, nextLen)
        );
        index += nextLen;

        if (index < stargatePayload.length) {
            nextLen = uint256(stargatePayload.toUint64(index));
            index += 8;
            swapDataDst = LibCross.decodeNormalizedSwapData(
                stargatePayload.slice(index, nextLen)
            );
            index += nextLen;
        }

        require(index == stargatePayload.length, "Length error");
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via Stargate
    function _startBridge(
        StargateData calldata stargateData,
        uint256 stargateValue,
        uint256 bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();
        address bridge = s.stargate;

        // Do Stargate stuff
        if (s.srcStargateChainId == stargateData.dstStargateChainId)
            revert CannotBridgeToSameNetwork();

        // Give Stargate approval to bridge tokens
        LibAsset.maxApproveERC20(
            IERC20(_getStargateTokenByPoolId(stargateData.srcStargatePoolId)),
            bridge,
            bridgeAmount
        );
        IStargate.lzTxObj memory lzTxParams = IStargate.lzTxObj(
            stargateData.dstGasForSgReceive,
            0,
            bytes("")
        );
        bytes memory to = abi.encodePacked(stargateData.dstSoDiamond);
        IStargate(bridge).swap{value: stargateValue}(
            stargateData.dstStargateChainId,
            stargateData.srcStargatePoolId,
            stargateData.dstStargatePoolId,
            payable(msg.sender),
            bridgeAmount,
            stargateData.minAmount,
            lzTxParams,
            to,
            payload
        );
    }

    /// @dev Calculate the fee for paying the stargate bridge
    function _getStargateValue(SoData memory soData)
        private
        view
        returns (uint256)
    {
        if (LibAsset.isNativeAsset(soData.sendingAssetId)) {
            require(msg.value > soData.amount, "Stargate value is not enough!");
            return msg.value.sub(soData.amount);
        } else {
            return msg.value;
        }
    }

    /// @dev Get stargate pool address by poolId
    function _getStargatePoolByPoolId(uint256 poolId)
        private
        view
        returns (address)
    {
        Storage storage s = getStorage();
        address factory = IStargate(s.stargate).factory();
        return IStargateFactory(factory).getPool(poolId);
    }

    /// @dev Get stargate bridge token address by poolId
    function _getStargateTokenByPoolId(uint256 poolId)
        private
        view
        returns (address)
    {
        return IStargatePool(_getStargatePoolByPoolId(poolId)).token();
    }

    /// @dev Get stargate bridge fee library address by poolId
    function _getStargateFeeLibraryByPoolId(uint256 poolId)
        private
        view
        returns (address)
    {
        return IStargatePool(_getStargatePoolByPoolId(poolId)).feeLibrary();
    }

    /// @dev Get stargate convert rate by poolId
    function _getStargateConvertRateByPoolId(uint256 poolId)
        private
        view
        returns (uint256)
    {
        return IStargatePool(_getStargatePoolByPoolId(poolId)).convertRate();
    }

    /// @dev Get stargate convert LD to SD poolId
    function _convertStargateLDToSDByPoolId(uint256 poolId, uint256 amount)
        private
        view
        returns (uint256)
    {
        return amount.div(_getStargateConvertRateByPoolId(poolId));
    }

    /// @dev Get stargate convert SD to LD poolId
    function _convertStargateSDToLDByPoolId(uint256 poolId, uint256 amount)
        private
        view
        returns (uint256)
    {
        return amount.mul(_getStargateConvertRateByPoolId(poolId));
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
