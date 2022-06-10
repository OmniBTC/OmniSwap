// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;


interface IStargateFactory {
    function allPoolsLength() external view returns (uint256);

    function getPool(uint256 poolId) external view returns (address);

}
