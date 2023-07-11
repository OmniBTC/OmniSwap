// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Libraries/LibDiamond.sol";
import "../Libraries/LibBytes.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibAsset.sol";
import "../Interfaces/ISo.sol";
import "../Helpers/Swapper.sol";
import "../Interfaces/ILibSoFee.sol";
import "../Interfaces/ITokenMessenger.sol";
import "../Interfaces/IReceiver.sol";

/// @title CCTP Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through CCTP
contract CCTPFacet is Swapper {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
    hex"ed7099a4d8ec3979659a0931894724cfba9c270625d87b539a3d3a9e869c389e"; // keccak256("com.so.facets.cctp")

    uint256 public constant RAY = 1e27;

    struct Storage {
        address tokenMessenger;
        address messageTransmitter;
    }

    /// Events ///

    /// Types ///

    struct CCTPData {
        uint32 destinationDomain;
        address burnToken;
        bytes32 mintRecipient;
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
        CCTPData calldata cctpData
    ) external payable {
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

        _startBridge(cctpData, bridgeAmount);

        emit SoTransferStarted(soData.transactionId);
    }

    function receiveCCTPMessage(bytes calldata message, bytes calldata attestation) external {
        Storage storage s = getStorage();
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

    function _startBridge(
        CCTPData calldata cctpData,
        uint256 amount
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
            cctpData.mintRecipient,
            cctpData.burnToken
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
