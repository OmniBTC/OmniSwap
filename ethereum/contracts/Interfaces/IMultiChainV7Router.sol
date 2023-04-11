// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity 0.8.13;

interface IMultiChainV7Router {
    struct ProxyInfo {
        bool supported;
        bool acceptAnyToken;
    }

    struct SwapInfo {
        bytes32 swapoutID;
        address token;
        address receiver;
        uint256 amount;
        uint256 fromChainID;
    }

    event LogAnySwapOutAndCall(
        bytes32 indexed swapoutID,
        address indexed token,
        address indexed from,
        string receiver,
        uint256 amount,
        uint256 toChainID,
        string anycallProxy,
        bytes data
    );

    event LogAnySwapInAndExec(
        string swapID,
        bytes32 indexed swapoutID,
        address indexed token,
        address indexed receiver,
        uint256 amount,
        uint256 fromChainID,
        bool success,
        bytes result
    );

    function anycallExecutor() external view returns (address);

    function anycallProxyInfo(address proxy) external view returns (ProxyInfo memory);

    // Swaps `amount` `token` from this chain to `toChainID` chain and call anycall proxy with `data`
    // `to` is the fallback receive address when exec failed on the `destination` chain
    function anySwapOutUnderlyingAndCall(
        address token,
        string calldata to,
        uint256 amount,
        uint256 toChainID,
        string calldata anycallProxy,
        bytes calldata data
    ) external;

    // Swaps `amount` `token` in `fromChainID` to `to` on this chainID with `to` receiving `underlying`
    function anySwapInUnderlyingAndExec(
        string calldata swapID,
        SwapInfo calldata swapInfo,
        address anycallProxy,
        bytes calldata data
    ) external;

    // Swaps `amount` `token` from this chain to `toChainID` chain with recipient `to`
    function anySwapOut(
        address token,
        string calldata to,
        uint256 amount,
        uint256 toChainID
    ) external;
}