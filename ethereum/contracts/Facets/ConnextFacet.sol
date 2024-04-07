// SPDX-License-Identifier: GPLv3
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

import "../Libraries/LibAsset.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibSwap.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibDiamond.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ICorrectSwap.sol";
import "../Interfaces/IConnext.sol";
import "../Interfaces/IStableSwap.sol";
import "../Interfaces/IXReceiver.sol";
import "../Interfaces/ILibSoFeeV2.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Errors/GenericErrors.sol";

/// @title Connext Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through Connext
contract ConnextFacet is Swapper, ReentrancyGuard, IXReceiver {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"bfb250ec550de32792eb54eef527e3bc2a5be2220e94da89b2f781a2e93fca97"; //keccak256("com.so.facets.connext");

    struct Storage {
        // The Connext contract on this domain
        address connext;
    }

    /// Types ///

    struct ConnextData {
        // Destination domain
        uint32 dstDomain;
        // Destination SoDiamond address
        address payable dstSoDiamond;
        // Bridge token
        address bridgeToken;
        // Max slippage the user will accept in BPS (e.g. 300 = 3%)
        uint256 slippage;
        // Whether the relayer fee is paid with native gas token
        bool isNativeRelayerFee;
        // Relayer fee
        uint256 relayFee;
        // Receive local
        bool receiveLocal;
    }

    struct CachePayload {
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    /// Events ///
    event ConnextInitialized(address connext);

    /// Init ///

    /// @notice Initializes local variables for the Connext facet
    function initConnext(address _connext) external {
        LibDiamond.enforceIsContractOwner();
        if (_connext == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.connext = _connext;
        emit ConnextInitialized(_connext);
    }

    /// External Methods ///

    /// @notice Bridge token via Connext
    /// @param soDataNo Data for tracking cross-chain transactions and a
    ///                portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    ///                     transactions on the source chain side
    /// @param connextData Data used to call connext xcall for swap
    /// @param swapDataDstNo Contains a set of Swap transaction data executed
    ///                     on the target chain.
    function soSwapViaConnext(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        ConnextData calldata connextData,
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
            transferWrappedAsset(
                soData.sendingAssetId,
                connextData.bridgeToken,
                soData.amount
            );
            bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            transferWrappedAsset(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                connextData.bridgeToken,
                bridgeAmount
            );
        }
        bytes memory payload = encodeConnextPayload(soDataNo, swapDataDstNo);

        uint256 soBasicFee = getConnextBasicFee();
        address soBasicBeneficiary = getConnextBasicBeneficiary();
        if (soBasicBeneficiary == address(0x0)) {
            soBasicFee = 0;
        }

        _checkRelayFee(soData, connextData, bridgeAmount, soBasicFee);

        if (soBasicFee > 0) {
            LibAsset.transferAsset(
                address(0x0),
                payable(soBasicBeneficiary),
                soBasicFee
            );
        }

        _startBridge(connextData, bridgeAmount, payload);

        emit SoTransferStarted(soData.transactionId);
    }

    function xReceive(
        bytes32 _transferId,
        uint256 _amount,
        address _asset,
        address _originSender,
        uint32 _origin,
        bytes memory _callData
    ) external returns (bytes memory) {
        (
            ISo.NormalizedSoData memory soDataNo,
            LibSwap.NormalizedSwapData[] memory swapDataDstNo
        ) = decodeConnextPayload(_callData);

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );

        try
            this.remoteConnextSwap(_asset, _amount, soData, swapDataDst)
        {} catch Error(string memory revertReason) {
            transferUnwrappedAsset(_asset, _asset, _amount, soData.receiver);
            emit SoTransferFailed(
                soData.transactionId,
                revertReason,
                bytes("")
            );
        } catch (bytes memory returnData) {
            transferUnwrappedAsset(_asset, _asset, _amount, soData.receiver);
            emit SoTransferFailed(soData.transactionId, "", returnData);
        }
        return "";
    }

    function xReceiveForGas(
        ISo.NormalizedSoData calldata soDataNo,
        address token,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external {
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            swapDataDstNo
        );
        uint256 amount = LibAsset.getOwnBalance(token);
        this.remoteConnextSwap(token, amount, soData, swapDataDst);
    }

    /// @dev Call connext bumpTransfer
    function bumpTransfer(bytes32 _connextTransferId) external payable {
        Storage storage s = getStorage();
        IConnext(s.connext).bumpTransfer{value: msg.value}(_connextTransferId);
    }

    // @dev Call connext forceUpdateSlippage
    function forceUpdateSlippage(
        IConnext.TransferInfo calldata _params,
        uint256 _slippage
    ) external {
        Storage storage s = getStorage();
        IConnext(s.connext).forceUpdateSlippage(_params, _slippage);
    }

    /// @dev Get so fee
    function getConnextSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.connext];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getFees(amount);
        }
    }

    /// Help to get swap result
    function calculateConnextSwap(
        bytes32 key,
        address tokenAddressFrom,
        address tokenAddressTo,
        uint256 amount
    ) external view returns (uint256) {
        Storage storage s = getStorage();
        uint8 tokenIndexFrom = IStableSwap(s.connext).getTokenIndex(
            key,
            tokenAddressFrom
        );
        uint8 tokenIndexTo = IStableSwap(s.connext).getTokenIndex(
            key,
            tokenAddressTo
        );
        return
            IStableSwap(s.connext).calculateSwap(
                key,
                tokenIndexFrom,
                tokenIndexTo,
                amount
            );
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
    function encodeConnextPayload(
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
    function decodeConnextPayload(
        bytes memory stargatePayload
    )
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

    /// @dev swap on destination chain
    function remoteConnextSwap(
        address token,
        uint256 amount,
        ISo.SoData memory soData,
        LibSwap.SwapData[] memory swapDataDst
    ) external {
        require(msg.sender == address(this), "NotDiamond");
        uint256 soFee = getConnextSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
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

            uint256 amountFinal = this.executeAndCheckSwaps(
                soData,
                swapDataDst
            );
            transferUnwrappedAsset(
                swapDataDst[swapDataDst.length - 1].receivingAssetId,
                soData.receivingAssetId,
                amountFinal,
                soData.receiver
            );
            emit SoTransferCompleted(soData.transactionId, amountFinal);
        }
    }

    /// Private Methods ///

    /// @dev Calculate the fee for paying the relay
    function _checkRelayFee(
        SoData memory soData,
        ConnextData calldata connextData,
        uint256 bridgeAmount,
        uint256 soBasicFee
    ) private view {
        if (connextData.isNativeRelayerFee) {
            if (LibAsset.isNativeAsset(soData.sendingAssetId)) {
                require(
                    msg.value ==
                        soData.amount.add(connextData.relayFee).add(soBasicFee),
                    "CheckNativeFail"
                );
            } else {
                require(
                    msg.value == connextData.relayFee.add(soBasicFee),
                    "CheckNativeFail"
                );
            }
        } else {
            if (LibAsset.isNativeAsset(soData.sendingAssetId)) {
                require(
                    msg.value == soData.amount.add(soBasicFee),
                    "CheckFail"
                );
            } else {
                require(msg.value == soBasicFee, "CheckFail");
            }
            require(bridgeAmount > connextData.relayFee, "CheckNotEnough");
        }
    }

    /// @dev Contains the business logic for the bridge via Connext
    function _startBridge(
        ConnextData calldata connextData,
        uint256 bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();
        address bridge = s.connext;

        // Give Connext approval to bridge tokens
        LibAsset.safeApproveERC20(
            IERC20(connextData.bridgeToken),
            bridge,
            bridgeAmount
        );

        if (connextData.isNativeRelayerFee) {
            if (connextData.receiveLocal) {
                IConnext(bridge).xcallIntoLocal{value: connextData.relayFee}(
                    connextData.dstDomain,
                    connextData.dstSoDiamond,
                    connextData.bridgeToken,
                    msg.sender,
                    bridgeAmount,
                    connextData.slippage,
                    payload
                );
            } else {
                IConnext(bridge).xcall{value: connextData.relayFee}(
                    connextData.dstDomain,
                    connextData.dstSoDiamond,
                    connextData.bridgeToken,
                    msg.sender,
                    bridgeAmount,
                    connextData.slippage,
                    payload
                );
            }
        } else {
            if (connextData.receiveLocal) {
                IConnext(bridge).xcallIntoLocal(
                    connextData.dstDomain,
                    connextData.dstSoDiamond,
                    connextData.bridgeToken,
                    msg.sender,
                    bridgeAmount.sub(connextData.relayFee),
                    connextData.slippage,
                    payload,
                    connextData.relayFee
                );
            } else {
                IConnext(bridge).xcall(
                    connextData.dstDomain,
                    connextData.dstSoDiamond,
                    connextData.bridgeToken,
                    msg.sender,
                    bridgeAmount.sub(connextData.relayFee),
                    connextData.slippage,
                    payload,
                    connextData.relayFee
                );
            }
        }
    }

    /// @dev Get basic beneficiary
    function getConnextBasicBeneficiary() public view returns (address) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.connext];
        if (soFee == address(0x0)) {
            return address(0x0);
        } else {
            return ILibSoFeeV2(soFee).getBasicBeneficiary();
        }
    }

    /// @dev Get basic fee
    function getConnextBasicFee() public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.connext];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getBasicFee();
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
