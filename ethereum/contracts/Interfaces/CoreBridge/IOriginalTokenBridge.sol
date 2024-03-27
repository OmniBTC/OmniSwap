// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "../../Libraries/LzLib.sol";

interface IOriginalTokenBridge {
    function estimateBridgeFee(
        bool useZro,
        bytes calldata adapterParams
    ) external view returns (uint nativeFee, uint zroFee);
    function bridge(
        address token,
        uint amountLD,
        address to,
        LzLib.CallParams calldata callParams,
        bytes memory adapterParams
    ) external payable;
    function bridgeNative(
        uint amountLD,
        address to,
        LzLib.CallParams calldata callParams,
        bytes memory adapterParams
    ) external payable;
}
