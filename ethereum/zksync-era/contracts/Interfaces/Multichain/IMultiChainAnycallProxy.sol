// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity 0.8.13;

/// IMultiChainAnycallProxy interface of the anycall proxy
/// Note: `receiver` is the `fallback receive address` when exec failed.
interface IMultiChainAnycallProxy {
    function exec(
        address token,
        address receiver,
        uint256 amount,
        bytes calldata data
    ) external returns (bool success, bytes memory result);
}
