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
import {InvalidAmount, ContractCallNotAllowed, NoSwapDataProvided, NotSupportedSwapRouter, NotEnoughMinAmount} from "../Errors/GenericErrors.sol";

/// @title Swapper
/// @notice Abstract contract to provide swap functionality
contract Swapper is ISo {
    /// Storage ///

    LibStorage internal appStorage;

    /// Modifiers ///

    /// @dev Sends any leftover balances back to the user
    modifier noLeftovers(LibSwap.SwapData[] calldata swapData) {
        uint256 nSwaps = swapData.length;
        if (nSwaps != 1) {
            uint256[] memory initialBalances = _fetchBalances(swapData);
            address finalAsset = swapData[nSwaps - 1].receivingAssetId;
            uint256 curBalance = 0;

            _;

            for (uint256 i = 0; i < nSwaps - 1; i++) {
                address curAsset = swapData[i].receivingAssetId;
                if (curAsset == finalAsset) continue; // Handle multi-to-one swaps
                curBalance =
                    LibAsset.getOwnBalance(curAsset) -
                    initialBalances[i];
                if (curBalance > 0)
                    LibAsset.transferAsset(
                        curAsset,
                        payable(msg.sender),
                        curBalance
                    );
            }
        } else _;
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
        uint256 minAmount = _executeSwapsV2(soData, swapData);
        swapBalance = LibAsset.getOwnBalance(finalTokenId) - swapBalance;
        if (swapBalance == 0) revert InvalidAmount();
        if (swapBalance < minAmount) revert NotEnoughMinAmount();
        return swapBalance;
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
        } else {
            // weth -> eth -> weth
            if (currentAssetId != expectAssetId) {
                try IWETH(currentAssetId).withdraw(amount) {} catch {
                    revert("DepositWithdrawErr");
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

    /// Private Methods ///

    /// @dev Executes swaps and checks that DEXs used are in the allowList
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function _executeSwaps(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) private {
        LibSwap.SwapData memory currentSwapData = swapData[0];
        for (uint256 i = 0; i < swapData.length; i++) {
            address receivedToken = currentSwapData.receivingAssetId;
            uint256 swapBalance = LibAsset.getOwnBalance(receivedToken);

            if (
                !(appStorage.dexAllowlist[currentSwapData.approveTo] &&
                    appStorage.dexAllowlist[currentSwapData.callTo] &&
                    appStorage.dexFuncSignatureAllowList[
                        bytes32(
                            LibUtil.getSlice(currentSwapData.callData, 0, 4)
                        )
                    ])
            ) revert ContractCallNotAllowed();

            LibSwap.swap(soData.transactionId, currentSwapData);

            swapBalance = LibAsset.getOwnBalance(receivedToken) - swapBalance;

            if (i + 1 < swapData.length) {
                currentSwapData = swapData[i + 1];
                address correctSwap = appStorage.correctSwapRouterSelectors;
                if (correctSwap == address(0)) revert NotSupportedSwapRouter();
                currentSwapData.fromAmount = swapBalance;
                currentSwapData.callData = ICorrectSwap(correctSwap)
                    .correctSwap(
                        currentSwapData.callData,
                        currentSwapData.fromAmount
                    );
            }
        }
    }

    function _findSwapSlice(LibSwap.SwapData[] calldata swapData)
        private
        returns (uint256[] memory)
    {
        address sendingAssetId = swapData[0].sendingAssetId;
        uint256 sliceLength = 0;
        for (uint256 i = 0; i < swapData.length; i++) {
            if (swapData[i].sendingAssetId == sendingAssetId) {
                sliceLength += 1;
            }
        }

        uint256[] memory sliceIndex = new uint256[](sliceLength);
        uint256 index = 0;
        for (uint256 i = 0; i < swapData.length; i++) {
            if (swapData[i].sendingAssetId == sendingAssetId) {
                sliceIndex[index] = i;
                index += 1;
            }
        }
    }

    /// @dev Executes swaps and checks that DEXs used are in the allowList. Support dynamic slice swap
    /// @param soData So tracking data
    /// @param swapData Array of data used to execute swaps
    function _executeSwapsV2(
        SoData memory soData,
        LibSwap.SwapData[] calldata swapData
    ) private returns (uint256) {
        address correctSwap = appStorage.correctSwapRouterSelectors;
        if (correctSwap == address(0)) revert NotSupportedSwapRouter();
        (uint256 minAmount, bytes memory swapCallData) = ICorrectSwap(
            correctSwap
        ).fixMinAmountZero(swapData[swapData.length - 1].callData);

        uint256[] memory sliceIndex = _findSwapSlice(swapData);
        for (uint256 k = 0; k < sliceIndex.length; k++) {
            uint256 endIndex;
            if (k + 1 == sliceIndex.length) {
                endIndex = swapData.length;
            } else {
                endIndex = sliceIndex[k + 1];
            }
            LibSwap.SwapData memory currentSwapData = swapData[sliceIndex[k]];
            for (uint256 i = sliceIndex[k]; i < endIndex; i++) {
                address receivedToken = currentSwapData.receivingAssetId;
                uint256 swapBalance = LibAsset.getOwnBalance(receivedToken);

                if (
                    !(appStorage.dexAllowlist[currentSwapData.approveTo] &&
                        appStorage.dexAllowlist[currentSwapData.callTo] &&
                        appStorage.dexFuncSignatureAllowList[
                            bytes32(
                                LibUtil.getSlice(currentSwapData.callData, 0, 4)
                            )
                        ])
                ) revert ContractCallNotAllowed();

                LibSwap.swap(soData.transactionId, currentSwapData);

                swapBalance =
                    LibAsset.getOwnBalance(receivedToken) -
                    swapBalance;

                if (i + 1 < swapData.length) {
                    currentSwapData = swapData[i + 1];
                    currentSwapData.fromAmount = swapBalance;
                    if (i + 1 == swapData.length - 1) {
                        currentSwapData.callData = ICorrectSwap(correctSwap)
                            .correctSwap(
                                swapCallData,
                                currentSwapData.fromAmount
                            );
                    } else {
                        currentSwapData.callData = ICorrectSwap(correctSwap)
                            .correctSwap(
                                currentSwapData.callData,
                                currentSwapData.fromAmount
                            );
                    }
                }
            }
        }
        return minAmount;
    }

    /// @dev Fetches balances of tokens to be swapped before swapping.
    /// @param swapData Array of data used to execute swaps
    /// @return uint256[] Array of token balances.
    function _fetchBalances(LibSwap.SwapData[] calldata swapData)
        private
        view
        returns (uint256[] memory)
    {
        uint256 length = swapData.length;
        uint256[] memory balances = new uint256[](length);
        for (uint256 i = 0; i < length; i++)
            balances[i] = LibAsset.getOwnBalance(swapData[i].receivingAssetId);
        return balances;
    }
}
