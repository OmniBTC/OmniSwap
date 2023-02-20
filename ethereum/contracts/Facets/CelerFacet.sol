// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Errors/GenericErrors.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibCelerMessageSender.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ICelerMessageBus.sol";
import "../Interfaces/ICelerBridge.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Helpers/CelerMessageReceiver.sol";

/// @title Celer Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through Celer
contract CelerFacet is Swapper, ReentrancyGuard, CelerMessageReceiver {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"5a7c277686f4a9ab3396ccbfbeac4866fb97785944f0661a3f0935d16bc9848b"; // keccak256("com.so.facets.celer")

    struct Storage {
        uint64  nextNonce; // The next nonce for celer bridge
        uint64  srcCelerChainId; // The Celer chain id of the source/current chain
        address messageBus; // The Celer MessageBus address
        mapping(address => bool) allowedList; // Permission to allow calls to sgReceive
    }

    /// Types ///

    struct CelerData {
        uint32  maxSlippage;  // The max slippage accepted
        uint64  dstCelerChainId; // The celer chain id of the destination chain
        address bridgeToken; // The bridge token address
        address payable dstSoDiamond; // destination SoDiamond address
    }

    struct CachePayload {
        ISo.NormalizedSoData soDataNo;
        LibSwap.NormalizedSwapData[] swapDataDstNo;
    }

    /// Events ///

    event CelerInitialized(address indexed messageBus, uint256 chainId);
    event SetMessageBus(address indexed messageBus);
    event SetAllowedList(address indexed messageBus, bool isAllowed);
    event CelerTransferId(bytes32 indexed transferId);

    /// Init ///

    /// @notice Initializes local variables for the Celer MessgeBus
    /// @param messageBus: address of the Celer messageBus contract
    /// @param chainId: chainId of this deployed contract
    function initCeler(address messageBus, uint64 chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (messageBus == address(0)) revert InvalidConfig();

        Storage storage s = getStorage();

        s.nextNonce = 1;
        s.messageBus = messageBus;
        s.srcCelerChainId = chainId;
        s.allowedList[messageBus] = true;
        s.allowedList[msg.sender] = true;

        emit CelerInitialized(messageBus, chainId);
    }

    /// @dev Set permissions to control calls to executeMessageWithTransfer
    function setAllowedAddress(address messageBus, bool isAllowed) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.allowedList[messageBus] = isAllowed;

        emit SetAllowedList(messageBus, isAllowed);
    }

    /// @dev Set new messageBus
    function setMessageBus(address messageBus) external
    {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.messageBus = messageBus;
        s.allowedList[messageBus] = true;

        emit SetMessageBus(messageBus);
    }

    /// External Methods ///

    /// @notice Bridges tokens via Celer (support chainid [1,65535])
    /// @param soDataNo Data for tracking cross-chain transactions and a
    /// portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    /// transactions on the source chain side
    /// @param celerData Data used to call Celer Message Bus for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    /// on the target chain.
    function soSwapViaCeler(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        CelerData calldata celerData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        uint256 bridgeAmount;

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
            bridgeAmount = soData.amount;
            transferWrappedAsset(
                soData.sendingAssetId,
                celerData.bridgeToken,
                bridgeAmount
            );
        } else {
            // bridge after swap
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            transferWrappedAsset(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                celerData.bridgeToken,
                bridgeAmount
            );
        }

        uint256 messageFee = getCelerValue(soData);
        bytes memory payload = encodeCelerPayload(soDataNo, swapDataDstNo);

        startBridge(
            celerData,
            messageFee,
            bridgeAmount,
            payload
        );

        emit SoTransferStarted(soData.transactionId);
    }

    /// @notice Called by Celer MessageBus to execute a message with an associated token transfer.
    function executeMessageWithTransfer(
        address, //sender,
        address token,
        uint256 amount,
        uint64, // srcChainId
        bytes calldata message,
        address // executor
    ) external payable override returns (ExecutionStatus) {
        Storage storage s = getStorage();
        require(s.allowedList[msg.sender], "No permission");

        if (LibAsset.getOwnBalance(token) < amount) {
            // judge eth
            require(token == this.getNativeWrap(s.messageBus), "TokenErr");
            require(
                LibAsset.getOwnBalance(LibAsset.NATIVE_ASSETID) >= amount,
                "NotEnough"
            );

            token = LibAsset.NATIVE_ASSETID;
        }

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeCelerPayload(message);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        remoteSoSwap(token, amount, soData, swapDataDst);

        return ExecutionStatus.Success;
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
    function encodeCelerPayload(
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
    function decodeCelerPayload(
        bytes memory celerPayload
    ) public pure returns (
        ISo.NormalizedSoData memory soDataNo,
        LibSwap.NormalizedSwapData[] memory swapDataDstNo
    )
    {
        CachePayload memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(celerPayload.toUint8(index));
        index += 1;
        data.soDataNo.transactionId = celerPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(celerPayload.toUint8(index));
        index += 1;
        data.soDataNo.receiver = celerPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(celerPayload.toUint8(index));
        index += 1;
        data.soDataNo.receivingAssetId = celerPayload.slice(index, nextLen);
        index += nextLen;

        if (index < celerPayload.length) {
            nextLen = uint256(celerPayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                celerPayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDstNo = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(celerPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].callTo = celerPayload.slice(
                    index,
                    nextLen
                );
                data.swapDataDstNo[i].approveTo = data.swapDataDstNo[i].callTo;
                index += nextLen;

                nextLen = uint256(celerPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].sendingAssetId = celerPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(celerPayload.toUint8(index));
                index += 1;
                data.swapDataDstNo[i].receivingAssetId = celerPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(celerPayload.toUint16(index));
                index += 2;
                data.swapDataDstNo[i].callData = celerPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        require(index == celerPayload.length, "LenErr");
        return (data.soDataNo, data.swapDataDstNo);
    }

    /// @dev Used to obtain celer cross-chain message fee
    function getCelerMessageFee1(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) public view returns (uint256) {
        Storage storage s = getStorage();
        bytes memory message = encodeCelerPayload(soDataNo, swapDataDstNo);

        return ICelerMessageBus(s.messageBus).calcFee(message);
    }

    /// @dev Calculate celer message fee
    function getCelerMessageFee2(
        address messageBus,
        bytes calldata message
    ) public view returns (uint256) {
        return ICelerMessageBus(messageBus).calcFee(message);
    }

    /// @dev Get celer native wrap address
    function getNativeWrap(address messageBus) public view returns (address) {
        address bridge = ICelerMessageBus(messageBus).liquidityBridge();

        return ICelerBridge(bridge).nativeWrap();
    }

    /// @dev Get so fee
    function getCelerSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.messageBus];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(soFee).getFees(amount);
        }
    }

    /// Private Methods ///

    /// @dev swap on destination chain
    function remoteSoSwap(
        address token,
        uint256 amount,
        ISo.SoData memory soData,
        LibSwap.SwapData[] memory swapDataDst
    ) private {
        uint256 soFee = getCelerSoFee(amount);
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
                emit SoTransferFailed(soData.transactionId, revertReason, bytes(""));
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

    /// @dev Checks for celer pool-based bridge
    function checkBridge(
        CelerData memory celerData,
        address messageBus,
        uint256 bridgeAmount
    ) private {
        address bridge = ICelerMessageBus(messageBus).liquidityBridge();
        uint256 minSend = ICelerBridge(bridge).minSend(celerData.bridgeToken);
        uint256 maxSend = ICelerBridge(bridge).maxSend(celerData.bridgeToken);
        uint256 minMaxSlippage = ICelerBridge(bridge).minimalMaxSlippage();

        require(minSend < bridgeAmount && bridgeAmount <= maxSend, "bridgeAmountErr");
        require(celerData.maxSlippage > minMaxSlippage, "maxSlippageErr");
    }

    /// @dev Conatains the business logic for the bridge via Celer
    function startBridge(
        CelerData memory celerData,
        uint256 messageFee,
        uint256 bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();
        address messageBus = s.messageBus;

        if (s.srcCelerChainId == celerData.dstCelerChainId)
            revert CannotBridgeToSameNetwork();

        checkBridge(celerData, messageBus, bridgeAmount);
        require(messageFee >= this.getCelerMessageFee2(messageBus, payload), "messageFeeErr");

        // 2023.02: only evm chains
        bytes32 transferId = LibCelerMessageSender.sendMessageWithTransfer(
            celerData.dstSoDiamond,
            celerData.bridgeToken,
            bridgeAmount,
            celerData.dstCelerChainId,
            s.nextNonce,
            celerData.maxSlippage,
            payload,
            messageBus,
            messageFee
        );
        // Update nonce
        s.nextNonce = s.nextNonce + 1;

        emit CelerTransferId(transferId);
    }

    /// @dev Separate celer message fee from msg.value
    function getCelerValue(SoData memory soData) private view returns (uint256) {
        if (LibAsset.isNativeAsset(soData.sendingAssetId)) {
            require(msg.value > soData.amount, "NotEnough");
            return msg.value.sub(soData.amount);
        } else {
            return msg.value;
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
