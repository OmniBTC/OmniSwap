// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

interface IStargateEthVault {

    event Approval(address indexed src, address indexed guy, uint wad);
    event Transfer(address indexed src, address indexed dst, uint wad);
    event Deposit(address indexed dst, uint wad);
    event Withdrawal(address indexed src, uint wad);
    event TransferNative(address indexed src, address indexed dst, uint wad);

    function balanceOf(address account) external view returns (uint256);

    function noUnwrapTo(address) external view returns (bool);

    function deposit() external payable;

    function transfer(address to, uint value) external returns (bool);

    function withdraw(uint) external;

    function approve(address guy, uint wad) external returns (bool);

    function transferFrom(address src, address dst, uint wad) external returns (bool);
}
