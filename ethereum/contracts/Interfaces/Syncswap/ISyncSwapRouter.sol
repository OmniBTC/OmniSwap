pragma solidity >=0.6.2;

interface ISyncSwapRouter {
    // The Router contract has Multicall and SelfPermit enabled.

    struct TokenInput {
        address token;
        uint256 amount;
    }

    struct SwapStep {
        address pool; // The pool of the step.
        bytes data; // The data to execute swap with the pool.
        address callback;
        bytes callbackData;
    }

    struct SwapPath {
        SwapStep[] steps; // Steps of the path.
        address tokenIn; // The input token of the path.
        uint256 amountIn; // The input token amount of the path.
    }

    struct SplitPermitParams {
        address token;
        uint256 approveAmount;
        uint256 deadline;
        uint8 v;
        bytes32 r;
        bytes32 s;
    }

    struct ArrayPermitParams {
        uint256 approveAmount;
        uint256 deadline;
        bytes signature;
    }

    // Returns the vault address.
    function vault() external view returns (address);

    // Returns the wETH address.
    function wETH() external view returns (address);

    // Performs a swap.
    function swap(
        SwapPath[] memory paths,
        uint256 amountOutMin,
        uint256 deadline
    ) external payable returns (uint256 amountOut);

    function swapWithPermit(
        SwapPath[] memory paths,
        uint256 amountOutMin,
        uint256 deadline,
        SplitPermitParams calldata permit
    ) external payable returns (uint256 amountOut);

    /// @notice Wrapper function to allow pool deployment to be batched.
    function createPool(
        address factory,
        bytes calldata data
    ) external payable returns (address);
}
