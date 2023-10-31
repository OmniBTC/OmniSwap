// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IOneInchUnoswapV3Router {
    /// @notice Same as `uniswapV3SwapTo` but calls permit first,
    /// allowing to approve token spending and make a swap in one transaction.
    /// @param recipient Address that will receive swap funds
    /// @param srcToken Source token
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    /// @param permit Should contain valid permit that can be used in `IERC20Permit.permit` calls.
    /// See tests for examples
    function uniswapV3SwapToWithPermit(
        address payable recipient,
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools,
        bytes calldata permit
    ) external returns (uint256 returnAmount);

    /// @notice Same as `uniswapV3SwapTo` but uses `msg.sender` as recipient
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    function uniswapV3Swap(
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools
    ) external payable returns (uint256 returnAmount);

    /// @notice Performs swap using Uniswap V3 exchange. Wraps and unwraps ETH if required.
    /// Sending non-zero `msg.value` for anything but ETH swaps is prohibited
    /// @param recipient Address that will receive swap funds
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    function uniswapV3SwapTo(
        address payable recipient,
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools
    ) external payable returns (uint256 returnAmount);

    function uniswapV3SwapCallback(
        int256 amount0Delta,
        int256 amount1Delta,
        bytes calldata /* data */
    ) external;
}
