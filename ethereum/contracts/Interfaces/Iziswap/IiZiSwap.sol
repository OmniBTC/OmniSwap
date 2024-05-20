// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.4;

interface IiZiSwap {
    struct SwapDesireParams {
        bytes path;
        address recipient;
        uint128 desire;
        uint256 maxPayed;
        uint256 deadline;
    }

    struct SwapAmountParams {
        bytes path;
        address recipient;
        // uint256 deadline;
        uint128 amount;
        uint256 minAcquired;
        uint256 deadline;
    }

    function swapAmount(
        SwapAmountParams calldata params
    ) external payable returns (uint256 cost, uint256 acquire);

    /// @notice Swap given amount of target token, usually used in multi-hop case.
    function swapDesire(
        SwapDesireParams calldata params
    ) external payable returns (uint256 cost, uint256 acquire);

    /// parameters when calling Swap.swap..., grouped together to avoid stake too deep
    struct SwapParams {
        // tokenX of swap pool
        address tokenX;
        // tokenY of swap pool
        address tokenY;
        // fee amount of swap pool
        uint24 fee;
        // highPt for y2x, lowPt for x2y
        // here y2X is calling swapY2X or swapY2XDesireX
        // in swapY2XDesireX, if boundaryPt is 800001, means user wants to get enough X
        // in swapX2YDesireY, if boundaryPt is -800001, means user wants to get enough Y
        int24 boundaryPt;
        // who will receive acquired token
        address recipient;
        // desired amount for desired mode, paid amount for non-desired mode
        // here, desire mode is calling swapX2YDesireY or swapY2XDesireX
        uint128 amount;
        // max amount of payed token from trader, used in desire mode
        uint256 maxPayed;
        // min amount of received token trader wanted, used in undesire mode
        uint256 minAcquired;
        uint256 deadline;
    }

    /// @notice Swap tokenY for tokenX, given max amount of tokenY user willing to pay
    /// @param swapParams params(for example: max amount in above line), see SwapParams for more
    function swapY2X(SwapParams calldata swapParams) external payable;

    /// @notice Swap tokenY for tokenX, given user's desired amount of tokenX.
    /// @param swapParams params(for example: desired amount in above line), see SwapParams for more
    function swapY2XDesireX(SwapParams calldata swapParams) external payable;

    /// @notice Swap tokenX for tokenY, given max amount of tokenX user willing to pay.
    /// @param swapParams params(for example: max amount in above line), see SwapParams for more
    function swapX2Y(SwapParams calldata swapParams) external payable;

    /// @notice Swap tokenX for tokenY, given amount of tokenY user desires.
    /// @param swapParams params(for example: desired amount in above line), see SwapParams for more
    function swapX2YDesireY(SwapParams calldata swapParams) external payable;
}
