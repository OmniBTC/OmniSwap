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

    /// Storage ///

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
    event TransferFromWormhole(
        uint16 srcWormholeChainId,
        uint16 dstWormholeChainId,
        uint64 sequence
    );

    /// Types ///

    struct NormalizedWormholeData {
        uint16 dstWormholeChainId;
        uint256 dstMaxGasPriceInWeiForRelayer;
        uint256 wormholeFee;
        bytes dstSoDiamond;
    }

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

    struct CachePayload {
        uint256 dstMaxGasPrice;
        uint256 dstMaxGas;
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    /// Init Methods ///

    /// @dev Set wormhole tokenbridge address and current wormhole chain id
    /// @param tokenBridge wormhole tokenbridge address
    /// @param wormholeChainId current wormhole chain id
    function initWormhole(address tokenBridge, uint16 wormholeChainId)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.tokenBridge = tokenBridge;
        s.srcWormholeChainId = wormholeChainId;
        emit InitWormholeEvent(tokenBridge, wormholeChainId);
    }

    /// @dev Sets the scale to be used when calculating relayer fees
    /// @param actualReserve percentage of actual use of relayer fees, expressed as RAY
    /// @param estimateReserve estimated percentage of use at the time of call, expressed as RAY
    function setWormholeReserve(uint256 actualReserve, uint256 estimateReserve)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.actualReserve = actualReserve;
        s.estimateReserve = estimateReserve;
        emit UpdateWormholeReserve(actualReserve, estimateReserve);
    }

    /// @dev Set the minimum gas to be spent on the target chain
    /// @param dstWormholeChainId destination chain wormhole chain id
    /// @param baseGas basic fee for a successful transaction
    /// @param gasPerBytes the amount of gas needed to transfer each byte of the payload
    function setWormholeGas(
        uint16 dstWormholeChainId,
        uint256 baseGas,
        uint256 gasPerBytes
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.dstBaseGas[dstWormholeChainId] = baseGas;
        s.dstGasPerBytes[dstWormholeChainId] = gasPerBytes;
        emit UpdateWormholeGas(dstWormholeChainId, baseGas, gasPerBytes);
    }

    /// External Methods ///

    /// @dev Bridge tokens via wormhole
    /// @param soDataNo data for tracking cross-chain transactions and a
    ///                 portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param wormholeDataNo data used to call Wormhole's tokenbridge for swap
    /// @param swapDataDstNo contains a set of Swap transaction data executed
    ///                     on the target chain.
    function soSwapViaWormhole(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        NormalizedWormholeData calldata wormholeDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable {
        require(msg.value == wormholeDataNo.wormholeFee, "Fee error");

        CacheSrcSoSwap memory _cache;

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        (
            _cache._flag,
            _cache._fee,
            _cache.returnValue,
            _cache.dstMaxGas
        ) = checkRelayerFee(soDataNo, wormholeDataNo, swapDataDstNo);

        require(_cache._flag, "Check fail");
        // return the redundant msg.value
        if (_cache.returnValue > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(msg.sender),
                _cache.returnValue
            );
        }

        if (_cache._fee > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(LibDiamond.contractOwner()),
                _cache._fee
            );
        }
        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }
        if (swapDataSrc.length == 0) {
            _cache._bridgeAddress = soData.sendingAssetId;
            _cache._bridgeAmount = soData.amount;
            _cache._hasSourceSwap = false;
        } else {
            require(
                soData.amount == swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            _cache._bridgeAmount = this.executeAndCheckSwaps(
                soData,
                swapDataSrc
            );
            _cache._bridgeAddress = swapDataSrc[swapDataSrc.length - 1]
                .receivingAssetId;
            _cache._hasSourceSwap = true;
        }

        _cache._payload = encodeWormholePayload(
            wormholeDataNo.dstMaxGasPriceInWeiForRelayer,
            _cache.dstMaxGas,
            soDataNo,
            swapDataDstNo
        );

        if (swapDataDstNo.length > 0) {
            _cache._hasDestinationSwap = true;
        }

        /// start bridge
        _startBridge(
            wormholeDataNo,
            _cache._bridgeAddress,
            _cache._bridgeAmount,
            _cache._payload
        );

        emit ISo.SoTransferStarted(
            soData.transactionId,
            "Wormhole",
            _cache._hasSourceSwap,
            _cache._hasDestinationSwap,
            soData
        );
    }

    /// @notice Receiving chain's native tokens crossed over from other chains
    /// @dev for relayer automatic call
    function completeTransferAndUnwrapETHWithPayload(bytes memory _encodeVm)
        external
    {
        completeSoSwap(_encodeVm);
    }

    /// @notice Receiving erc20 tokens crossed over from other chains
    /// @dev for relayer automatic call
    function completeTransferWithPayload(bytes memory _encodeVm) external {
        completeSoSwap(_encodeVm);
    }

    /// @notice Users can manually call for cross-chain tokens
    function completeSoSwap(bytes memory _encodeVm) public {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;

        bytes memory payload = IWormholeBridge(bridge)
            .completeTransferWithPayload(_encodeVm);

        IWormholeBridge.TransferWithPayload
            memory wormholePayload = IWormholeBridge(bridge)
                .parseTransferWithPayload(payload);

        (
            ,
            ,
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeWormholePayload(wormholePayload.payload);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        address _tokenAddress;
        bool _isOriginChain;
        if (wormholePayload.tokenChain == IWormholeBridge(bridge).chainId()) {
            _tokenAddress = address(
                uint160(uint256(wormholePayload.tokenAddress))
            );
            _isOriginChain = true;
        } else {
            _tokenAddress = IWormholeBridge(bridge).wrappedAsset(
                wormholePayload.tokenChain,
                wormholePayload.tokenAddress
            );
        }

        uint256 amount = LibAsset.getOwnBalance(_tokenAddress);
        require(amount > 0, "amount > 0");

        IWETH _weth = IWormholeBridge(bridge).WETH();

        if (_isOriginChain && address(_weth) == _tokenAddress) {
            _weth.withdraw(amount);
            _tokenAddress = LibAsset.NATIVE_ASSETID;
        }

        uint256 soFee = getSoFee(amount);
        if (soFee > 0 && soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
            require(_tokenAddress == soData.receivingAssetId, "token error");
            if (soFee > 0) {
                LibAsset.transferAsset(
                    soData.receivingAssetId,
                    payable(LibDiamond.contractOwner()),
                    soFee
                );
            }
            LibAsset.transferAsset(
                soData.receivingAssetId,
                soData.receiver,
                amount
            );
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
                LibAsset.transferAsset(
                    swapDataDst[0].sendingAssetId,
                    payable(LibDiamond.contractOwner()),
                    soFee
                );
            }
            require(
                swapDataDst[0].sendingAssetId == _tokenAddress,
                "token error"
            );

            swapDataDst[0].fromAmount = amount;

            address _correctSwap = appStorage.correctSwapRouterSelectors;

            if (_correctSwap != address(0)) {
                swapDataDst[0].callData = ICorrectSwap(_correctSwap)
                    .correctSwap(
                        swapDataDst[0].callData,
                        swapDataDst[0].fromAmount
                    );
            }

            try this.executeAndCheckSwaps(soData, swapDataDst) returns (
                uint256 _amountFinal
            ) {
                LibAsset.transferAsset(
                    swapDataDst[swapDataDst.length - 1].receivingAssetId,
                    soData.receiver,
                    _amountFinal
                );
                emit SoTransferCompleted(
                    soData.transactionId,
                    soData.receivingAssetId,
                    soData.receiver,
                    _amountFinal,
                    block.timestamp,
                    soData
                );
            } catch Error(string memory revertReason) {
                LibAsset.transferAsset(
                    soData.receivingAssetId,
                    soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    soData.transactionId,
                    revertReason,
                    bytes(""),
                    soData
                );
            } catch (bytes memory returnData) {
                LibAsset.transferAsset(
                    soData.receivingAssetId,
                    soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    soData.transactionId,
                    "",
                    returnData,
                    soData
                );
            }
        }
    }

    /// @dev Estimate the minimum gas to be consumed at the target chain
    /// @param soData used to encode into payload
    /// @param wormholeData used to encode into payload
    /// @param swapDataDst used to encode into payload
    function estimateCompleteSoSwapGas(
        ISo.NormalizedSoData calldata soData,
        NormalizedWormholeData calldata wormholeData,
        LibSwap.NormalizedSwapData[] calldata swapDataDst
    ) public view returns (uint256) {
        bytes memory _payload = encodeWormholePayload(
            wormholeData.dstMaxGasPriceInWeiForRelayer,
            0,
            soData,
            swapDataDst
        );
        Storage storage s = getStorage();
        return
            s.dstBaseGas[wormholeData.dstWormholeChainId].add(
                s.dstGasPerBytes[wormholeData.dstWormholeChainId].mul(
                    _payload.length
                )
            );
    }

    /// @dev Check if enough value is passed in for payment
    function checkRelayerFee(
        ISo.NormalizedSoData calldata soData,
        NormalizedWormholeData calldata wormholeData,
        LibSwap.NormalizedSwapData[] calldata swapDataDst
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
        data._ratio = _oracle.updatePriceRatio(wormholeData.dstWormholeChainId);
        data.dstMaxGasForRelayer = estimateCompleteSoSwapGas(
            soData,
            wormholeData,
            swapDataDst
        );

        data._dstFee = data.dstMaxGasForRelayer.mul(
            wormholeData.dstMaxGasPriceInWeiForRelayer
        );
        data._srcFee = data
            ._dstFee
            .mul(data._ratio)
            .div(_oracle.RAY())
            .mul(s.actualReserve)
            .div(RAY);

        if (LibAsset.isNativeAsset(soData.sendingAssetId.toAddress(0))) {
            data._userInput = soData.amount;
        }
        data.consumeValue = IWormholeBridge(s.tokenBridge)
            .wormhole()
            .messageFee()
            .add(data._userInput)
            .add(data._srcFee);
        if (data.consumeValue <= wormholeData.wormholeFee) {
            data.flag = true;
            data.returnValue = wormholeData.wormholeFee.sub(data.consumeValue);
        }
        return (
            data.flag,
            data._srcFee,
            data.returnValue,
            data.dstMaxGasForRelayer
        );
    }

    /// @dev Estimated relayer cost, which needs to be paid by the user
    function estimateRelayerFee(
        ISo.NormalizedSoData calldata soData,
        NormalizedWormholeData calldata wormholeData,
        LibSwap.NormalizedSwapData[] calldata swapDataDst
    ) external view returns (uint256) {
        Storage storage s = getStorage();
        ILibPrice _oracle = ILibPrice(
            appStorage.gatewaySoFeeSelectors[s.tokenBridge]
        );
        (uint256 _ratio, ) = _oracle.getPriceRatio(
            wormholeData.dstWormholeChainId
        );
        uint256 dstMaxGasForRelayer = estimateCompleteSoSwapGas(
            soData,
            wormholeData,
            swapDataDst
        );
        uint256 _dstFee = dstMaxGasForRelayer.mul(
            wormholeData.dstMaxGasPriceInWeiForRelayer
        );
        uint256 _srcFee = _dstFee
            .mul(_ratio)
            .div(_oracle.RAY())
            .mul(s.estimateReserve)
            .div(RAY);
        return _srcFee;
    }

    function getWormholeMessageFee() public view returns (uint256) {
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

        nextLen = uint256(wormholeData.toUint64(index));
        index += 8;
        if (index < wormholeData.length) {
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
        NormalizedWormholeData calldata wormholeData,
        address _token,
        uint256 _amount,
        bytes memory _payload
    ) internal {
        Storage storage s = getStorage();
        address _bridge = s.tokenBridge;

        bytes32 dstSoDiamond;
        if (wormholeData.dstSoDiamond.length == 20) {
            dstSoDiamond = bytes32(
                uint256(uint160(wormholeData.dstSoDiamond.toAddress(0)))
            );
        } else {
            dstSoDiamond = wormholeData.dstSoDiamond.toBytes32(0);
        }

        uint64 sequence;
        uint256 wormhole_msg_fee = getWormholeMessageFee();
        if (LibAsset.isNativeAsset(_token)) {
            sequence = IWormholeBridge(_bridge).wrapAndTransferETHWithPayload{
                value: _amount + wormhole_msg_fee
            }(wormholeData.dstWormholeChainId, dstSoDiamond, 0, _payload);
        } else {
            LibAsset.maxApproveERC20(IERC20(_token), _bridge, _amount);
            sequence = IWormholeBridge(_bridge).transferTokensWithPayload{
                value: wormhole_msg_fee
            }(
                _token,
                _amount,
                wormholeData.dstWormholeChainId,
                dstSoDiamond,
                0,
                _payload
            );
        }

        uint256 _dust = LibAsset.getOwnBalance(_token);
        if (_dust > 0) {
            LibAsset.transferAsset(_token, payable(msg.sender), _dust);
        }

        emit TransferFromWormhole(
            s.srcWormholeChainId,
            wormholeData.dstWormholeChainId,
            sequence
        );
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
