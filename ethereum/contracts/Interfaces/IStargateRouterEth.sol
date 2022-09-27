// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

interface IStargateRouterEth {
    function stargateEthVault() external view returns (address);

    function stargateRouter() external view returns (address);

    function poolId() external view returns (uint16);
}
