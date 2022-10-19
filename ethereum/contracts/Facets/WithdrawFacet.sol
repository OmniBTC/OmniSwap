// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../Libraries/LibDiamond.sol";

/// @title Withdraw Facet
/// @notice Allows admin to withdraw funds that are kept in the contract by accident
contract WithdrawFacet {
    /// Storage ///

    address private constant NATIVE_ASSET =
        0x0000000000000000000000000000000000000000; // address(0)

    /// Errors ///

    error NotEnoughBalance(uint256 requested, uint256 available);
    error WithdrawFailed();

    /// Events ///

    event LogWithdraw(address indexed assetAddress, address to, uint256 amount);

    /// External Methods ///

    /// @notice Withdraw asset.
    /// @param assetAddress Asset to be withdrawn.
    /// @param to address to withdraw to.
    /// @param amount amount of asset to withdraw.
    function withdraw(
        address assetAddress,
        address to,
        uint256 amount
    ) external {
        LibDiamond.enforceIsContractOwner();
        address sendTo = (to == address(0)) ? msg.sender : to;
        uint256 assetBalance;
        if (assetAddress == NATIVE_ASSET) {
            address self = address(this); // workaround for a possible solidity bug

            if (amount > self.balance)
                revert NotEnoughBalance(amount, self.balance);
            // solhint-disable-next-line avoid-low-level-calls
            (bool success, ) = payable(sendTo).call{value: amount}("");
            if (!success) revert WithdrawFailed();
        } else {
            assetBalance = IERC20(assetAddress).balanceOf(address(this));
            if (amount > assetBalance)
                revert NotEnoughBalance(amount, assetBalance);
            SafeERC20.safeTransfer(IERC20(assetAddress), sendTo, amount);
        }
        emit LogWithdraw(assetAddress, sendTo, amount);
    }
}
