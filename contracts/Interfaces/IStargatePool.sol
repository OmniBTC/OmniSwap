// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;


interface IStargatePool {
    struct ChainPath {
        bool ready; // indicate if the counter chainPath has been created.
        uint16 dstChainId;
        uint256 dstPoolId;
        uint256 weight;
        uint256 balance;
        uint256 lkb;
        uint256 credits;
        uint256 idealBalance;
    }

    struct SwapObj {
        uint256 amount;
        uint256 eqFee;
        uint256 eqReward;
        uint256 lpFee;
        uint256 protocolFee;
        uint256 lkbRemove;
    }

    function chainPaths(uint256 index) external view returns (ChainPath memory);

    function getChainPathsLength() external view returns (uint256);

    function getChainPath(uint16 _dstChainId, uint256 _dstPoolId) external view returns (ChainPath memory);

    function convertRate() external view returns (uint256);

    function token() external view returns (address);

    function feeLibrary() external view returns (address);

}
