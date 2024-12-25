// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../Libraries/LibDiamond.sol";

/// @title Allowance Facet
/// @notice clears allowance for a token
contract AllowanceFacet {
    /// Events ///

    event LogClear(address indexed token);

    /// External Methods ///

    /// @notice clears allowance for a token
    /// @param token The token to clear the allowance for
    /// @param spenders The addresses to clear the allowance for
    function clearAllowance(address token, address[] memory spenders) external {
        LibDiamond.enforceIsContractOwner();

        for (uint256 i = 0; i < spenders.length; i++) {
            SafeERC20.safeApprove(IERC20(token), spenders[i], 0);
        }

        emit LogClear(token);
    }
}
