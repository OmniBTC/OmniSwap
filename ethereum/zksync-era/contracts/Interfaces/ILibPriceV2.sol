// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

// Celer chain id is u64, stargate and wormhole are u16
// ILibPriceV2 for Celer bridge
interface ILibPriceV2 {
    function getPriceRatio(uint64 _chainId)
        external
        view
        returns (uint256, bool);

    function updatePriceRatio(uint64 _chainId) external returns (uint256);

    function RAY() external view returns (uint256);
}
