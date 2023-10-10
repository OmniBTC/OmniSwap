// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;


/// @title Interface for LiquidityManager
interface IZiSwapQuoter {

    struct SwapAmountParams {
        bytes path;
        address recipient;
        uint128 amount;
        uint256 minAcquired;

        uint256 deadline;
    }
    /// @notice Swap given amount of input token, usually used in multi-hop case.
    function swapAmount(SwapAmountParams calldata params)
        external
        payable
        returns (uint256 cost, uint256 acquire);
}