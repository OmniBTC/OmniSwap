// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "./IStargatePool.sol";

interface IStargateFeeLibrary {
    function getFees(
        uint256 _srcPoolId,
        uint256 _dstPoolId,
        uint16 _dstChainId,
        address _from,
        uint256 _amountSD
    ) external view returns (IStargatePool.SwapObj memory s);

    function getVersion() external view returns (string memory);
}
