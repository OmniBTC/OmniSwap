// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity 0.8.13;

interface IMultiChainUnderlying {
    function underlying() external view returns (address);

    function deposit(uint256 amount, address to) external returns (uint256);

    function withdraw(uint256 amount, address to) external returns (uint256);
}
