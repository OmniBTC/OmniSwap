// SPDX-License-Identifier: Apache 2

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IWormhole.sol";

interface IWormholeBridge {
    /// @notice Send eth through portal by first wrapping it to WETH
    function wrapAndTransferETH(
        uint16 recipientChain,
        bytes32 recipient,
        uint256 arbiterFee,
        uint32 nonce
    ) external payable returns (uint64 sequence);

    /// @notice Send eth through portal by first wrapping it.
    ///
    /// @dev This type of transfer is called a "contract-controlled transfer".
    /// There are three differences from a regular token transfer:
    ///   1) Additional arbitrary payload can be attached to the message
    ///   2) Only the recipient (typically a contract) can redeem the transaction
    ///   3) The sender's address (msg.sender) is also included in the transaction payload
    ///
    /// With these three additional components, xDapps can implement cross-chain
    /// composable interactions.
    function wrapAndTransferETHWithPayload(
        uint16 recipientChain,
        bytes32 recipient,
        uint32 nonce,
        bytes memory payload
    ) external payable returns (uint64 sequence);

    /// @notice Send ERC20 token through portal.
    function transferTokens(
        address token,
        uint256 amount,
        uint16 recipientChain,
        bytes32 recipient,
        uint256 arbiterFee,
        uint32 nonce
    ) external payable returns (uint64 sequence);

    /// @notice Send ERC20 token through portal.
    ///
    /// @dev This type of transfer is called a "contract-controlled transfer".
    /// There are three differences from a regular token transfer:
    /// 1) Additional arbitrary payload can be attached to the message
    /// 2) Only the recipient (typically a contract) can redeem the transaction
    /// 3) The sender's address (msg.sender) is also included in the transaction payload
    ///
    /// With these three additional components, xDapps can implement cross-chain
    /// composable interactions.
    function transferTokensWithPayload(
        address token,
        uint256 amount,
        uint16 recipientChain,
        bytes32 recipient,
        uint32 nonce,
        bytes memory payload
    ) external payable returns (uint64 sequence);

    function governanceActionIsConsumed(bytes32 hash)
        external
        view
        returns (bool);

    function isInitialized(address impl) external view returns (bool);

    function isTransferCompleted(bytes32 hash) external view returns (bool);

    function wormhole() external view returns (IWormhole);

    function chainId() external view returns (uint16);

    function evmChainId() external view returns (uint256);

    function isFork() external view returns (bool);

    function governanceChainId() external view returns (uint16);

    function governanceContract() external view returns (bytes32);

    function wrappedAsset(uint16 tokenChainId, bytes32 tokenAddress)
        external
        view
        returns (address);

    function bridgeContracts(uint16 chainId_) external view returns (bytes32);

    function tokenImplementation() external view returns (address);

    function WETH() external view returns (IWETH);

    function outstandingBridged(address token) external view returns (uint256);

    function isWrappedAsset(address token) external view returns (bool);

    function finality() external view returns (uint8);
}

interface IWETH is IERC20 {
    function deposit() external payable;

    function withdraw(uint256 amount) external;
}
