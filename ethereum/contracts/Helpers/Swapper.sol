// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import {IWETH} from "../Interfaces/IWETH.sol";
import {ISo} from "../Interfaces/ISo.sol";
import {ICorrectSwap} from "../Interfaces/ICorrectSwap.sol";
import {LibSwap} from "../Libraries/LibSwap.sol";
import {LibAsset} from "../Libraries/LibAsset.sol";
import {LibUtil} from "../Libraries/LibUtil.sol";
import {LibStorage} from "../Libraries/LibStorage.sol";
import {LibAsset} from "../Libraries/LibAsset.sol";
import {InvalidAmount, ContractCallNotAllowed, NoSwapDataProvided, NotSupportedSwapRouter} from "../Errors/GenericErrors.sol";

/// @title Swapper
/// @notice Abstract contract to provide swap functionality
contract Swapper is ISo {
    /// Storage ///

    LibStorage internal appStorage;

    struct CacheSwapInnerParam {
        LibSwap.SwapData currentSwapData;
        uint256 fromAmount;
        uint256 minAmount;
        uint256 swapBalance;
        address receivedToken;
    }

    struct CacheSwapParam {
        address correctSwap;
        uint256[] sliceIndex;
        uint256 deltaFromAmount;
        uint256 deltaMinAmount;
        uint256 startIndex;
        uint256 endIndex;
        bool flag;
        uint256 fromAmount;
        uint256 minAmount;
    }

    /// External Methods ///

    /// @dev Validates input before executing swaps
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function executeAndCheckSwaps(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) external returns (uint256) {
        require(msg.sender == address(this), "NotDiamond");
        uint256 nSwaps = swapData.length;
        if (nSwaps == 0) revert NoSwapDataProvided();
        address finalTokenId = swapData[swapData.length - 1].receivingAssetId;
        uint256 swapBalance = LibAsset.getOwnBalance(finalTokenId);
        _executeSwaps(soData, swapData);
        swapBalance = LibAsset.getOwnBalance(finalTokenId) - swapBalance;
        if (swapBalance == 0) revert InvalidAmount();
        return swapBalance;
    }

    /// @dev Validates input before executing swaps. Support dynamic slice swap
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function executeAndCheckSwapsV2(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) external returns (uint256) {
        require(msg.sender == address(this), "NotDiamond");
        uint256 nSwaps = swapData.length;
        if (nSwaps == 0) revert NoSwapDataProvided();
        address finalTokenId = swapData[swapData.length - 1].receivingAssetId;
        uint256 swapBalance = LibAsset.getOwnBalance(finalTokenId);
        _executeSwapsV2(soData, swapData);
        swapBalance = LibAsset.getOwnBalance(finalTokenId) - swapBalance;
        if (swapBalance == 0) revert InvalidAmount();
        return swapBalance;
    }

    function libSwap(
        bytes32 transactionId,
        LibSwap.SwapData memory _swapData
    ) external {
        require(msg.sender == address(this), "NotDiamond");
        LibSwap.swap(transactionId, _swapData);
    }

    /// Internal Methods ///

    /// @dev Convert eth to wrapped eth and Transfer.
    function transferWrappedAsset(
        address currentAssetId,
        address expectAssetId,
        uint256 amount
    ) internal {
        if (currentAssetId == expectAssetId) {
            require(
                LibAsset.getOwnBalance(currentAssetId) >= amount,
                "NotEnough"
            );
            return;
        }

        if (LibAsset.isNativeAsset(currentAssetId)) {
            // eth -> weth
            try IWETH(expectAssetId).deposit{value: amount}() {} catch {
                revert("DepositErr");
            }
        } else if (LibAsset.isNativeAsset(expectAssetId)) {
            // weth -> eth
            try IWETH(currentAssetId).withdraw(amount) {} catch {
                revert("WithdrawErr");
            }
        } else {
            // weth -> eth -> weth
            if (currentAssetId != expectAssetId) {
                try IWETH(currentAssetId).withdraw(amount) {} catch {
                    revert("WithdrawDepositErr");
                }
                try IWETH(expectAssetId).deposit{value: amount}() {} catch {
                    revert("WithdrawDepositErr");
                }
            }
        }
    }

    /// @dev Convert wrapped eth to eth and Transfer.
    function transferUnwrappedAsset(
        address currentAssetId,
        address expectAssetId,
        uint256 amount,
        address receiver
    ) internal {
        if (LibAsset.isNativeAsset(expectAssetId)) {
            if (currentAssetId != expectAssetId) {
                try IWETH(currentAssetId).withdraw(amount) {} catch {
                    revert("WithdrawErr");
                }
            }
        } else {
            require(currentAssetId == expectAssetId, "AssetIdErr");
        }
        if (receiver != address(this)) {
            require(
                LibAsset.getOwnBalance(expectAssetId) >= amount,
                "NotEnough"
            );
            LibAsset.transferAsset(expectAssetId, payable(receiver), amount);
        }
    }

    /// @dev Find swap slice
    /// @param swapData Array of data used to execute swaps
    function _getSwapAmount(
        LibSwap.SwapData[] memory swapData
    ) internal returns (uint256) {
        address sendingAssetId = swapData[0].sendingAssetId;
        uint256 amount;
        for (uint256 i = 0; i < swapData.length; i++) {
            if (
                swapData[i].sendingAssetId == sendingAssetId &&
                swapData[i].fromAmount > 0
            ) {
                amount += swapData[i].fromAmount;
            }
        }
        return amount;
    }

    /// Private Methods ///

    /// @dev Executes swaps and checks that DEXs used are in the allowList
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    /// @param startIndex Start index used to execute swaps
    /// @param endIndex End index used to execute swaps
    /// @param deltaFromAmount Delta fromAmount used to execute swaps,
    /// @param deltaMinAmount Delta minAmount used to execute swaps,
    /// @param correctSwap Correct swap address
    function _executeSwapsInner(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData,
        uint256 startIndex,
        uint256 endIndex,
        uint256 deltaFromAmount,
        uint256 deltaMinAmount,
        address correctSwap
    ) private returns (bool, uint256, uint256) {
        CacheSwapInnerParam memory cache;
        cache.currentSwapData = swapData[startIndex];
        cache.fromAmount = cache.currentSwapData.fromAmount;
        (cache.minAmount, ) = ICorrectSwap(correctSwap).fixMinAmount(
            swapData[endIndex - 1].callData,
            deltaMinAmount
        );
        cache.swapBalance = cache.currentSwapData.fromAmount + deltaFromAmount;

        for (uint256 i = startIndex; i < endIndex; i++) {
            if (i + 1 == endIndex && deltaMinAmount > 0) {
                (, cache.currentSwapData.callData) = ICorrectSwap(correctSwap)
                    .fixMinAmount(
                        cache.currentSwapData.callData,
                        deltaMinAmount
                    );
            }

            cache.currentSwapData.fromAmount = cache.swapBalance;
            cache.currentSwapData.callData = ICorrectSwap(correctSwap)
                .correctSwap(
                    cache.currentSwapData.callData,
                    cache.currentSwapData.fromAmount
                );

            cache.receivedToken = cache.currentSwapData.receivingAssetId;
            cache.swapBalance = LibAsset.getOwnBalance(cache.receivedToken);

            if (
                !(appStorage.dexAllowlist[cache.currentSwapData.approveTo] &&
                    appStorage.dexAllowlist[cache.currentSwapData.callTo] &&
                    appStorage.dexFuncSignatureAllowList[
                        bytes32(
                            LibUtil.getSlice(
                                cache.currentSwapData.callData,
                                0,
                                4
                            )
                        )
                    ])
            ) revert ContractCallNotAllowed();

            try
                this.libSwap(soData.transactionId, cache.currentSwapData)
            {} catch {
                return (false, cache.fromAmount, cache.minAmount);
            }

            cache.swapBalance =
                LibAsset.getOwnBalance(cache.receivedToken) -
                cache.swapBalance;

            if (i + 1 < swapData.length) {
                cache.currentSwapData = swapData[i + 1];
            }
        }
        return (true, cache.fromAmount, cache.minAmount);
    }

    /// @dev Executes swaps and checks that DEXs used are in the allowList
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function _executeSwaps(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) private {
        address correctSwap = appStorage.correctSwapRouterSelectors;
        if (correctSwap == address(0)) revert NotSupportedSwapRouter();
        _executeSwapsInner(
            soData,
            swapData,
            0,
            swapData.length,
            0,
            0,
            correctSwap
        );
    }

    /// @dev Find swap slice
    /// @param swapData Array of data used to execute swaps
    function _findSwapSlice(
        LibSwap.SwapData[] calldata swapData
    ) private returns (uint256[] memory) {
        address sendingAssetId = swapData[0].sendingAssetId;
        uint256 sliceLength = 0;
        for (uint256 i = 0; i < swapData.length; i++) {
            if (
                swapData[i].sendingAssetId == sendingAssetId &&
                swapData[i].fromAmount > 0
            ) {
                sliceLength += 1;
            }
        }

        uint256[] memory sliceIndex = new uint256[](sliceLength);
        uint256 index = 0;
        for (uint256 i = 0; i < swapData.length; i++) {
            if (
                swapData[i].sendingAssetId == sendingAssetId &&
                swapData[i].fromAmount > 0
            ) {
                sliceIndex[index] = i;
                index += 1;
            }
        }
        return sliceIndex;
    }

    /// @dev Executes swaps and checks that DEXs used are in the allowList. Support dynamic slice swap
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function _executeSwapsV2(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) private {
        CacheSwapParam memory cache;
        cache.correctSwap = appStorage.correctSwapRouterSelectors;
        if (cache.correctSwap == address(0)) revert NotSupportedSwapRouter();
        cache.sliceIndex = _findSwapSlice(swapData);
        for (uint256 k = 0; k < cache.sliceIndex.length; k++) {
            cache.startIndex = cache.sliceIndex[k];
            if (k + 1 == cache.sliceIndex.length) {
                cache.endIndex = swapData.length;
            } else {
                cache.endIndex = cache.sliceIndex[k + 1];
            }
            (
                bool flag,
                uint256 fromAmount,
                uint256 minAmount
            ) = _executeSwapsInner(
                    soData,
                    swapData,
                    cache.startIndex,
                    cache.endIndex,
                    cache.deltaFromAmount,
                    cache.deltaMinAmount,
                    cache.correctSwap
                );
            if (!flag) {
                cache.deltaFromAmount += fromAmount;
                cache.deltaMinAmount += minAmount;
            } else {
                cache.deltaFromAmount = 0;
                cache.deltaMinAmount = 0;
            }
        }
    }
}
