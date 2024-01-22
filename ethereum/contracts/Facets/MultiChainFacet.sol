// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Errors/GenericErrors.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibAsset.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/Multichain/IMultiChainAnycallProxy.sol";
import "../Interfaces/Multichain/IMultiChainV7Router.sol";
import "../Interfaces/Multichain/IMultiChainUnderlying.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/ReentrancyGuard.sol";

/// @title MultiChain Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through MultiChain
contract MultiChainFacet is Swapper, ReentrancyGuard, IMultiChainAnycallProxy {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"29b1dcc732f71f6f329711b7ae2f37f88d68bd03cf06d931f287f1c8cf592dde"; // keccak256("com.so.facets.multichain")

    struct Storage {
        address fastRouter; // The multichain FAST_ROUTER_V7 address
        uint64 srcChainId; // The multichain chain id of the source/current chain
        mapping(address => bool) allowedList; // Permission to allow calls to exec
        mapping(address => address) tokenMap; // The map: token -> anytoken
    }

    /// Types ///

    struct MultiChainData {
        uint64 dstChainId; // The multichain chain id of the destination chain
        address bridgeToken; // The underlying token address of the anytoken
        string dstSoDiamond; // The destination SoDiamond address
    }

    struct CacheSrcSoSwap {
        uint256 bridgeAmount;
        bytes payload;
    }

    struct CachePayload {
        ISo.NormalizedSoData soDataNo;
        LibSwap.NormalizedSwapData[] swapDataDstNo;
    }

    /// Events ///
    event MultiChainInitialized(address fastRouter, uint64 chainId);
    event SetAllowedList(address account, bool isAllowed);
    event AnyMappingUpdated(address[] anyTokens);

    /// Init ///

    /// @notice Initializes local variables for the multichain FAST_ROUTER_V7
    /// @param fastRouter: address of the multichain FAST_ROUTER_V7 contract
    /// @param chainId: chainId of this deployed contract
    function initMultiChain(address fastRouter, uint64 chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (fastRouter == address(0)) revert InvalidConfig();

        Storage storage s = getStorage();

        address anycallExecutor = IMultiChainV7Router(fastRouter)
            .anycallExecutor();

        s.fastRouter = fastRouter;
        s.srcChainId = chainId;
        s.allowedList[fastRouter] = true;
        s.allowedList[msg.sender] = true;
        s.allowedList[anycallExecutor] = true;

        emit MultiChainInitialized(fastRouter, chainId);
    }

    /// @dev Set permissions to control calls to exec
    function setAllowedAddress(address account, bool isAllowed) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.allowedList[account] = isAllowed;

        emit SetAllowedList(account, isAllowed);
    }

    /// @notice Updates the tokenAddress > anyTokenAddress storage
    /// @param  anyTokens any token addresses
    function updateAddressMappings(address[] calldata anyTokens) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();

        for (uint64 i; i < anyTokens.length; i++) {
            address token = IMultiChainUnderlying(anyTokens[i]).underlying();
            require(token != address(0), "InvalidAnyToken");
            s.tokenMap[token] = anyTokens[i];
        }

        emit AnyMappingUpdated(anyTokens);
    }

    /// External Methods ///

    /// @notice Bridges tokens via MultiChain
    /// @param soDataNo Data for tracking cross-chain transactions and a
    /// portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    /// transactions on the source chain side
    /// @param multiChainData Data used to call multichain fast router for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    /// on the destination chain.
    /// Call on source chain by user
    function soSwapViaMultiChain(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        MultiChainData calldata multiChainData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        CacheSrcSoSwap memory cache;

        // decode soDataNo and swapDataSrcNo
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        // deposit erc20 tokens to this contract
        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }

        // calculate bridgeAmount
        if (swapDataSrc.length == 0) {
            // direct bridge
            cache.bridgeAmount = soData.amount;
            transferWrappedAsset(
                soData.sendingAssetId,
                multiChainData.bridgeToken,
                cache.bridgeAmount
            );
        } else {
            // bridge after swap
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            try this.executeAndCheckSwaps(soData, swapDataSrc) returns (
                uint256 bridgeAmount
            ) {
                cache.bridgeAmount = bridgeAmount;
                transferWrappedAsset(
                    swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                    multiChainData.bridgeToken,
                    cache.bridgeAmount
                );
            } catch (bytes memory lowLevelData) {
                // Rethrowing exception
                assembly {
                    let start := add(lowLevelData, 0x20)
                    let end := add(lowLevelData, mload(lowLevelData))
                    revert(start, end)
                }
            }
        }

        cache.payload = encodeMultiChainPayload(soDataNo, swapDataDstNo);

        startBridge(multiChainData, cache.bridgeAmount, cache.payload);

        emit SoTransferStarted(soData.transactionId);
    }

    /// @notice Execute a message with an associated token transfer on destination chain.
    /// Call on destination chain by anyCallExecutor
    function exec(
        address token,
        address, // receiver
        uint256 amount,
        bytes calldata message
    ) external returns (bool success, bytes memory result) {
        Storage storage s = getStorage();
        require(s.allowedList[msg.sender], "No permission");

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeMultiChainPayload(message);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        remoteSoSwap(token, amount, soData, swapDataDst);

        return (true, "");
    }

    /// Public Methods ///

    /// CrossData
    // 1. length + transactionId(SoData)
    // 2. length + receiver(SoData)
    // 3. length + receivingAssetId(SoData)
    // 4. length + swapDataLength(u8)
    // 5. length + callTo(SwapData)
    // 6. length + sendingAssetId(SwapData)
    // 7. length + receivingAssetId(SwapData)
    // 8. length + callData(SwapData)
    function encodeMultiChainPayload(
        ISo.NormalizedSoData memory soDataNo,
        LibSwap.NormalizedSwapData[] memory swapDataDstNo
    ) public pure returns (bytes memory) {
        bytes memory encodeData = abi.encodePacked(
            uint8(soDataNo.transactionId.length),
            soDataNo.transactionId,
            uint8(soDataNo.receiver.length),
            soDataNo.receiver,
            uint8(soDataNo.receivingAssetId.length),
            soDataNo.receivingAssetId
        );

        if (swapDataDstNo.length > 0) {
            bytes memory swapLenBytes = LibCross.serializeU256WithHexStr(
                swapDataDstNo.length
            );
            encodeData = encodeData.concat(
                abi.encodePacked(uint8(swapLenBytes.length), swapLenBytes)
            );
        }

        for (uint256 i = 0; i < swapDataDstNo.length; i++) {
            encodeData = encodeData.concat(
                abi.encodePacked(
                    uint8(swapDataDstNo[i].callTo.length),
                    swapDataDstNo[i].callTo,
                    uint8(swapDataDstNo[i].sendingAssetId.length),
                    swapDataDstNo[i].sendingAssetId,
                    uint8(swapDataDstNo[i].receivingAssetId.length),
                    swapDataDstNo[i].receivingAssetId,
                    uint16(swapDataDstNo[i].callData.length),
                    swapDataDstNo[i].callData
                )
            );
        }
        return encodeData;
    }

    /// CrossData
    // 1. length + transactionId(SoData)
    // 2. length + receiver(SoData)
    // 3. length + receivingAssetId(SoData)
    // 4. length + swapDataLength(u8)
    // 5. length + callTo(SwapData)
    // 6. length + sendingAssetId(SwapData)
    // 7. length + receivingAssetId(SwapData)
    // 8. length + callData(SwapData)
    function decodeMultiChainPayload(bytes memory multiChainPayload)
        public
        pure
        returns (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        )
    {
        CachePayload memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(multiChainPayload.toUint8(index));
        index += 1;
        data.soDataNo.transactionId = multiChainPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(multiChainPayload.toUint8(index));
        index += 1;
        data.soDataNo.receiver = multiChainPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(multiChainPayload.toUint8(index));
        index += 1;
        data.soDataNo.receivingAssetId = multiChainPayload.slice(
            index,
            nextLen
        );
        index += nextLen;

        if (index < multiChainPayload.length) {
            nextLen = uint256(multiChainPayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                multiChainPayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDstNo = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(multiChainPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].callTo = multiChainPayload.slice(
                    index,
                    nextLen
                );
                data.swapDataDstNo[i].approveTo = data.swapDataDstNo[i].callTo;
                index += nextLen;

                nextLen = uint256(multiChainPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].sendingAssetId = multiChainPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(multiChainPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].receivingAssetId = multiChainPayload
                    .slice(index, nextLen);
                index += nextLen;

                nextLen = uint256(multiChainPayload.toUint16(index));
                index += 2;
                data.swapDataDstNo[i].callData = multiChainPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        require(index == multiChainPayload.length, "LenErr");

        return (data.soDataNo, data.swapDataDstNo);
    }

    /// @dev Get so fee
    function getMultiChainSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.fastRouter];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(soFee).getFees(amount);
        }
    }

    /// @dev Make sure the multichain config is valid
    function isValidMultiChainConfig() public view returns (bool) {
        Storage storage s = getStorage();
        IMultiChainV7Router.ProxyInfo memory proxyInfo = IMultiChainV7Router(
            s.fastRouter
        ).anycallProxyInfo(address(this));

        return proxyInfo.supported && !proxyInfo.acceptAnyToken;
    }

    /// @dev get the anyToken address
    function getAnyToken(address bridgeToken) public view returns (address) {
        Storage storage s = getStorage();

        return s.tokenMap[bridgeToken];
    }

    /// @dev get the fast router address
    function getFastRouter() public view returns (address) {
        Storage storage s = getStorage();

        return s.fastRouter;
    }

    /// Private Methods ///

    /// @dev swap on destination chain
    function remoteSoSwap(
        address token,
        uint256 amount,
        ISo.SoData memory soData,
        LibSwap.SwapData[] memory swapDataDst
    ) private {
        uint256 soFee = getMultiChainSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
            require(token == soData.receivingAssetId, "TokenErr");

            if (soFee > 0) {
                transferUnwrappedAsset(
                    token,
                    soData.receivingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            transferUnwrappedAsset(
                token,
                soData.receivingAssetId,
                amount,
                soData.receiver
            );
            emit SoTransferCompleted(soData.transactionId, amount);
        } else {
            require(token == swapDataDst[0].sendingAssetId, "TokenErr");

            if (soFee > 0) {
                transferUnwrappedAsset(
                    token,
                    swapDataDst[0].sendingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            transferUnwrappedAsset(
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

            try this.executeAndCheckSwaps(soData, swapDataDst) returns (
                uint256 amountFinal
            ) {
                // may swap to weth
                transferUnwrappedAsset(
                    swapDataDst[swapDataDst.length - 1].receivingAssetId,
                    soData.receivingAssetId,
                    amountFinal,
                    soData.receiver
                );
                emit SoTransferCompleted(soData.transactionId, amountFinal);
            } catch Error(string memory revertReason) {
                LibAsset.transferAsset(
                    swapDataDst[0].sendingAssetId,
                    soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    soData.transactionId,
                    revertReason,
                    bytes("")
                );
            } catch (bytes memory returnData) {
                LibAsset.transferAsset(
                    swapDataDst[0].sendingAssetId,
                    soData.receiver,
                    amount
                );
                emit SoTransferFailed(soData.transactionId, "", returnData);
            }
        }
    }

    /// @dev Conatains the business logic for the bridge via MultiChain
    function startBridge(
        MultiChainData memory multiChainData,
        uint256 bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();

        if (s.srcChainId == multiChainData.dstChainId)
            revert CannotBridgeToSameNetwork();

        address anyToken = s.tokenMap[multiChainData.bridgeToken];
        require(anyToken != address(0), "anyTokenNotFound");

        LibAsset.maxApproveERC20(
            IERC20(multiChainData.bridgeToken),
            s.fastRouter,
            bridgeAmount
        );

        try
            IMultiChainV7Router(s.fastRouter).anySwapOutUnderlyingAndCall(
                anyToken,
                multiChainData.dstSoDiamond,
                bridgeAmount,
                uint256(multiChainData.dstChainId),
                multiChainData.dstSoDiamond,
                payload
            )
        {} catch (bytes memory lowLevelData) {
            // Rethrowing exception
            assembly {
                let start := add(lowLevelData, 0x20)
                let end := add(lowLevelData, mload(lowLevelData))
                revert(start, end)
            }
        }
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
