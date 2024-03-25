// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface ILibPrice {
    function getPriceRatio(
        uint16 _chainId
    ) external view returns (uint256, bool);

    function updatePriceRatio(uint16 _chainId) external returns (uint256);

    function RAY() external view returns (uint256);
}
