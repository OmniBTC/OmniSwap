// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.4;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IMetaAggregationRouterV2 {
    struct SwapDescriptionV2 {
        IERC20 srcToken;
        IERC20 dstToken;
        address[] srcReceivers; // transfer src token to these addresses, default
        uint256[] srcAmounts;
        address[] feeReceivers;
        uint256[] feeAmounts;
        address dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 flags;
        bytes permit;
    }

    /// @dev  use for swapGeneric and swap to avoid stack too deep
    struct SwapExecutionParams {
        address callTarget; // call this address
        address approveTarget; // approve this address if _APPROVE_FUND set
        bytes targetData;
        SwapDescriptionV2 desc;
        bytes clientData;
    }

    struct SimpleSwapData {
        address[] firstPools;
        uint256[] firstSwapAmounts;
        bytes[] swapDatas;
        uint256 deadline;
        bytes destTokenFeeData;
    }

    event Swapped(
        address sender,
        IERC20 srcToken,
        IERC20 dstToken,
        address dstReceiver,
        uint256 spentAmount,
        uint256 returnAmount
    );

    event ClientData(bytes clientData);

    event Exchange(address pair, uint256 amountOut, address output);

    event Fee(
        address token,
        uint256 totalAmount,
        uint256 totalFee,
        address[] recipients,
        uint256[] amounts,
        bool isBps
    );

    function swapGeneric(SwapExecutionParams calldata execution)
        external
        payable
        returns (uint256 returnAmount, uint256 gasUsed);

    function swap(SwapExecutionParams calldata execution)
        external
        payable
        returns (uint256 returnAmount, uint256 gasUsed);

    function swapSimpleMode(
        address caller,
        SwapDescriptionV2 memory desc,
        bytes calldata executorData,
        bytes calldata clientData
    ) external returns (uint256 returnAmount, uint256 gasUsed);
}
