// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.13;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IStableSwap {
    /*** EVENTS ***/

    // events replicated from SwapUtils to make the ABI easier for dumb
    // clients
    event TokenSwap(
        address indexed buyer,
        uint256 tokensSold,
        uint256 tokensBought,
        uint128 soldId,
        uint128 boughtId
    );
    event AddLiquidity(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256[] fees,
        uint256 invariant,
        uint256 lpTokenSupply
    );
    event RemoveLiquidity(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256 lpTokenSupply
    );
    event RemoveLiquidityOne(
        address indexed provider,
        uint256 lpTokenAmount,
        uint256 lpTokenSupply,
        uint256 boughtId,
        uint256 tokensBought
    );
    event RemoveLiquidityImbalance(
        address indexed provider,
        uint256[] tokenAmounts,
        uint256[] fees,
        uint256 invariant,
        uint256 lpTokenSupply
    );
    event NewAdminFee(uint256 newAdminFee);
    event NewSwapFee(uint256 newSwapFee);
    event NewWithdrawFee(uint256 newWithdrawFee);
    event RampA(
        uint256 oldA,
        uint256 newA,
        uint256 initialTime,
        uint256 futureTime
    );
    event StopRampA(uint256 currentA, uint256 time);

    function swap(
        bytes32 key,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dx,
        uint256 minDy,
        uint256 deadline
    ) external returns (uint256);

    function swapExact(
        bytes32 key,
        uint256 amountIn,
        address assetIn,
        address assetOut,
        uint256 minAmountOut,
        uint256 deadline
    ) external payable returns (uint256);

    function swapExactOut(
        bytes32 key,
        uint256 amountOut,
        address assetIn,
        address assetOut,
        uint256 maxAmountIn,
        uint256 deadline
    ) external payable returns (uint256);

    function getA(bytes32 key) external view returns (uint256);

    function getToken(bytes32 key, uint8 index) external view returns (IERC20);

    function getTokenIndex(bytes32 key, address tokenAddress)
    external
    view
    returns (uint8);

    function getTokenBalance(bytes32 key, uint8 index)
    external
    view
    returns (uint256);

    function getVirtualPrice(bytes32 key) external view returns (uint256);

    // min return calculation functions
    function calculateSwap(
        bytes32 key,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dx
    ) external view returns (uint256);

    function calculateSwapOut(
        bytes32 key,
        uint8 tokenIndexFrom,
        uint8 tokenIndexTo,
        uint256 dy
    ) external view returns (uint256);

    function calculateSwapFromAddress(
        bytes32 key,
        address assetIn,
        address assetOut,
        uint256 amountIn
    ) external view returns (uint256);

    function calculateSwapOutFromAddress(
        bytes32 key,
        address assetIn,
        address assetOut,
        uint256 amountOut
    ) external view returns (uint256);

    function calculateTokenAmount(
        bytes32 key,
        uint256[] calldata amounts,
        bool deposit
    ) external view returns (uint256);

    function calculateRemoveLiquidity(bytes32 key, uint256 amount)
    external
    view
    returns (uint256[] memory);

    function calculateRemoveLiquidityOneToken(
        bytes32 key,
        uint256 tokenAmount,
        uint8 tokenIndex
    ) external view returns (uint256 availableTokenAmount);

    // state modifying functions
    function initialize(
        IERC20[] memory pooledTokens,
        uint8[] memory decimals,
        string memory lpTokenName,
        string memory lpTokenSymbol,
        uint256 a,
        uint256 fee,
        uint256 adminFee,
        address lpTokenTargetAddress
    ) external;

    function addLiquidity(
        bytes32 key,
        uint256[] calldata amounts,
        uint256 minToMint,
        uint256 deadline
    ) external returns (uint256);

    function removeLiquidity(
        bytes32 key,
        uint256 amount,
        uint256[] calldata minAmounts,
        uint256 deadline
    ) external returns (uint256[] memory);

    function removeLiquidityOneToken(
        bytes32 key,
        uint256 tokenAmount,
        uint8 tokenIndex,
        uint256 minAmount,
        uint256 deadline
    ) external returns (uint256);

    function removeLiquidityImbalance(
        bytes32 key,
        uint256[] calldata amounts,
        uint256 maxBurnAmount,
        uint256 deadline
    ) external returns (uint256);
}
