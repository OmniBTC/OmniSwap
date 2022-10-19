// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Interfaces/ISo.sol";
import "../Libraries/LibAsset.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Errors/GenericErrors.sol";
import "../Helpers/Swapper.sol";
import "../Libraries/LibCross.sol";

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
        if (!LibAsset.isNativeAsset(swapData[0].sendingAssetId)) {
            LibAsset.depositAsset(
                swapData[0].sendingAssetId,
                swapData[0].fromAmount
            );
        }
        uint256 postSwapBalance = this.executeAndCheckSwaps(soData, swapData);
        address receivingAssetId = swapData[swapData.length - 1]
            .receivingAssetId;
        withdraw(
            receivingAssetId,
            soData.receivingAssetId,
            postSwapBalance,
            soData.receiver
        );

        emit SoSwappedGeneric(
            soData.transactionId,
            soData.sendingAssetId,
            soData.receivingAssetId,
            swapData[0].fromAmount,
            postSwapBalance
        );
    }
}
