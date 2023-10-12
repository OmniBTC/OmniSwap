// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibAsset.sol";
import "../Libraries/LibMessageCCTP.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/TypedMemView.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Interfaces/CCTP/ITokenMessenger.sol";
import "../Interfaces/CCTP/IReceiver.sol";
import "../Interfaces/ILibPrice.sol";
import "../Interfaces/CCTP/IMessageHandler.sol";
import "../Interfaces/CCTP/IMessageTransmitter.sol";

/// @title CCTP Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through CCTP
contract CCTPFacet is Swapper, ReentrancyGuard, IMessageHandler {
    using SafeMath for uint256;
    using LibBytes for bytes;
    using TypedMemView for bytes29;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"ed7099a4d8ec3979659a0931894724cfba9c270625d87b539a3d3a9e869c389e"; // keccak256("com.so.facets.cctp")

    uint256 public constant RAY = 1e27;

    struct Storage {
        address tokenMessenger;
        address messageTransmitter;
        mapping(uint32 => uint256) dstBaseGas;
        mapping(uint32 => uint256) dstGasPerBytes;
    }

    /// Events ///
    event InitCCTP(address tokenMessenger, address messageTransmitter);
    event RelayEvent(bytes32 transactionId, uint256 fee);

    /// Types ///

    struct CCTPData {
        // Chain ID defined by CCTP
        uint32 destinationDomain;
        // Destination chain's diamond
        bytes32 dstDiamond;
        // CCTP supports tokens across chains
        address burnToken;
    }

    struct CachePayload {
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    /// Init Methods ///

    /// @dev Set CCTP's token bridge address and message transmitter address
    /// @param _tokenMessenger cctp token bridge
    /// @param _messageTransmitter cctp message protocol
    function initCCTP(address _tokenMessenger, address _messageTransmitter)
        external
    {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.tokenMessenger = _tokenMessenger;
        s.messageTransmitter = _messageTransmitter;
        emit InitCCTP(_tokenMessenger, _messageTransmitter);
    }

    /// External Methods ///

    /// @dev Set the minimum gas to be spent on the destination chain
    /// @param destinationDomains  a batch of destination domain id
    /// @param dstBaseGas  base gas for destination chain
    function setCCTPBaseGas(
        uint32[] calldata destinationDomains,
        uint256 dstBaseGas
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        for (uint64 i; i < destinationDomains.length; i++) {
            s.dstBaseGas[destinationDomains[i]] = dstBaseGas;
        }
    }

    /// @dev Set the minimum gas to be spent on the destination chain
    /// @param destinationDomains  a batch of destination domain id
    /// @param dstGasPerBytes gas per bytes for destination chain
    function setCCTPGasPerBytes(
        uint32[] calldata destinationDomains,
        uint256 dstGasPerBytes
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        for (uint64 i; i < destinationDomains.length; i++) {
            s.dstGasPerBytes[destinationDomains[i]] = dstGasPerBytes;
        }
    }

    /// @dev Bridge tokens via CCTP
    /// @param soDataNo data for tracking cross-chain transactions and a
    ///                 portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param cctpData data used to call CCTP's TokenMessenger for cross usdc
    function soSwapViaCCTP(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        CCTPData calldata cctpData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable {
        uint256 bridgeAmount;

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }

        // calculate relay fee
        uint256 relay_fee = 0;
        if (LibAsset.isNativeAsset(soData.sendingAssetId)) {
            require(msg.value > soData.amount, "ValueErr");
            relay_fee = msg.value - soData.amount;
        } else {
            relay_fee = msg.value;
        }

        if (relay_fee > 0) {
            LibAsset.transferAsset(
                LibAsset.NATIVE_ASSETID,
                payable(LibDiamond.contractOwner()),
                relay_fee
            );
            emit RelayEvent(soData.transactionId, relay_fee);
        }

        if (swapDataSrc.length == 0) {
            require(soData.sendingAssetId == cctpData.burnToken, "TokenErr");
            bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            require(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId ==
                    cctpData.burnToken,
                "TokenErr"
            );
        }

        bytes memory payload = encodeCCTPPayloadWithAmount(
            soDataNo,
            swapDataDstNo,
            bridgeAmount
        );

        require(bridgeAmount > 0, "bridgeAmount>0");
        _startBridge(cctpData, bridgeAmount, payload);

        emit SoTransferStarted(soData.transactionId);
    }

    /// CrossData
    // 1. length + amount(SoData)
    // 2. length + transactionId(SoData)
    // 3. length + receiver(SoData)
    // 4. length + receivingAssetId(SoData)
    // 5. length + swapDataLength(u8)
    // 6. length + callTo(SwapData)
    // 7. length + sendingAssetId(SwapData)
    // 8. length + receivingAssetId(SwapData)
    // 9. length + callData(SwapData)
    function encodeCCTPPayloadWithAmount(
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst,
        uint256 bridgeAmount
    ) public pure returns (bytes memory) {
        bytes memory bridgeAmountByte = LibCross.serializeU256WithHexStr(
            bridgeAmount
        );

        bytes memory encodeData = abi.encodePacked(
            uint8(bridgeAmountByte.length),
            bridgeAmountByte,
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
    // 1. length + amount(SoData)
    // 2. length + transactionId(SoData)
    // 3. length + receiver(SoData)
    // 4. length + receivingAssetId(SoData)
    // 5. length + swapDataLength(u8)
    // 6. length + callTo(SwapData)
    // 7. length + sendingAssetId(SwapData)
    // 8. length + receivingAssetId(SwapData)
    // 9. length + callData(SwapData)
    function decodeCCTPPayload(bytes memory cctpPayload)
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

        nextLen = uint256(cctpPayload.toUint8(index));
        index += 1;
        data.soData.amount = LibCross.deserializeU256WithHexStr(
            cctpPayload.slice(index, nextLen)
        );
        index += nextLen;

        nextLen = uint256(cctpPayload.toUint8(index));
        index += 1;
        data.soData.transactionId = cctpPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(cctpPayload.toUint8(index));
        index += 1;
        data.soData.receiver = cctpPayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(cctpPayload.toUint8(index));
        index += 1;
        data.soData.receivingAssetId = cctpPayload.slice(index, nextLen);
        index += nextLen;

        if (index < cctpPayload.length) {
            nextLen = uint256(cctpPayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                cctpPayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDst = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(cctpPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].callTo = cctpPayload.slice(index, nextLen);
                data.swapDataDst[i].approveTo = data.swapDataDst[i].callTo;
                index += nextLen;

                nextLen = uint256(cctpPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].sendingAssetId = cctpPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(cctpPayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].receivingAssetId = cctpPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(cctpPayload.toUint16(index));
                index += 2;
                data.swapDataDst[i].callData = cctpPayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        require(index == cctpPayload.length, "LenErr");
        return (data.soData, data.swapDataDst);
    }

    function decodeCCTPMessage(bytes memory message)
        public
        view
        returns (LibMessageCCTP.CCTPMessage memory)
    {
        LibMessageCCTP.CCTPMessage memory data;
        bytes29 _msg = TypedMemView.ref(message, 0);
        data._msgVersion = LibMessageCCTP._version(_msg);
        data._msgSourceDomain = LibMessageCCTP._sourceDomain(_msg);
        data._msgDestinationDomain = LibMessageCCTP._destinationDomain(_msg);
        data._msgNonce = LibMessageCCTP._nonce(_msg);
        data._msgSender = LibMessageCCTP._sender(_msg);
        data._msgRecipient = LibMessageCCTP._recipient(_msg);
        data._msgDestinationCaller = LibMessageCCTP._destinationCaller(_msg);
        data._msgRawBody = LibMessageCCTP._messageBody(_msg).clone();
        return data;
    }

    function handleReceiveMessage(
        uint32,
        bytes32,
        bytes calldata messageBody
    ) external override returns (bool) {
        Storage storage s = getStorage();
        require(
            msg.sender == s.messageTransmitter,
            "Only message transmitter can call"
        );

        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeCCTPPayload(messageBody);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        // cross-chain loss not exist in burn-mint mode
        uint256 amount = soData.amount;

        uint256 soFee = getCCTPSoFee(amount);
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

        return true;
    }

    function receiveCCTPMessage(
        bytes calldata tokenMessage,
        bytes calldata tokenAttestation,
        bytes calldata message,
        bytes calldata attestation
    ) external {
        Storage storage s = getStorage();

        // check token and msg nonce
        bytes29 tokenMsg = TypedMemView.ref(tokenMessage, 0);
        uint64 tokenNonce = LibMessageCCTP._nonce(tokenMsg);
        bytes29 _msg = TypedMemView.ref(message, 0);
        uint64 nonce = LibMessageCCTP._nonce(_msg);
        require(tokenNonce + 1 == nonce, "nonce mismatch");

        IReceiver(s.messageTransmitter).receiveMessage(
            tokenMessage,
            tokenAttestation
        );
        IReceiver(s.messageTransmitter).receiveMessage(message, attestation);
    }

    function receiveCCTPMessageByOwner(
        bytes calldata tokenMessage,
        bytes calldata tokenAttestation
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        IReceiver(s.messageTransmitter).receiveMessage(
            tokenMessage,
            tokenAttestation
        );
    }

    /// @dev estimate dst swap gas
    function estimateReceiveCCTPMessageGas(
        ISo.NormalizedSoData calldata soDataNo,
        CCTPData calldata cctpData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) public view returns (uint256) {
        bytes memory payload = encodeCCTPPayloadWithAmount(
            soDataNo,
            swapDataDstNo,
            uint256(0)
        );
        Storage storage s = getStorage();
        return
            s.dstBaseGas[cctpData.destinationDomain].add(
                s.dstGasPerBytes[cctpData.destinationDomain].mul(payload.length)
            );
    }

    /// @dev Get so fee
    function getCCTPSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.tokenMessenger];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(soFee).getFees(amount);
        }
    }

    /// Internal Methods ///
    function _startBridge(
        CCTPData calldata cctpData,
        uint256 bridgeAmount,
        bytes memory payload
    ) internal {
        Storage storage s = getStorage();
        // Give TokenMessenger approval to bridge tokens
        LibAsset.maxApproveERC20(
            IERC20(cctpData.burnToken),
            s.tokenMessenger,
            bridgeAmount
        );

        ITokenMessenger(s.tokenMessenger).depositForBurnWithCaller(
            bridgeAmount,
            cctpData.destinationDomain,
            cctpData.dstDiamond,
            cctpData.burnToken,
            cctpData.dstDiamond
        );

        IMessageTransmitter(s.messageTransmitter).sendMessageWithCaller(
            cctpData.destinationDomain,
            cctpData.dstDiamond,
            cctpData.dstDiamond,
            payload
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
