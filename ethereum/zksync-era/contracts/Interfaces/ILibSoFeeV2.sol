// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface ILibSoFeeV2 {
    function getFees(uint256 _amount) external view returns (uint256 s);

    function getRestoredAmount(uint256 _amount)
        external
        view
        returns (uint256 r);

    function getTransferForGas() external view returns (uint256);

    function getVersion() external view returns (string memory);

    function getBasicBeneficiary() external view returns (address);

    function getBasicFee() external view returns (uint256);
}
