// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

interface IZkSyncDeposit {
    /// @notice Deposit ETH to Layer 2 - transfer ether from user into contract, validate it, register deposit
    /// @param _zkSyncAddress The receiver Layer 2 address
    function depositETH(address _zkSyncAddress) external payable;
    /// @notice Checks that contract is ready for upgrade
    /// @return bool flag indicating that contract is ready for upgrade
    function isReadyForUpgrade() external view returns (bool);
}