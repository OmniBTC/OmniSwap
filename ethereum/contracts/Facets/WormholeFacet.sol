// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
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
    struct NormalizedWormholeData {
        uint16 dstWormholeChainId;
        uint256 dstMaxGasPriceInWeiForRelayer;
        uint256 wormholeFee;
        bytes dstSoDiamond;
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

    struct CacheSrcSoSwap {
        bool _flag;
        uint256 _fee;
        bool _hasSourceSwap;
        bool _hasDestinationSwap;
        uint256 _bridgeAmount;
        address _bridgeAddress;
        uint256 returnValue;
        uint256 dstMaxGas;
        bytes _payload;
    }

    /// transfer with payload
    function soSwapViaWormhole(
        ISo.NormalizedSoData calldata _soDataNo,
        LibSwap.NormalizedSwapData[] calldata _swapDataSrcNo,
        NormalizedWormholeData calldata _wormholeDataNo,
        LibSwap.NormalizedSwapData[] calldata _swapDataDstNo
    ) external payable {
        require(msg.value == _wormholeDataNo.wormholeFee, "Fee error");

        CacheSrcSoSwap memory _cache;

        ISo.SoData memory _soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory _swapDataSrc = LibCross.denormalizeSwapData(
            _swapDataSrcNo
        );

        (
            _cache._flag,
            _cache._fee,
            _cache.returnValue,
            _cache.dstMaxGas
        ) = checkRelayerFee(_soDataNo, _wormholeDataNo, _swapDataDstNo);

        require(_cache._flag, "Check fail");
        // return the redundant msg.value
        if (_cache.returnValue > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(msg.sender),
                _cache.returnValue
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

        _cache._payload = encodeWormholePayload(
            _wormholeDataNo.dstMaxGasPriceInWeiForRelayer,
            _cache.dstMaxGas,
            _soDataNo,
            _swapDataDstNo
        );

        if (_swapDataSrc.length > 0) {
            _cache._hasDestinationSwap = true;
        }

        /// start bridge
        _startBridge(
            _wormholeDataNo,
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

        (
            ,
            ,
            ISo.NormalizedSoData memory _soDataNo,
            LibSwap.NormalizedSwapData[] memory _swapDataDstNo
        ) = decodeWormholePayload(_wormholePayload.payload);

        ISo.SoData memory _soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory _swapDataDst = LibCross.denormalizeSwapData(
            _swapDataDstNo
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
        ISo.NormalizedSoData calldata _soData,
        NormalizedWormholeData calldata _wormholeData,
        LibSwap.NormalizedSwapData[] calldata _swapDataDst
    ) public view returns (uint256) {
        bytes memory _payload = encodeWormholePayload(
            _wormholeData.dstMaxGasPriceInWeiForRelayer,
            0,
            _soData,
            _swapDataDst
        );
        Storage storage s = getStorage();
        return
            s.dstBaseGas[_wormholeData.dstWormholeChainId].add(
                s.dstGasPerBytes[_wormholeData.dstWormholeChainId].mul(
                    _payload.length
                )
            );
    }

    struct CacheCheck {
        uint256 _ratio;
        uint256 _srcFee;
        uint256 _dstFee;
        uint256 _userInput;
        uint256 dstMaxGasForRelayer;
        bool flag;
        uint256 returnValue;
        uint256 consumeValue;
    }

    function checkRelayerFee(
        ISo.NormalizedSoData calldata _soData,
        NormalizedWormholeData calldata _wormholeData,
        LibSwap.NormalizedSwapData[] calldata _swapDataDst
    )
        public
        returns (
            bool,
            uint256,
            uint256,
            uint256
        )
    {
        CacheCheck memory data;
        Storage storage s = getStorage();
        ILibPrice _oracle = ILibPrice(
            appStorage.gatewaySoFeeSelectors[s.tokenBridge]
        );
        data._ratio = _oracle.updatePriceRatio(
            _wormholeData.dstWormholeChainId
        );
        data.dstMaxGasForRelayer = estimateCompleteSoSwapGas(
            _soData,
            _wormholeData,
            _swapDataDst
        );

        data._dstFee = data.dstMaxGasForRelayer.mul(
            _wormholeData.dstMaxGasPriceInWeiForRelayer
        );
        data._srcFee = data
            ._dstFee
            .mul(data._ratio)
            .div(_oracle.RAY())
            .mul(s.actualReserve)
            .div(RAY);

        if (LibAsset.isNativeAsset(_soData.sendingAssetId.toAddress(0))) {
            data._userInput = _soData.amount;
        }
        data.consumeValue = IWormholeBridge(s.tokenBridge)
            .wormhole()
            .messageFee()
            .add(data._userInput)
            .add(data._srcFee);
        if (data.consumeValue <= _wormholeData.wormholeFee) {
            data.flag = true;
            data.returnValue = _wormholeData.wormholeFee.sub(data.consumeValue);
        }
        return (
            data.flag,
            data._srcFee,
            data.returnValue,
            data.dstMaxGasForRelayer
        );
    }

    function estimateRelayerFee(
        ISo.NormalizedSoData calldata _soData,
        NormalizedWormholeData calldata _wormholeData,
        LibSwap.NormalizedSwapData[] calldata _swapDataDst
    ) external view returns (uint256) {
        Storage storage s = getStorage();
        ILibPrice _oracle = ILibPrice(
            appStorage.gatewaySoFeeSelectors[s.tokenBridge]
        );
        (uint256 _ratio, ) = _oracle.getPriceRatio(
            _wormholeData.dstWormholeChainId
        );
        uint256 dstMaxGasForRelayer = estimateCompleteSoSwapGas(
            _soData,
            _wormholeData,
            _swapDataDst
        );
        uint256 _dstFee = dstMaxGasForRelayer.mul(
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

        (uint256 dstMaxGasPriceInWeiForRelayer, , , ) = decodeWormholePayload(
            _wormholePayload.payload
        );

        return dstMaxGasPriceInWeiForRelayer;
    }

    function encodeNormalizedWormholeData(NormalizedWormholeData memory data)
        public
        pure
        returns (bytes memory)
    {
        return
            abi.encodePacked(
                data.dstWormholeChainId,
                data.dstMaxGasPriceInWeiForRelayer,
                data.wormholeFee,
                uint64(data.dstSoDiamond.length),
                data.dstSoDiamond
            );
    }

    function decodeNormalizedWormholeData(bytes memory wormholeData)
        public
        pure
        returns (NormalizedWormholeData memory)
    {
        NormalizedWormholeData memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = 2;
        data.dstWormholeChainId = wormholeData.toUint16(index);
        index += nextLen;

        nextLen = 32;
        data.dstMaxGasPriceInWeiForRelayer = wormholeData.toUint256(index);
        index += nextLen;

        nextLen = 32;
        data.wormholeFee = wormholeData.toUint256(index);
        index += nextLen;

        nextLen = uint256(wormholeData.toUint64(index));
        index += 8;
        data.dstSoDiamond = wormholeData.slice(index, nextLen);
        index += nextLen;

        require(index == wormholeData.length, "Length error");

        return data;
    }

    function encodeWormholePayload(
        uint256 dstMaxGasPrice,
        uint256 dstMaxGas,
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst
    ) public pure returns (bytes memory) {
        bytes memory d1 = LibCross.encodeNormalizedSoData(soData);
        bytes memory d2 = LibCross.encodeNormalizedSwapData(swapDataDst);
        return
            abi.encodePacked(
                dstMaxGasPrice,
                dstMaxGas,
                uint64(d1.length),
                d1,
                uint64(d2.length),
                d2
            );
    }

    struct CachePayload {
        uint256 dstMaxGasPrice;
        uint256 dstMaxGas;
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    function decodeWormholePayload(bytes memory wormholeData)
        public
        pure
        returns (
            uint256,
            uint256,
            ISo.NormalizedSoData memory,
            LibSwap.NormalizedSwapData[] memory
        )
    {
        uint256 index;
        uint256 nextLen;
        CachePayload memory data;

        nextLen = 32;
        data.dstMaxGasPrice = uint256(wormholeData.toUint256(index));
        index += nextLen;

        nextLen = 32;
        data.dstMaxGas = uint256(wormholeData.toUint256(index));
        index += nextLen;

        nextLen = uint256(wormholeData.toUint64(index));
        index += 8;
        data.soData = LibCross.decodeNormalizedSoData(
            wormholeData.slice(index, nextLen)
        );
        index += nextLen;

        if (index < wormholeData.length) {
            nextLen = uint256(wormholeData.toUint64(index));
            index += 8;
            data.swapDataDst = LibCross.decodeNormalizedSwapData(
                wormholeData.slice(index, nextLen)
            );
            index += nextLen;
        }

        require(index == wormholeData.length, "Length error");
        return (
            data.dstMaxGasPrice,
            data.dstMaxGas,
            data.soData,
            data.swapDataDst
        );
    }

    /// Internal Methods ///

    function _startBridge(
        NormalizedWormholeData calldata _wormholeData,
        address _token,
        uint256 _amount,
        uint256 _srcFee,
        bytes memory _payload
    ) internal {
        Storage storage s = getStorage();
        address _bridge = s.tokenBridge;

        bytes32 dstSoDiamond;
        if (_wormholeData.dstSoDiamond.length == 20) {
            dstSoDiamond = bytes32(
                uint256(uint160(_wormholeData.dstSoDiamond.toAddress(0)))
            );
        } else {
            dstSoDiamond = _wormholeData.dstSoDiamond.toBytes32(0);
        }

        if (LibAsset.isNativeAsset(_token)) {
            IWormholeBridge(_bridge).wrapAndTransferETHWithPayload{
                value: msg.value.sub(_srcFee)
            }(_wormholeData.dstWormholeChainId, dstSoDiamond, 0, _payload);
        } else {
            LibAsset.maxApproveERC20(IERC20(_token), _bridge, _amount);
            IWormholeBridge(_bridge).transferTokensWithPayload{
                value: msg.value
            }(
                _token,
                _amount,
                _wormholeData.dstWormholeChainId,
                dstSoDiamond,
                0,
                _payload
            );
        }

        uint256 _dust = LibAsset.getOwnBalance(_token);
        if (_dust > 0) {
            LibAsset.transferAsset(_token, payable(msg.sender), _dust);
        }
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
