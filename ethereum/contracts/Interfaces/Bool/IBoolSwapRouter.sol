// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;

interface IBoolSwapRouter {
    function factory() external view returns (address);

    function swap(
        uint32 poolId,
        uint32 dstChainId,
        uint256 amount,
        bytes32 recipient,
        address payable refundAddress,
        bytes calldata consumerData
    ) external payable returns (bytes32 crossId);

    function estimateBNFee(
        uint32 poolId,
        uint32 dstChainId,
        uint256 amount,
        bytes32 recipient,
        bytes calldata consumerData
    ) external view returns (uint256 fee);
}
