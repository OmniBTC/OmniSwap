// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "../../Libraries/LzLib.sol";

interface IWrappedTokenBridge {
    function estimateBridgeFee(
        uint16 remoteChainId,
        bool useZro,
        bytes calldata adapterParams
    ) external view returns (uint nativeFee, uint zroFee);
    function bridge(
        address localToken,
        uint16 remoteChainId,
        uint amount,
        address to,
        bool unwrapWeth,
        LzLib.CallParams calldata callParams,
        bytes memory adapterParams
    ) external payable;
}
