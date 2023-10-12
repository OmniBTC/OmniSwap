// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;

interface IBoolSwapFactory {
    struct PoolInfo {
        uint16 fee;
        address pool;
        address token;
        address anchor;
        uint256 liquidity;
    }

    function fetchPool(uint32 poolId) external view returns (address);

    function fetchInfo(uint32 poolId) external view returns (PoolInfo memory);
}
