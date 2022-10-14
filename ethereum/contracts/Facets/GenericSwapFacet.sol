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
    /// @param _soDataNo data used purely for tracking and analytics
    /// @param _swapDataNo an array of swap related data for performing swaps before bridging
    function swapTokensGeneric(
        ISo.NormalizedSoData calldata _soDataNo,
        LibSwap.NormalizedSwapData[] calldata _swapDataNo
    ) external payable nonReentrant {
        ISo.SoData memory _soData = LibCross.denormalizeSoData(_soDataNo);
        LibSwap.SwapData[] memory _swapData = LibCross.denormalizeSwapData(
            _swapDataNo
        );

        if (_swapData.length == 0) revert NoSwapDataProvided();
        if (!LibAsset.isNativeAsset(_swapData[0].sendingAssetId)) {
            LibAsset.depositAsset(
                _swapData[0].sendingAssetId,
                _swapData[0].fromAmount
            );
        }
        uint256 postSwapBalance = this.executeAndCheckSwaps(_soData, _swapData);
        address receivingAssetId = _swapData[_swapData.length - 1]
            .receivingAssetId;
        withdraw(
            receivingAssetId,
            _soData.receivingAssetId,
            postSwapBalance,
            _soData.receiver
        );

        emit SoSwappedGeneric(
            _soData.transactionId,
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            _swapData[0].fromAmount,
            postSwapBalance
        );
    }
}
