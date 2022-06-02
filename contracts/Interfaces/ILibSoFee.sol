// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface ILibSoFee {
    function getFees(
        uint256 _amount
    ) external returns (uint256 s);

    function getVersion() external view returns (string memory);
}
