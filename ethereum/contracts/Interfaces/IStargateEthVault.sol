// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

interface IStargateEthVault {
    event Approval(address indexed src, address indexed guy, uint256 wad);
    event Transfer(address indexed src, address indexed dst, uint256 wad);
    event Deposit(address indexed dst, uint256 wad);
    event Withdrawal(address indexed src, uint256 wad);
    event TransferNative(address indexed src, address indexed dst, uint256 wad);

    function balanceOf(address account) external view returns (uint256);

    function noUnwrapTo(address) external view returns (bool);

    function deposit() external payable;

    function transfer(address to, uint256 value) external returns (bool);

    function withdraw(uint256) external;

    function approve(address guy, uint256 wad) external returns (bool);

    function transferFrom(
        address src,
        address dst,
        uint256 wad
    ) external returns (bool);
}
