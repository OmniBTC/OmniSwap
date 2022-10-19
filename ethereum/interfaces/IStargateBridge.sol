// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;


interface IStargateBridge {
    function layerZeroEndpoint() external view returns (address);
}
