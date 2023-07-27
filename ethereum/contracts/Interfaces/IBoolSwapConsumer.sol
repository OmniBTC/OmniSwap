// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;

interface IBoolSwapConsumer {
    function receiveFromBoolSwap(
        uint32 srcChainId,
        address bridgeToken,
        uint256 bridgeAmount,
        bytes calldata payload
    ) external payable;
}
