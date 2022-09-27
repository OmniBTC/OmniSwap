// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface ICorrectSwap {
    function correctSwap(bytes calldata, uint256)
        external
        pure
        returns (bytes memory);
}
