// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface ICorrectSwap {
    function correctSwap(
        bytes calldata,
        uint256
    ) external returns (bytes memory);

    function fixMinAmount(
        bytes calldata,
        uint256
    ) external view returns (uint256, bytes memory);
}
