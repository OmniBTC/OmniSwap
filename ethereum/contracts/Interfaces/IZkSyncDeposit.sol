// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

interface IZkSyncDeposit {
    /// @notice Deposit ETH to Layer 2 - transfer ether from user into contract, validate it, register deposit
    /// @param _zkSyncAddress The receiver Layer 2 address
    function depositETH(address _zkSyncAddress) external payable;
    /// @dev Flag indicates that exodus (mass exit) mode is triggered
    /// @dev Once it was raised, it can not be cleared again, and all users must exit
    function exodusMode() external view returns (bool);
}