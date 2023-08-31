// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Client} from "../Libraries/LibCCIPClient.sol";

interface IRouterClient {
    error UnsupportedDestinationChain(uint64 destChainSelector);
    error InsufficientFeeTokenAmount();
    error InvalidMsgValue();

    /// @notice Checks if the given chain ID is supported for sending/receiving.
    /// @param chainSelector The chain to check.
    /// @return supported is true if it is supported, false if not.
    function isChainSupported(uint64 chainSelector) external view returns (bool supported);

    /// @notice Gets a list of all supported tokens which can be sent or received
    /// to/from a given chain id.
    /// @param chainSelector The chainSelector.
    /// @return tokens The addresses of all tokens that are supported.
    function getSupportedTokens(uint64 chainSelector) external view returns (address[] memory tokens);

    /// @param destinationChainSelector The destination chainSelector
    /// @param message The cross-chain CCIP message including data and/or tokens
    /// @return fee returns guaranteed execution fee for the specified message
    /// delivery to destination chain
    /// @dev returns 0 fee on invalid message.
    function getFee(
        uint64 destinationChainSelector,
        Client.EVM2AnyMessage memory message
    ) external view returns (uint256 fee);

    /// @notice Request a message to be sent to the destination chain
    /// @param destinationChainSelector The destination chain ID
    /// @param message The cross-chain CCIP message including data and/or tokens
    /// @return messageId The message ID
    /// @dev Note if msg.value is larger than the required fee (from getFee) we accept
    /// the overpayment with no refund.
    function ccipSend(
        uint64 destinationChainSelector,
        Client.EVM2AnyMessage calldata message
    ) external payable returns (bytes32);
}
