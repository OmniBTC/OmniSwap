// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import { ISo } from "../Interfaces/ISo.sol";
import { LibAsset, IERC20 } from "../Libraries/LibAsset.sol";
import { ReentrancyGuard } from "../Helpers/ReentrancyGuard.sol";
import { ZeroPostSwapBalance, NoSwapDataProvided } from "../Errors/GenericErrors.sol";
import { Swapper, LibSwap } from "../Helpers/Swapper.sol";

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
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapData an array of swap related data for performing swaps before bridging
    function swapTokensGeneric(SoData calldata _soData, LibSwap.SwapData[] calldata _swapData)
        external
        payable
        nonReentrant
    {
        if (_swapData.length == 0) revert NoSwapDataProvided();
        if (!LibAsset.isNativeAsset(_swapData[0].sendingAssetId)){
            LibAsset.depositAsset(_swapData[0].sendingAssetId, _swapData[0].fromAmount);
        }
        uint256 postSwapBalance = this.executeAndCheckSwaps(_soData, _swapData);
        address receivingAssetId = _swapData[_swapData.length - 1].receivingAssetId;
        withdraw(receivingAssetId, _soData.receivingAssetId, postSwapBalance, _soData.receiver);

        emit SoSwappedGeneric(
            _soData.transactionId,
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            _swapData[0].fromAmount,
            postSwapBalance
        );
    }
}
