// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

struct LibStorage {
    mapping(address => bool) dexAllowlist;
    mapping(bytes32 => bool) dexFuncSignatureAllowList;
    address[] dexs;
    // maps gateway facet addresses to sofee address
    mapping(address => address) gatewaySoFeeSelectors;
    // Storage correct swap address
    address correctSwapRouterSelectors;
}
