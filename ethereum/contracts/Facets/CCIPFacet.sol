// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Errors/GenericErrors.sol";
import "../Libraries/LibCCIPClient.sol";
import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibAsset.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Interfaces/ILibPrice.sol";
import "../Interfaces/ICCIPRouterClient.sol";
import "../Interfaces/IAny2EVMMessageReceiver.sol";
import "../Interfaces/IERC165.sol";

/// @title CCIP Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through CCIP
contract CCIPFacet is Swapper, ReentrancyGuard, IAny2EVMMessageReceiver {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
    hex"115c77a130824400d839f1a193041dfaef0cb83dbbe297c6b2d0a2f7a794bc1e"; // keccak256("com.so.facets.ccip")

    struct Storage {
        uint64 chainSelector;
        address router;
        mapping(uint64 => mapping(address => bool)) allowedSources;
    }

    struct CCIPData {
        uint64 dstChainSelector;
        address dstDiamond;
        address bridgeToken;
        address payFeesIn;
        bytes extraArgs;
    }

    struct CachePayload {
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    /// Events ///

    // Event emitted when setup ccip storage
    event CCIPFacetInitialized(uint64 chainSelector, address router);
    event setCCIPFacetAllowedSource(uint64 chainSelector, address sender, bool allow);

    // Event emitted when a message is sent to another chain.
    event CCIPMessageSent(
        bytes32 indexed messageId, // The unique ID of the message.
        uint64 indexed dstChainSelector, // The chain selector of the destination chain.
        address dstDiamond, // The address of the receiver contract on the destination chain.
        address sender, // The message being sent - will be the EOA of the person sending tokens.
        Client.EVMTokenAmount tokenAmount, // The token amount that was sent.
        uint256 fees // The fees paid for sending the message.
    );

    // Event emitted when a message is received from another chain.
    event CCIPMessageReceived(
        bytes32 indexed messageId, // The unique ID of the message.
        uint64 indexed srcChainSelector, // The chain selector of the source chain.
        address srcDiamond, // The address of the sender from the source chain.
        address receiver, // The token receiver
        Client.EVMTokenAmount tokenAmount // The token amount that was sent.
    );

    /// External Methods ///

    /// @notice Initializes local variables for the ccip facet
    /// @param _chainSelector ccip chain id
    /// @param _router ccip router
    function initCCIP(uint64 _chainSelector, address _router) external {
        LibDiamond.enforceIsContractOwner();
        if (_router == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.chainSelector = _chainSelector;
        s.router = _router;

        // add supported interface
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        ds.supportedInterfaces[type(IERC165).interfaceId] = true;
        ds.supportedInterfaces[
        type(IAny2EVMMessageReceiver).interfaceId
        ] = true;

        emit CCIPFacetInitialized(_chainSelector, _router);
    }

    function setCCIPAllowedSource(
        uint64 _chainSelector,
        address _sender,
        bool _allow
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.allowedSources[_chainSelector][_sender] = _allow;

        emit setCCIPFacetAllowedSource(_chainSelector, _sender, _allow);
    }

    /// @notice Bridges tokens via CCIP
    /// @param soDataNo Data for tracking cross-chain transactions and a
    ///                portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param ccipData Data used to call CCIP's router for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    ///                     on the target chain.
    function soSwapViaCCIP(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        CCIPData calldata ccipData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        uint256 bridgeAmount;

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }
        if (swapDataSrc.length == 0) {
            require(soData.sendingAssetId == ccipData.bridgeToken, "TokenErr");
            bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            require(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId ==
                ccipData.bridgeToken,
                "TokenErr"
            );
        }
        bytes memory payload = encodeCCIPPayload(soDataNo, swapDataDstNo);
        Client.EVMTokenAmount memory bridgeTokenAmount = Client.EVMTokenAmount({
            token: ccipData.bridgeToken,
            amount: bridgeAmount
        });

        Client.EVMTokenAmount[]
        memory tokenAmounts = new Client.EVMTokenAmount[](1);
        tokenAmounts[0] = bridgeTokenAmount;

        require(bridgeAmount > 0, "bridgeAmount>0");
        _startBridge(ccipData, tokenAmounts, payload);

        emit SoTransferStarted(soData.transactionId);
    }

    function ccipReceive(Client.Any2EVMMessage calldata message)
    external
    override
    {
        Storage storage s = getStorage();
        require(msg.sender == s.router, "InvalidSender");
        require(
            s.allowedSources[message.sourceChainSelector][
            abi.decode(message.sender, (address))
            ],
            "InvalidSource"
        );

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeCCIPPayload(message.data);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        Client.EVMTokenAmount[] memory tokenAmounts = message.destTokenAmounts;
        address token = tokenAmounts[0].token;
        uint256 amount = tokenAmounts[0].amount;

        uint256 soFee = getCCIPSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
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
            emit SoTransferCompleted(soData.transactionId, amount);
        } else {
            if (soFee > 0) {
                LibAsset.transferAsset(
                    swapDataDst[0].sendingAssetId,
                    payable(LibDiamond.contractOwner()),
                    soFee
                );
            }
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

        emit CCIPMessageReceived(
            message.messageId,
            message.sourceChainSelector,
            abi.decode(message.sender, (address)),
            soData.receiver,
            message.destTokenAmounts[0]
        );
    }

    function getCCIPExtraArgs(uint256 gasLimit, bool strict)
    public
    view
    returns (bytes memory)
    {
        return
            Client._argsToBytes(
            Client.EVMExtraArgsV1({gasLimit: gasLimit, strict: strict})
        );
    }

    function getCCIPFees(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo,
        CCIPData calldata ccipData
    ) public view returns (uint256 fees) {
        Storage storage s = getStorage();

        bytes memory payload = encodeCCIPPayload(soDataNo, swapDataDstNo);
        Client.EVMTokenAmount memory bridgeTokenAmount = Client.EVMTokenAmount({
            token: ccipData.bridgeToken,
            amount: 0
        });

        Client.EVMTokenAmount[]
        memory tokenAmounts = new Client.EVMTokenAmount[](1);
        tokenAmounts[0] = bridgeTokenAmount;

        Client.EVM2AnyMessage memory message = Client.EVM2AnyMessage({
            receiver: abi.encode(ccipData.dstDiamond), // ABI-encoded receiver contract address
            data: payload,
            tokenAmounts: tokenAmounts,
            extraArgs: ccipData.extraArgs,
            feeToken: ccipData.payFeesIn // Setting feeToken to zero address, indicating native asset will be used for fees
        });

        // Get the fee required to send the message
        fees = IRouterClient(s.router).getFee(
            ccipData.dstChainSelector,
            message
        );
    }

    /// @dev Get so fee
    function getCCIPSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.router];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(soFee).getFees(amount);
        }
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
    function encodeCCIPPayload(
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst
    ) public pure returns (bytes memory) {
        bytes memory encodeData = abi.encodePacked(
            uint8(soData.transactionId.length),
            soData.transactionId,
            uint8(soData.receiver.length),
            soData.receiver,
            uint8(soData.receivingAssetId.length),
            soData.receivingAssetId
        );

        if (swapDataDst.length > 0) {
            bytes memory swapLenBytes = LibCross.serializeU256WithHexStr(
                swapDataDst.length
            );
            encodeData = encodeData.concat(
                abi.encodePacked(uint8(swapLenBytes.length), swapLenBytes)
            );
        }

        for (uint256 i = 0; i < swapDataDst.length; i++) {
            encodeData = encodeData.concat(
                abi.encodePacked(
                    uint8(swapDataDst[i].callTo.length),
                    swapDataDst[i].callTo,
                    uint8(swapDataDst[i].sendingAssetId.length),
                    swapDataDst[i].sendingAssetId,
                    uint8(swapDataDst[i].receivingAssetId.length),
                    swapDataDst[i].receivingAssetId,
                    uint16(swapDataDst[i].callData.length),
                    swapDataDst[i].callData
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
    function decodeCCIPPayload(bytes memory ccipPayload)
    public
    pure
    returns (
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst
    )
    {
        CachePayload memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(ccipPayload.toUint8(index));
        index += 1;
        data.soData.transactionId = ccipPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(ccipPayload.toUint8(index));
        index += 1;
        data.soData.receiver = ccipPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(ccipPayload.toUint8(index));
        index += 1;
        data.soData.receivingAssetId = ccipPayload.slice(index, nextLen);
        index += nextLen;

        if (index < ccipPayload.length) {
            nextLen = uint256(ccipPayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                ccipPayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDst = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(ccipPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].callTo = ccipPayload.slice(index, nextLen);
                data.swapDataDst[i].approveTo = data.swapDataDst[i].callTo;
                index += nextLen;

                nextLen = uint256(ccipPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].sendingAssetId = ccipPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(ccipPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].receivingAssetId = ccipPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(ccipPayload.toUint16(index));
                index += 2;
                data.swapDataDst[i].callData = ccipPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        require(index == ccipPayload.length, "LenErr");
        return (data.soData, data.swapDataDst);
    }

    /// Private Methods ///

    function _startBridge(
        CCIPData memory ccipData,
        Client.EVMTokenAmount[] memory tokenAmounts,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();

        // note: not consider the case of multiple tokenAmounts
        address bridgeToken = tokenAmounts[0].token;
        uint256 bridgeAmount = tokenAmounts[0].amount;
        Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
            receiver: abi.encode(ccipData.dstDiamond),
            data: payload,
            tokenAmounts: tokenAmounts,
            extraArgs: ccipData.extraArgs,
            feeToken: ccipData.payFeesIn
        });

        // Initialize a router client instance to interact with cross-chain router
        IRouterClient router = IRouterClient(s.router);

        uint256 fees = router.getFee(ccipData.dstChainSelector, evm2AnyMessage);

        if (ccipData.bridgeToken != address(0)) {
            LibAsset.maxApproveERC20(
                IERC20(ccipData.bridgeToken),
                s.router,
                bridgeAmount
            );
        }

        if (ccipData.payFeesIn == address(0)) {
            // Send the message through the router and store the returned message ID
            bytes32 messageId = router.ccipSend{value: fees}(
                ccipData.dstChainSelector,
                evm2AnyMessage
            );

            emit CCIPMessageSent(
                messageId,
                ccipData.dstChainSelector,
                ccipData.dstDiamond,
                msg.sender,
                tokenAmounts[0],
                fees
            );
        } else {
            revert("InvalidFeeToken");
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
