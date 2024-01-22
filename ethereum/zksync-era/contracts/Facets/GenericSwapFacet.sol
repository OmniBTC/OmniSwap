// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Interfaces/ISo.sol";
import "../Libraries/LibAsset.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Errors/GenericErrors.sol";
import "../Helpers/Swapper.sol";
import "../Libraries/LibCross.sol";
import "../Interfaces/ILibSoFeeV2.sol";

/// @title Generic Swap Facet
/// @notice Provides functionality for swapping through ANY APPROVED DEX
/// @dev Uses calldata to execute APPROVED arbitrary methods on DEXs
contract GenericSwapFacet is ISo, Swapper, ReentrancyGuard {
    /// Events ///

    event SoSwappedGeneric(
        bytes32 indexed transactionId,
        address fromAssetId,
        address toAssetId,
        uint256 fromAmount,
        uint256 toAmount
    );

    /// External Methods ///

    /// @notice Performs multiple swaps in one transaction
    /// @param soDataNo data used purely for tracking and analytics
    /// @param swapDataNo an array of swap related data for performing swaps before bridging
    function swapTokensGeneric(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataNo
    ) external payable nonReentrant {
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapData = LibCross.denormalizeSwapData(
            swapDataNo
        );

        if (swapData.length == 0) revert NoSwapDataProvided();
        uint256 fromAmount = _getSwapAmount(swapData);

        if (!LibAsset.isNativeAsset(swapData[0].sendingAssetId)) {
            LibAsset.depositAsset(swapData[0].sendingAssetId, fromAmount);
        } else {
            require(msg.value >= fromAmount, "NotEnoughValue");
        }
        uint256 postSwapBalance = this.executeAndCheckSwapsV2(soData, swapData);
        address receivingAssetId = swapData[swapData.length - 1]
            .receivingAssetId;

        uint256 soFee = getGenericSoFee(postSwapBalance);
        address soBasicBeneficiary = getGenericBasicBeneficiary();
        if (soBasicBeneficiary != address(0x0) && soFee > 0) {
            transferUnwrappedAsset(
                receivingAssetId,
                soData.receivingAssetId,
                soFee,
                soBasicBeneficiary
            );
            postSwapBalance -= soFee;
        }

        transferUnwrappedAsset(
            receivingAssetId,
            soData.receivingAssetId,
            postSwapBalance,
            soData.receiver
        );

        emit SoSwappedGeneric(
            soData.transactionId,
            soData.sendingAssetId,
            soData.receivingAssetId,
            fromAmount,
            postSwapBalance
        );
    }

    /// @dev Get so fee
    function getGenericSoFee(uint256 amount) public view returns (uint256) {
        address soFee = appStorage.gatewaySoFeeSelectors[address(0x0)];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getFees(amount);
        }
    }

    /// @dev Get basic beneficiary
    function getGenericBasicBeneficiary() public view returns (address) {
        address soFee = appStorage.gatewaySoFeeSelectors[address(0x0)];
        if (soFee == address(0x0)) {
            return address(0x0);
        } else {
            return ILibSoFeeV2(soFee).getBasicBeneficiary();
        }
    }

    /// @dev Get basic fee
    function getGenericBasicFee() public view returns (uint256) {
        address soFee = appStorage.gatewaySoFeeSelectors[address(0x0)];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getBasicFee();
        }
    }
}
