// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IOpenOceanCaller {
    struct CallDescription {
        uint256 target;
        uint256 gasLimit;
        uint256 value;
        bytes data;
    }

    function makeCall(CallDescription memory desc) external;

    function makeCalls(CallDescription[] memory desc) external payable;
}

interface IOpenOceanExchange {
    struct SwapDescription {
        IERC20 srcToken;
        IERC20 dstToken;
        address srcReceiver;
        address dstReceiver;
        uint256 amount;
        uint256 minReturnAmount;
        uint256 guaranteedAmount;
        uint256 flags;
        address referrer;
        bytes permit;
    }

    function swap(
        IOpenOceanCaller caller,
        SwapDescription calldata desc,
        IOpenOceanCaller.CallDescription[] calldata calls
    ) external payable returns (uint256 returnAmount);
}

interface IUniswapV2Exchange {
    function callUniswap(
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        bytes32[] calldata pools
    ) external payable returns (uint256 returnAmount);

    function callUniswapTo(
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        bytes32[] calldata, /* pools */
        address payable recipient
    ) external payable returns (uint256 returnAmount);

    function callUniswapWithPermit(
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        bytes32[] calldata pools,
        bytes calldata permit
    ) external returns (uint256 returnAmount);

    function callUniswapToWithPermit(
        IERC20 srcToken,
        uint256 amount,
        uint256 minReturn,
        bytes32[] calldata pools,
        bytes calldata permit,
        address payable recipient
    ) external returns (uint256 returnAmount);
}
