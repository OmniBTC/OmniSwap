// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Errors/GenericErrors.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibCelerMessageSender.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/Celer/ICelerMessageBus.sol";
import "../Interfaces/Celer/ICelerBridge.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Interfaces/ILibPriceV2.sol";
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

    uint256 public constant RAY = 1e27;
    uint256 public constant GasPerByte = 68;

    struct Storage {
        address messageBus; // The Celer MessageBus address
        address executorFeeTo; // The receiver of the executor fee.
        uint64 nextNonce; // The next nonce for celer bridge
        uint64 srcCelerChainId; // The Celer chain id of the source/current chain
        uint256 actualReserve; // [RAY]
        uint256 estimateReserve; // [RAY]
        mapping(uint64 => uint256) dstBaseGas; // For estimate destination chain execute gas
        mapping(address => bool) allowedList; // Permission to allow calls to executeMessageWithTransfer
    }

    /// Types ///

    struct CelerData {
        address sender;
        uint32 maxSlippage; // The max slippage accepted
        uint64 dstCelerChainId; // The celer chain id of the destination chain
        address bridgeToken; // The bridge token address
        uint256 dstMaxGasPriceInWeiForExecutor; // The gas price on destination chain
        uint256 estimateCost; // The msg.value = message fee(for SGN) + executor fee(for executor) + native_gas(optional)
        address payable dstSoDiamond; // The destination SoDiamond address
    }

    struct CacheSrcSoSwap {
        bool flag;
        uint256 srcMessageFee;
        uint256 srcExecutorFee;
        uint256 srcMaybeInput;
        uint256 dstMaxGasForExecutor;
        uint256 bridgeAmount;
        bytes payload;
    }

    struct CacheCheck {
        bool flag;
        uint256 srcExecutorFee;
        uint256 userInput;
        uint256 dstMaxGasForExecutor;
        uint256 srsMessageFee;
        uint256 consumeValue;
    }

    struct CacheEstimate {
        ILibPriceV2 oracle;
        uint256 ratio;
        bytes message;
        uint256 srcMessageFee;
        uint256 dstExecutorGas;
        uint256 dstExecutorFee;
        uint256 srcExecutorFee;
        uint256 reserve;
    }

    struct CachePayload {
        address sender;
        ISo.NormalizedSoData soDataNo;
        LibSwap.NormalizedSwapData[] swapDataDstNo;
    }

    /// Events ///

    event CelerInitialized(address indexed messageBus, uint256 chainId);
    event SetMessageBus(address indexed messageBus);
    event SetAllowedList(address indexed messageBus, bool isAllowed);
    event UpdateCelerReserve(uint256 actualReserve, uint256 estimateReserve);
    event TransferFromCeler(
        bytes32 indexed celerTransferId,
        uint64 srcCelerChainId,
        uint64 dstCelerChainId,
        address bridgeToken,
        uint256 bridgeAmount,
        uint64 nonce
    );
    event RefundCelerToken(
        address indexed token,
        address sender,
        uint256 amount,
        bytes32 srcTxId
    );

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
        s.executorFeeTo = LibDiamond.contractOwner();
        s.srcCelerChainId = chainId;
        s.actualReserve = (RAY).mul(11).div(10); // 110%
        s.estimateReserve = (RAY).mul(12).div(10); // 120%
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

    /// @dev Set new nonce
    /// Avoid celer revert "transfer exists" after redeploy this contract
    function setNonce(uint64 nonce) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.nextNonce = nonce;
    }

    /// @dev Set new receiver of the executor fee
    function setExecutorFeeTo(address feeTo) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.executorFeeTo = feeTo;
    }

    /// @dev Sets the scale to be used when calculating executor fees
    /// @param actualReserve percentage of actual use of executor fees, expressed as RAY
    /// @param estimateReserve estimated percentage of use at the time of call, expressed as RAY
    function setCelerReserve(uint256 actualReserve, uint256 estimateReserve)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        s.actualReserve = actualReserve;
        s.estimateReserve = estimateReserve;

        emit UpdateCelerReserve(actualReserve, estimateReserve);
    }

    /// @dev Set the minimum gas to be spent on the destination chain
    /// @param dstChainIds  a batch of destination chain id
    /// @param dstBaseGas  base gas for destination chain
    function setBaseGas(uint64[] calldata dstChainIds, uint256 dstBaseGas)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        for (uint64 i; i < dstChainIds.length; i++) {
            s.dstBaseGas[dstChainIds[i]] = dstBaseGas;
        }
    }

    /// External Methods ///

    /// @notice Bridges tokens via Celer (support chainid [1,65535])
    /// @param soDataNo Data for tracking cross-chain transactions and a
    /// portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    /// transactions on the source chain side
    /// @param celerData Data used to call Celer Message Bus for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    /// on the destination chain.
    /// Call on source chain by user
    function soSwapViaCeler(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        CelerData calldata celerData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        require(msg.value == celerData.estimateCost, "FeeErr");

        CacheSrcSoSwap memory cache;

        // decode soDataNo and swapDataSrcNo
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        (
            cache.flag,
            cache.srcExecutorFee,
            cache.dstMaxGasForExecutor,
            cache.srcMaybeInput
        ) = checkExecutorFee(soDataNo, celerData, swapDataDstNo);

        require(cache.flag, "CheckFail");

        if (cache.srcExecutorFee > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(getExecutorFeeTo()),
                cache.srcExecutorFee
            );
        }

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
                celerData.bridgeToken,
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
                    celerData.bridgeToken,
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

        cache.payload = encodeCelerPayload(
            celerData.sender,
            soDataNo,
            swapDataDstNo
        );

        cache.srcMessageFee = getCelerMessageFee2(cache.payload);

        startBridge(
            celerData,
            cache.srcMessageFee,
            cache.bridgeAmount,
            cache.payload
        );

        uint256 returnValue = msg
            .value
            .sub(cache.srcMessageFee)
            .sub(cache.srcExecutorFee)
            .sub(cache.srcMaybeInput);

        // return the redundant msg.value
        if (returnValue > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(msg.sender),
                returnValue
            );
        }

        emit SoTransferStarted(soData.transactionId);
    }

    /// @notice Called by Celer MessageBus to execute a message with an associated token transfer.
    /// Call on destination chain by executor
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
            ,
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

    /// @notice Called by MessageBus to process refund of the original transfer from this contract.
    /// The contract is guaranteed to have received the refund before this function is called.
    /// Call on source chain by executor
    function executeMessageWithTransferRefund(
        address token,
        uint256 amount,
        bytes calldata message,
        address // executor
    ) external payable override returns (ExecutionStatus) {
        Storage storage s = getStorage();
        require(s.allowedList[msg.sender], "No permission");

        (
            address sender,
            ISo.NormalizedSoData memory soDataNo,

        ) = decodeCelerPayload(message);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);

        if (sender != address(0)) {
            LibAsset.transferAsset(token, payable(sender), amount);
        }

        emit RefundCelerToken(token, sender, amount, soData.transactionId);

        return ExecutionStatus.Success;
    }

    /// Public Methods ///

    /// @dev Check if enough value is passed in for payment
    function checkExecutorFee(
        ISo.NormalizedSoData calldata soData,
        CelerData calldata celerData,
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

        require(
            appStorage.gatewaySoFeeSelectors[s.messageBus] != address(0),
            "SoFeeEmpty"
        );
        ILibPriceV2 oracle = ILibPriceV2(
            appStorage.gatewaySoFeeSelectors[s.messageBus]
        );

        oracle.updatePriceRatio(celerData.dstCelerChainId);

        (
            data.srsMessageFee,
            data.dstMaxGasForExecutor,
            data.srcExecutorFee
        ) = estCelerMessageFeeAndExecutorFee(
            celerData.dstCelerChainId,
            celerData.dstMaxGasPriceInWeiForExecutor,
            soData,
            swapDataDst,
            true
        );

        if (LibAsset.isNativeAsset(soData.sendingAssetId.toAddress(0))) {
            data.userInput = soData.amount;
        }

        data.consumeValue = data.srsMessageFee.add(data.srcExecutorFee).add(
            data.userInput
        );

        if (data.consumeValue <= celerData.estimateCost) {
            data.flag = true;
        }

        return (
            data.flag,
            data.srcExecutorFee,
            data.dstMaxGasForExecutor,
            data.userInput
        );
    }

    /// CrossData
    // 1. length + sender
    // 2. length + transactionId(SoData)
    // 3. length + receiver(SoData)
    // 4. length + receivingAssetId(SoData)
    // 5. length + swapDataLength(u8)
    // 6. length + callTo(SwapData)
    // 7. length + sendingAssetId(SwapData)
    // 8. length + receivingAssetId(SwapData)
    // 9. length + callData(SwapData)
    function encodeCelerPayload(
        address sender,
        ISo.NormalizedSoData memory soDataNo,
        LibSwap.NormalizedSwapData[] memory swapDataDstNo
    ) public pure returns (bytes memory) {
        bytes memory senderByte = abi.encodePacked(sender);

        bytes memory encodeData = abi.encodePacked(
            uint8(senderByte.length),
            senderByte,
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
    // 1. length + sender
    // 2. length + transactionId(SoData)
    // 3. length + receiver(SoData)
    // 4. length + receivingAssetId(SoData)
    // 5. length + swapDataLength(u8)
    // 6. length + callTo(SwapData)
    // 7. length + sendingAssetId(SwapData)
    // 8. length + receivingAssetId(SwapData)
    // 9. length + callData(SwapData)
    function decodeCelerPayload(bytes memory celerPayload)
        public
        pure
        returns (
            address,
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        )
    {
        CachePayload memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(celerPayload.toUint8(index));
        index += 1;
        data.sender = LibCross.tryAddress(celerPayload.slice(index, nextLen));
        index += nextLen;

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

        return (data.sender, data.soDataNo, data.swapDataDstNo);
    }

    /// @dev Estimate celer cross-chain message fee and executor fee
    function estCelerMessageFeeAndExecutorFee(
        uint64 dstCelerChainId,
        uint256 dstMaxGasPriceInWeiForExecutor,
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo,
        bool is_actual
    )
        public
        view
        returns (
            uint256,
            uint256,
            uint256
        )
    {
        CacheEstimate memory c;
        Storage storage s = getStorage();

        require(
            appStorage.gatewaySoFeeSelectors[s.messageBus] != address(0),
            "SoFeeEmpty"
        );
        c.oracle = ILibPriceV2(appStorage.gatewaySoFeeSelectors[s.messageBus]);

        (c.ratio, ) = c.oracle.getPriceRatio(dstCelerChainId);

        // Only for estimate gas
        c.message = encodeCelerPayload(address(0), soDataNo, swapDataDstNo);

        c.srcMessageFee = getCelerMessageFee1(s.messageBus, c.message);

        c.dstExecutorGas = s.dstBaseGas[dstCelerChainId].add(
            GasPerByte.mul(c.message.length)
        );

        c.dstExecutorFee = c.dstExecutorGas.mul(dstMaxGasPriceInWeiForExecutor);

        if (is_actual) {
            c.reserve = s.actualReserve;
        } else {
            c.reserve = s.estimateReserve;
        }

        c.srcExecutorFee = c
            .dstExecutorFee
            .mul(c.ratio)
            .div(c.oracle.RAY())
            .mul(c.reserve)
            .div(RAY);

        return (c.srcMessageFee, c.dstExecutorGas, c.srcExecutorFee);
    }

    /// @dev Calculate celer message fee
    function getCelerMessageFee1(address messageBus, bytes memory message)
        public
        view
        returns (uint256)
    {
        return ICelerMessageBus(messageBus).calcFee(message);
    }

    /// @dev Calculate celer message fee
    function getCelerMessageFee2(bytes memory message)
        public
        view
        returns (uint256)
    {
        Storage storage s = getStorage();
        return getCelerMessageFee1(s.messageBus, message);
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

    /// @dev Get nonce
    function getNonce() public view returns (uint64) {
        Storage storage s = getStorage();
        return s.nextNonce;
    }

    /// @dev Get base gas of destination chain
    function getBaseGas(uint64 dstChainId) public view returns (uint256) {
        Storage storage s = getStorage();
        return s.dstBaseGas[dstChainId];
    }

    /// @dev Get the receiver of the executor fee
    function getExecutorFeeTo() public view returns (address) {
        Storage storage s = getStorage();
        return s.executorFeeTo;
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

    /// @dev Checks for celer pool-based bridge
    function checkBridge(
        CelerData memory celerData,
        address messageBus,
        uint256 bridgeAmount
    ) private view {
        address bridge = ICelerMessageBus(messageBus).liquidityBridge();
        uint256 minSend = ICelerBridge(bridge).minSend(celerData.bridgeToken);
        uint256 maxSend = ICelerBridge(bridge).maxSend(celerData.bridgeToken);
        uint256 minMaxSlippage = ICelerBridge(bridge).minimalMaxSlippage();

        require(
            minSend < bridgeAmount && bridgeAmount <= maxSend,
            "bridgeAmountErr"
        );
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

        emit TransferFromCeler(
            transferId,
            s.srcCelerChainId,
            celerData.dstCelerChainId,
            celerData.bridgeToken,
            bridgeAmount,
            s.nextNonce
        );

        // Update nonce
        s.nextNonce = s.nextNonce + 1;
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
