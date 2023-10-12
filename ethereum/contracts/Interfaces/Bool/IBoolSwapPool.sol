// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;

interface IBoolSwapPool {
    function feeRatio() external view returns (uint16);

    function token() external view returns (address);

    function swapLimit() external view returns (uint256);

    function liquidity() external view returns (uint256);
}
