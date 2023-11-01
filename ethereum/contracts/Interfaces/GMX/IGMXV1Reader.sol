// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {IGMXV1Vault} from "./IGMXV1Vault.sol";

interface IGMXV1Reader {
    function getAmountOut(
        IGMXV1Vault _vault,
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn
    ) external view returns (uint256, uint256);
}
