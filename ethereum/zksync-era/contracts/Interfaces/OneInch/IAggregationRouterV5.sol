// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title Interface for making arbitrary calls during swap
interface IAggregationExecutor {
    /// @notice propagates information about original msg.sender and executes arbitrary data
    function execute(address msgSender) external payable; // 0x4b64e492
}

interface IOneInchGenericRouter {
    struct SwapDescription {
        IERC20 srcToken;
        IERC20 dstToken;
        address payable srcReceiver;
        address payable dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 flags;
    }

    /// @notice Performs a swap, delegating all calls encoded in `data` to `executor`. See tests for usage examples
    /// @dev router keeps 1 wei of every token on the contract balance for gas optimisations reasons. This affects first swap of every token by leaving 1 wei on the contract.
    /// @param executor Aggregation executor that executes calls described in `data`
    /// @param desc Swap description
    /// @param permit Should contain valid permit that can be used in `IERC20Permit.permit` calls.
    /// @param data Encoded calls that `caller` should execute in between of swaps
    /// @return returnAmount Resulting token amount
    /// @return spentAmount Source token amount
    function swap(
        IAggregationExecutor executor,
        SwapDescription calldata desc,
        bytes calldata permit,
        bytes calldata data
    ) external payable returns (uint256 returnAmount, uint256 spentAmount);
}

/// @title Clipper interface subset used in swaps
interface IClipperExchangeInterface {
    struct Signature {
        uint8 v;
        bytes32 r;
        bytes32 s;
    }

    function sellEthForToken(
        address outputToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        address destinationAddress,
        Signature calldata theSignature,
        bytes calldata auxiliaryData
    ) external payable;

    function sellTokenForEth(
        address inputToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        address destinationAddress,
        Signature calldata theSignature,
        bytes calldata auxiliaryData
    ) external;

    function swap(
        address inputToken,
        address outputToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        address destinationAddress,
        Signature calldata theSignature,
        bytes calldata auxiliaryData
    ) external;
}

interface IOneInchClipperRouter {
    /// @notice Same as `clipperSwapTo` but calls permit first,
    /// allowing to approve token spending and make a swap in one transaction.
    /// @dev See tests for examples
    /// @param recipient Address that will receive swap funds
    /// @param srcToken Source token
    /// @param dstToken Destination token
    /// @param inputAmount Amount of source tokens to swap
    /// @param outputAmount Amount of destination tokens to receive
    /// @param goodUntil Timestamp until the swap will be valid
    /// @param r Clipper order signature (r part)
    /// @param vs Clipper order signature (vs part)
    /// @param permit Should contain valid permit that can be used in `IERC20Permit.permit` calls.
    /// @return returnAmount Amount of destination tokens received
    function clipperSwapToWithPermit(
        IClipperExchangeInterface clipperExchange,
        address payable recipient,
        IERC20 srcToken,
        IERC20 dstToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        bytes32 r,
        bytes32 vs,
        bytes calldata permit
    ) external returns (uint256 returnAmount);

    /// @notice Same as `clipperSwapTo` but uses `msg.sender` as recipient
    /// @param srcToken Source token
    /// @param dstToken Destination token
    /// @param inputAmount Amount of source tokens to swap
    /// @param outputAmount Amount of destination tokens to receive
    /// @param goodUntil Timestamp until the swap will be valid
    /// @param r Clipper order signature (r part)
    /// @param vs Clipper order signature (vs part)
    /// @return returnAmount Amount of destination tokens received
    function clipperSwap(
        IClipperExchangeInterface clipperExchange,
        IERC20 srcToken,
        IERC20 dstToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        bytes32 r,
        bytes32 vs
    ) external payable returns (uint256 returnAmount);

    /// @notice Performs swap using Clipper exchange. Wraps and unwraps ETH if required.
    /// Sending non-zero `msg.value` for anything but ETH swaps is prohibited
    /// @param recipient Address that will receive swap funds
    /// @param srcToken Source token
    /// @param dstToken Destination token
    /// @param inputAmount Amount of source tokens to swap
    /// @param outputAmount Amount of destination tokens to receive
    /// @param goodUntil Timestamp until the swap will be valid
    /// @param r Clipper order signature (r part)
    /// @param vs Clipper order signature (vs part)
    /// @return returnAmount Amount of destination tokens received
    function clipperSwapTo(
        IClipperExchangeInterface clipperExchange,
        address payable recipient,
        IERC20 srcToken,
        IERC20 dstToken,
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 goodUntil,
        bytes32 r,
        bytes32 vs
    ) external payable returns (uint256 returnAmount);
}

interface IOneInchUnoswapRouter {
    /// @notice Same as `unoswapTo` but calls permit first,
    /// allowing to approve token spending and make a swap in one transaction.
    /// @param recipient Address that will receive swapped funds
    /// @param srcToken Source token
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    /// @param permit Should contain valid permit that can be used in `IERC20Permit.permit` calls.
    /// See tests for examples
    function unoswapToWithPermit(
        address payable recipient,
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools,
        bytes calldata permit
    ) external returns (uint256 returnAmount);

    /// @notice Performs swap using Uniswap exchange. Wraps and unwraps ETH if required.
    /// Sending non-zero `msg.value` for anything but ETH swaps is prohibited
    /// @param recipient Address that will receive swapped funds
    /// @param srcToken Source token
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    function unoswapTo(
        address payable recipient,
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools
    ) external payable returns (uint256 returnAmount);

    /// @notice Performs swap using Uniswap exchange. Wraps and unwraps ETH if required.
    /// Sending non-zero `msg.value` for anything but ETH swaps is prohibited
    /// @param srcToken Source token
    /// @param amount Amount of source tokens to swap
    /// @param minReturn Minimal allowed returnAmount to make transaction commit
    /// @param pools Pools chain used for swaps. Pools src and dst tokens should match to make swap happen
    function unoswap(
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        uint256[] calldata pools
    ) external payable returns (uint256 returnAmount);
}

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
