// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { LibDiamond } from "../Libraries/LibDiamond.sol";

/// @title Withdraw Facet
/// @author LI.FI (https://li.fi)
/// @notice Allows admin to withdraw funds that are kept in the contract by accident
contract WithdrawFacet {
    /// Storage ///

    address private constant NATIVE_ASSET = 0x0000000000000000000000000000000000000000; // address(0)

    /// Errors ///

    error NotEnoughBalance(uint256 requested, uint256 available);
    error WithdrawFailed();

    /// Events ///

    event LogWithdraw(address indexed _assetAddress, address _to, uint256 amount);

    /// External Methods ///

    /// @notice Withdraw asset.
    /// @param _assetAddress Asset to be withdrawn.
    /// @param _to address to withdraw to.
    /// @param _amount amount of asset to withdraw.
    function withdraw(
        address _assetAddress,
        address _to,
        uint256 _amount
    ) external {
        LibDiamond.enforceIsContractOwner();
        address sendTo = (_to == address(0)) ? msg.sender : _to;
        uint256 assetBalance;
        if (_assetAddress == NATIVE_ASSET) {
            address self = address(this); // workaround for a possible solidity bug

            if (_amount > self.balance) revert NotEnoughBalance(_amount, self.balance);
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, ) = payable(sendTo).call{ value: _amount }("");
            if (!success) revert WithdrawFailed();
        } else {
            assetBalance = IERC20(_assetAddress).balanceOf(address(this));
            if (_amount > assetBalance) revert NotEnoughBalance(_amount, assetBalance);
            SafeERC20.safeTransfer(IERC20(_assetAddress), sendTo, _amount);
        }
        emit LogWithdraw(_assetAddress, sendTo, _amount);
    }
}
