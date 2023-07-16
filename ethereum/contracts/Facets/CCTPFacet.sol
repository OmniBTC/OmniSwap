// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibAsset.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/TypedMemView.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Interfaces/ITokenMessenger.sol";
import "../Interfaces/IReceiver.sol";
import "../Interfaces/ILibPrice.sol";
import "../Interfaces/IMessageHandler.sol";
import "../Interfaces/IMessageTransmitter.sol";

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
            transferWrappedAsset(
                soData.sendingAssetId,
                cctpData.burnToken,
                soData.amount
            );
            bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            transferWrappedAsset(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                cctpData.burnToken,
                bridgeAmount
            );
        }

        uint256 soFee = getCCTPSoFee(bridgeAmount);
        if (soFee < bridgeAmount) {
            bridgeAmount = bridgeAmount.sub(soFee);
        }

        if (soFee > 0) {
            transferUnwrappedAsset(
                cctpData.burnToken,
                cctpData.burnToken,
                soFee,
                LibDiamond.contractOwner()
            );
        }

        bytes memory payload = encodeCCTPPayload(soDataNo, swapDataDstNo);

        _startBridge(cctpData, bridgeAmount, payload);

        emit SoTransferStarted(soData.transactionId);
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
    function encodeCCTPPayload(
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
    function decodeCCTPPayload(bytes memory stargatePayload)
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

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.transactionId = stargatePayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.receiver = stargatePayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.receivingAssetId = stargatePayload.slice(index, nextLen);
        index += nextLen;

        if (index < stargatePayload.length) {
            nextLen = uint256(stargatePayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                stargatePayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDst = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].callTo = stargatePayload.slice(
                    index,
                    nextLen
                );
                data.swapDataDst[i].approveTo = data.swapDataDst[i].callTo;
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].sendingAssetId = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].receivingAssetId = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint16(index));
                index += 2;
                data.swapDataDst[i].callData = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        require(index == stargatePayload.length, "LenErr");
        return (data.soData, data.swapDataDst);
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

        uint256 amount;
        if (swapDataDst.length == 0) {
            amount = LibAsset.getOwnBalance(soData.receivingAssetId);
            LibAsset.transferAsset(
                soData.receivingAssetId,
                soData.receiver,
                amount
            );
            emit SoTransferCompleted(soData.transactionId, amount);
        } else {
            amount = LibAsset.getOwnBalance(swapDataDst[0].sendingAssetId);
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
        uint64 tokenNonce = _nonce(tokenMsg);
        bytes29 _msg = TypedMemView.ref(message, 0);
        uint64 nonce = _nonce(_msg);
        require(tokenNonce + 1 == nonce, "nonce mismatch");

        IReceiver(s.messageTransmitter).receiveMessage(
            tokenMessage,
            tokenAttestation
        );
        IReceiver(s.messageTransmitter).receiveMessage(message, attestation);
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

    // @notice Returns _message's nonce field
    function _nonce(bytes29 _message) internal pure returns (uint64) {
        return uint64(_message.indexUint(12, 8));
    }

    function _startBridge(
        CCTPData calldata cctpData,
        uint256 amount,
        bytes memory payload
    ) internal {
        Storage storage s = getStorage();
        // Give TokenMessenger approval to bridge tokens
        LibAsset.maxApproveERC20(
            IERC20(cctpData.burnToken),
            s.tokenMessenger,
            amount
        );

        ITokenMessenger(s.tokenMessenger).depositForBurn(
            amount,
            cctpData.destinationDomain,
            cctpData.dstDiamond,
            cctpData.burnToken
        );

        IMessageTransmitter(s.messageTransmitter).sendMessage(
            cctpData.destinationDomain,
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
