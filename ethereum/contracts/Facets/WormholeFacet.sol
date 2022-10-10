// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ILibPrice.sol";
import "../Helpers/Swapper.sol";
import "../Interfaces/IWormholeBridge.sol";
import "../Interfaces/ILibSoFee.sol";

/// @title Wormhole Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through Wormhole
contract WormholeFacet is Swapper {
    using SafeMath for uint256;
    using LibBytes for bytes;

    bytes32 internal constant NAMESPACE =
        hex"d4ca4302bca26785486b2ceec787497a9cf992c36dcf57c306a00c1f88154623"; // keccak256("com.so.facets.wormhole")

    uint256 public constant RAY = 1e27;

    struct Storage {
        address tokenBridge;
        uint16 srcWormholeChainId;
        uint64 nonce;
        uint256 actualReserve; // [RAY]
        uint256 estimateReserve; // [RAY]
        mapping(uint16 => uint256) dstBaseGas;
        mapping(uint16 => uint256) dstGasPerBytes;
    }

    /// Events ///

    event InitWormholeEvent(address tokenBridge, uint16 srcWormholeChainId);
    event UpdateWormholeReserve(uint256 actualReserve, uint256 estimateReserve);
    event UpdateWormholeGas(
        uint16 dstWormholeChainId,
        uint256 baseGas,
        uint256 gasPerBytes
    );

    /// Types ///
    struct WormholeData {
        uint16 dstWormholeChainId;
        uint256 dstMaxGasForRelayer;
        uint256 dstMaxGasPriceInWeiForRelayer;
        address dstSoDiamond;
    }

    /// Init ///

    /// init wormhole token bridge
    function initWormhole(address _tokenBridge, uint16 _wormholeChainId)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.tokenBridge = _tokenBridge;
        s.srcWormholeChainId = _wormholeChainId;
        emit InitWormholeEvent(_tokenBridge, _wormholeChainId);
    }

    function setWormholeReserve(
        uint256 _actualReserve,
        uint256 _estimateReserve
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.actualReserve = _actualReserve;
        s.estimateReserve = _estimateReserve;
        emit UpdateWormholeReserve(_actualReserve, _estimateReserve);
    }

    function setWormholeGas(
        uint16 _dstWormholeChainId,
        uint256 _baseGas,
        uint256 _gasPerBytes
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.dstBaseGas[_dstWormholeChainId] = _baseGas;
        s.dstGasPerBytes[_dstWormholeChainId] = _gasPerBytes;
        emit UpdateWormholeGas(_dstWormholeChainId, _baseGas, _gasPerBytes);
    }

    /// External Methods ///

    struct WormholeCache {
        bool _flag;
        uint256 _fee;
        bool _hasSourceSwap;
        bool _hasDestinationSwap;
        uint256 _bridgeAmount;
        address _bridgeAddress;
        bytes _payload;
    }

    /// transfer with payload
    function soSwapViaWormhole(
        ISo.SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        WormholeData calldata _wormholeData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable {
        WormholeCache memory _cache;
        uint256 returnValue;
        (_cache._flag, _cache._fee, returnValue) = checkRelayerFee(
            _soData,
            _wormholeData,
            msg.value
        );
        require(_cache._flag, "Check fail");
        // return the redundant msg.value
        if (returnValue > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(msg.sender),
                returnValue
            );
        }
        LibAsset.transferAsset(
            LibAsset.NATIVE_ASSETID,
            payable(LibDiamond.contractOwner()),
            _cache._fee
        );
        if (!LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            LibAsset.depositAsset(_soData.sendingAssetId, _soData.amount);
        }
        if (_swapDataSrc.length == 0) {
            _cache._bridgeAddress = _soData.sendingAssetId;
            _cache._bridgeAmount = _soData.amount;
            _cache._hasSourceSwap = false;
        } else {
            require(
                _soData.amount == _swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            _cache._bridgeAmount = this.executeAndCheckSwaps(
                _soData,
                _swapDataSrc
            );
            _cache._bridgeAddress = _swapDataSrc[_swapDataSrc.length - 1]
                .receivingAssetId;
            _cache._hasSourceSwap = true;
        }

        if (_swapDataDst.length == 0) {
            _cache._payload = abi.encodePacked(
                _wormholeData.dstMaxGasPriceInWeiForRelayer,
                encodeSoData(_soData)
            );
            _cache._hasDestinationSwap = false;
        } else {
            _cache._payload = abi.encode(
                _wormholeData.dstMaxGasPriceInWeiForRelayer,
                encodeSoData(_soData),
                encodeSwapData(_swapDataDst)
            );
            _cache._hasDestinationSwap = true;
        }

        /// start bridge
        _startBridge(
            _wormholeData,
            _cache._bridgeAddress,
            _cache._bridgeAmount,
            _cache._fee,
            _cache._payload
        );

        emit ISo.SoTransferStarted(
            _soData.transactionId,
            "Wormhole",
            _cache._hasSourceSwap,
            _cache._hasDestinationSwap,
            _soData
        );
    }

    function completeTransferAndUnwrapETHWithPayload(bytes memory _encodeVm)
        external
    {
        completeSoSwap(_encodeVm);
    }

    function completeTransferWithPayload(bytes memory _encodeVm) external {
        completeSoSwap(_encodeVm);
    }

    /// complete transfer with payload
    /// called by relayer
    function completeSoSwap(bytes memory _encodeVm) public {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;

        bytes memory payload = IWormholeBridge(bridge)
            .completeTransferWithPayload(_encodeVm);

        IWormholeBridge.TransferWithPayload
            memory _wormholePayload = IWormholeBridge(bridge)
                .parseTransferWithPayload(payload);

        ISo.SoData memory _soData = parseSoData(_wormholePayload.payload);
        LibSwap.SwapData[] memory _swapDataDst = parseSwapData(
            _wormholePayload.payload
        );

        address _tokenAddress;
        bool _isOriginChain;
        if (_wormholePayload.tokenChain == IWormholeBridge(bridge).chainId()) {
            _tokenAddress = address(
                uint160(uint256(_wormholePayload.tokenAddress))
            );
            _isOriginChain = true;
        } else {
            _tokenAddress = IWormholeBridge(bridge).wrappedAsset(
                _wormholePayload.tokenChain,
                _wormholePayload.tokenAddress
            );
        }

        uint256 amount = LibAsset.getOwnBalance(_tokenAddress);
        uint256 soFee = getSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }
        require(amount > 0, "amount > 0");

        IWETH _weth = IWormholeBridge(bridge).WETH();

        if (_isOriginChain && address(_weth) == _tokenAddress) {
            _weth.withdraw(amount);
            _tokenAddress = LibAsset.NATIVE_ASSETID;
        }

        if (_swapDataDst.length == 0) {
            require(_tokenAddress == _soData.receivingAssetId, "token error");
            if (soFee > 0) {
                LibAsset.transferAsset(
                    _soData.receivingAssetId,
                    payable(LibDiamond.contractOwner()),
                    soFee
                );
            }
            LibAsset.transferAsset(
                _soData.receivingAssetId,
                _soData.receiver,
                amount
            );
            emit SoTransferCompleted(
                _soData.transactionId,
                _soData.receivingAssetId,
                _soData.receiver,
                amount,
                block.timestamp,
                _soData
            );
        } else {
            if (soFee > 0) {
                LibAsset.transferAsset(
                    _swapDataDst[0].sendingAssetId,
                    payable(LibDiamond.contractOwner()),
                    soFee
                );
            }
            require(
                _swapDataDst[0].sendingAssetId == _tokenAddress,
                "token error"
            );

            _swapDataDst[0].fromAmount = amount;

            address _correctSwap = appStorage.correctSwapRouterSelectors;

            if (_correctSwap != address(0)) {
                _swapDataDst[0].callData = ICorrectSwap(_correctSwap)
                    .correctSwap(
                        _swapDataDst[0].callData,
                        _swapDataDst[0].fromAmount
                    );
            }

            try this.executeAndCheckSwaps(_soData, _swapDataDst) returns (
                uint256 _amountFinal
            ) {
                LibAsset.transferAsset(
                    _swapDataDst[_swapDataDst.length - 1].receivingAssetId,
                    _soData.receiver,
                    _amountFinal
                );
                emit SoTransferCompleted(
                    _soData.transactionId,
                    _soData.receivingAssetId,
                    _soData.receiver,
                    _amountFinal,
                    block.timestamp,
                    _soData
                );
            } catch Error(string memory revertReason) {
                LibAsset.transferAsset(
                    _soData.receivingAssetId,
                    _soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    _soData.transactionId,
                    revertReason,
                    bytes(""),
                    _soData
                );
            } catch (bytes memory returnData) {
                LibAsset.transferAsset(
                    _soData.receivingAssetId,
                    _soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    _soData.transactionId,
                    "",
                    returnData,
                    _soData
                );
            }
        }
    }

    function estimateCompleteSoSwapGas(
        ISo.SoData calldata _soData,
        WormholeData calldata _wormholeData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) public view returns (uint256) {
        bytes memory _payload;
        if (_swapDataDst.length == 0) {
            _payload = abi.encode(_soData, bytes(""));
        } else {
            _payload = abi.encode(_soData, abi.encode(_swapDataDst));
        }
        Storage storage s = getStorage();
        return
            s.dstBaseGas[_wormholeData.dstWormholeChainId].add(
                s.dstGasPerBytes[_wormholeData.dstWormholeChainId].mul(
                    _payload.length
                )
            );
    }

    function checkRelayerFee(
        ISo.SoData calldata _soData,
        WormholeData calldata _wormholeData,
        uint256 _value
    )
        public
        returns (
            bool,
            uint256,
            uint256
        )
    {
        Storage storage s = getStorage();
        ILibPrice _oracle = ILibPrice(
            appStorage.gatewaySoFeeSelectors[s.tokenBridge]
        );
        uint256 _ratio = _oracle.updatePriceRatio(
            _wormholeData.dstWormholeChainId
        );
        uint256 _dstFee = _wormholeData.dstMaxGasForRelayer.mul(
            _wormholeData.dstMaxGasPriceInWeiForRelayer
        );
        uint256 _srcFee = _dstFee
            .mul(_ratio)
            .div(_oracle.RAY())
            .mul(s.actualReserve)
            .div(RAY);

        uint256 _userInput;
        if (LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            _userInput = _soData.amount;
        }
        bool flag;
        uint256 returnValue;
        uint256 consumeValue = IWormholeBridge(s.tokenBridge)
            .wormhole()
            .messageFee()
            .add(_userInput)
            .add(_srcFee);
        if (consumeValue <= _value) {
            flag = true;
            returnValue = _value.sub(consumeValue);
        }
        return (flag, _srcFee, returnValue);
    }

    function estimateRelayerFee(WormholeData calldata _wormholeData)
        external
        view
        returns (uint256)
    {
        Storage storage s = getStorage();
        ILibPrice _oracle = ILibPrice(
            appStorage.gatewaySoFeeSelectors[s.tokenBridge]
        );
        (uint256 _ratio, ) = _oracle.getPriceRatio(
            _wormholeData.dstWormholeChainId
        );
        uint256 _dstFee = _wormholeData.dstMaxGasForRelayer.mul(
            _wormholeData.dstMaxGasPriceInWeiForRelayer
        );
        uint256 _srcFee = _dstFee
            .mul(_ratio)
            .div(_oracle.RAY())
            .mul(s.estimateReserve)
            .div(RAY);
        return _srcFee;
    }

    function getWormholeMessageFee() external view returns (uint256) {
        Storage storage s = getStorage();
        return IWormholeBridge(s.tokenBridge).wormhole().messageFee();
    }

    /// @dev Get so fee
    function getSoFee(uint256 _amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address _soFee = appStorage.gatewaySoFeeSelectors[s.tokenBridge];
        if (_soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(_soFee).getFees(_amount);
        }
    }

    /// @dev decode signedVAA to get max gas and price for relayer
    function getMaxGasAndPrice(bytes memory _encodeVm)
        external
        view
        returns (uint256)
    {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;
        bytes memory payload = IWormholeBridge(bridge)
            .wormhole()
            .parseVM(_encodeVm)
            .payload;

        IWormholeBridge.TransferWithPayload
            memory _wormholePayload = IWormholeBridge(bridge)
                .parseTransferWithPayload(payload);

        uint256 dstMaxGasPriceInWeiForRelayer = parseMaxGasPrice(
            _wormholePayload.payload
        );

        return dstMaxGasPriceInWeiForRelayer;
    }

    function encodeSoData(ISo.SoData memory _soData)
        public
        pure
        returns (bytes memory _encoded)
    {
        _encoded = abi.encodePacked(
            _soData.transactionId,
            _soData.receiver,
            _soData.sourceChainId,
            _soData.sendingAssetId,
            _soData.destinationChainId,
            _soData.receivingAssetId,
            _soData.amount
        );
    }

    function encodeSwapData(LibSwap.SwapData[] memory _swapData)
        public
        pure
        returns (bytes memory _encoded)
    {
        bytes memory encodedLength = abi.encodePacked(_swapData.length);
        _encoded.concat(encodedLength);
        for (uint256 i = 0; i < _swapData.length; i++) {
            bytes memory encodedSwapData = abi.encodePacked(
                _swapData[i].callTo,
                _swapData[i].approveTo,
                _swapData[i].sendingAssetId,
                _swapData[i].receivingAssetId,
                _swapData[i].fromAmount,
                _swapData[i].callData.length,
                _swapData[i].callData
            );
            _encoded.concat(encodedSwapData);
        }
    }

    function parseMaxGasPrice(bytes memory _encodedPayload)
        public
        pure
        returns (uint256 maxGasPrice)
    {
        maxGasPrice = _encodedPayload.toUint256(0);
    }

    function parseSoData(bytes memory _encodedPayload)
        public
        pure
        returns (ISo.SoData memory _soData)
    {
        uint256 index = 0 + 32;

        _soData.transactionId = _encodedPayload.toBytes32(index);
        index += 32;

        _soData.receiver = payable(_encodedPayload.toAddress(index));
        index += 20;

        _soData.sourceChainId = _encodedPayload.toUint256(index);
        index += 32;

        _soData.sendingAssetId = _encodedPayload.toAddress(index);
        index += 20;

        _soData.destinationChainId = _encodedPayload.toUint256(index);
        index += 32;

        _soData.receivingAssetId = _encodedPayload.toAddress(index);
        index += 20;

        _soData.amount = _encodedPayload.toUint256(index);
        index += 32;
    }

    function parseSwapData(bytes memory _encodedPayload)
        public
        pure
        returns (LibSwap.SwapData[] memory _swapData)
    {
        uint256 index = 0 + 32 + 32 + 20 + 32 + 20 + 32 + 20 + 32;
        if (_encodedPayload.length == index) {} else {
            uint256 length = _encodedPayload.toUint256(index);
            index += 32;

            for (uint256 i = 0; i < length; i++) {
                _swapData[i].callTo = _encodedPayload.toAddress(index);
                index += 20;

                _swapData[i].approveTo = _encodedPayload.toAddress(index);
                index += 20;

                _swapData[i].sendingAssetId = _encodedPayload.toAddress(index);
                index += 20;

                _swapData[i].receivingAssetId = _encodedPayload.toAddress(
                    index
                );
                index += 20;

                _swapData[i].fromAmount = _encodedPayload.toUint256(index);
                index += 32;

                uint256 bytesLength = _encodedPayload.toUint256(index);
                index += 32;

                _swapData[i].callData = _encodedPayload.slice(
                    index,
                    bytesLength
                );
                index += bytesLength;
            }
        }
    }

    /// Internal Methods ///

    function _startBridge(
        WormholeData calldata _wormholeData,
        address _token,
        uint256 _amount,
        uint256 _srcFee,
        bytes memory _payload
    ) internal {
        Storage storage s = getStorage();
        address _bridge = s.tokenBridge;

        if (LibAsset.isNativeAsset(_token)) {
            IWormholeBridge(_bridge).wrapAndTransferETHWithPayload{
                value: msg.value.sub(_srcFee)
            }(
                _wormholeData.dstWormholeChainId,
                bytes32(uint256(uint160(_wormholeData.dstSoDiamond))),
                s.nonce,
                _payload
            );
        } else {
            LibAsset.maxApproveERC20(IERC20(_token), _bridge, _amount);
            IWormholeBridge(_bridge).transferTokensWithPayload{
                value: msg.value
            }(
                _token,
                _amount,
                _wormholeData.dstWormholeChainId,
                bytes32(uint256(uint160(_wormholeData.dstSoDiamond))),
                s.nonce,
                _payload
            );
        }

        uint256 _dust = LibAsset.getOwnBalance(_token);
        if (_dust > 0) {
            LibAsset.transferAsset(_token, payable(msg.sender), _dust);
        }

        s.nonce += 1;
    }

    /// Private Methods ///

    /// @dev fetch local storage
    function getStorage() private pure returns (Storage storage s) {
        bytes32 namespace = NAMESPACE;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            s.slot := namespace
        }
    }
}
