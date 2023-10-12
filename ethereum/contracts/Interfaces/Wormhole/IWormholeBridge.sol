// SPDX-License-Identifier: Apache 2

pragma solidity ^0.8.0;

import "../IWETH.sol";
import "./IWormhole.sol";

interface IWormholeBridge {
    struct Transfer {
        // PayloadID uint8 = 1
        uint8 payloadID;
        // Amount being transferred (big-endian uint256)
        uint256 amount;
        // Address of the token. Left-zero-padded if shorter than 32 bytes
        bytes32 tokenAddress;
        // Chain ID of the token
        uint16 tokenChain;
        // Address of the recipient. Left-zero-padded if shorter than 32 bytes
        bytes32 to;
        // Chain ID of the recipient
        uint16 toChain;
        // Amount of tokens (big-endian uint256) that the user is willing to pay as relayer fee. Must be <= Amount.
        uint256 fee;
    }

    struct TransferWithPayload {
        // PayloadID uint8 = 3
        uint8 payloadID;
        // Amount being transferred (big-endian uint256)
        uint256 amount;
        // Address of the token. Left-zero-padded if shorter than 32 bytes
        bytes32 tokenAddress;
        // Chain ID of the token
        uint16 tokenChain;
        // Address of the recipient. Left-zero-padded if shorter than 32 bytes
        bytes32 to;
        // Chain ID of the recipient
        uint16 toChain;
        // Address of the message sender. Left-zero-padded if shorter than 32 bytes
        bytes32 fromAddress;
        // An arbitrary payload
        bytes payload;
    }

    struct TransferResult {
        // Chain ID of the token
        uint16 tokenChain;
        // Address of the token. Left-zero-padded if shorter than 32 bytes
        bytes32 tokenAddress;
        // Amount being transferred (big-endian uint256)
        uint256 normalizedAmount;
        // Amount of tokens (big-endian uint256) that the user is willing to pay as relayer fee. Must be <= Amount.
        uint256 normalizedArbiterFee;
        // Portion of msg.value to be paid as the core bridge fee
        uint256 wormholeFee;
    }

    struct AssetMeta {
        // PayloadID uint8 = 2
        uint8 payloadID;
        // Address of the token. Left-zero-padded if shorter than 32 bytes
        bytes32 tokenAddress;
        // Chain ID of the token
        uint16 tokenChain;
        // Number of decimals of the token (big-endian uint256)
        uint8 decimals;
        // Symbol of the token (UTF-8)
        bytes32 symbol;
        // Name of the token (UTF-8)
        bytes32 name;
    }

    struct RegisterChain {
        // Governance Header
        // module: "TokenBridge" left-padded
        bytes32 module;
        // governance action: 1
        uint8 action;
        // governance paket chain id: this or 0
        uint16 chainId;
        // Chain ID
        uint16 emitterChainID;
        // Emitter address. Left-zero-padded if shorter than 32 bytes
        bytes32 emitterAddress;
    }

    struct UpgradeContract {
        // Governance Header
        // module: "TokenBridge" left-padded
        bytes32 module;
        // governance action: 2
        uint8 action;
        // governance paket chain id
        uint16 chainId;
        // Address of the new contract
        bytes32 newContract;
    }

    struct RecoverChainId {
        // Governance Header
        // module: "TokenBridge" left-padded
        bytes32 module;
        // governance action: 3
        uint8 action;
        // EIP-155 Chain ID
        uint256 evmChainId;
        // Chain ID
        uint16 newChainId;
    }

    /*
     * @dev Parse a token transfer (payload id 1).
     *
     * @params encoded The byte array corresponding to the token transfer (not
     *                 the whole VAA, only the payload)
     */
    function parseTransfer(bytes memory encoded)
        external
        pure
        returns (Transfer memory transfer);

    /*
     * @dev Parse a token transfer with payload (payload id 3).
     *
     * @params encoded The byte array corresponding to the token transfer (not
     *                 the whole VAA, only the payload)
     */
    function parseTransferWithPayload(bytes memory encoded)
        external
        pure
        returns (TransferWithPayload memory transfer);

    /*
     *  @dev Produce a AssetMeta message for a given token
     */
    function attestToken(address tokenAddress, uint32 nonce)
        external
        payable
        returns (uint64 sequence);

    function createWrapped(bytes memory encodedVm)
        external
        returns (address token);

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

    /// @notice Complete a contract-controlled transfer of an ERC20 token.
    ///
    /// @dev The transaction can only be redeemed by the recipient, typically a
    /// contract.
    ///
    /// @param encodedVm    A byte array containing a VAA signed by the guardians.
    ///
    /// @return The byte array representing a BridgeStructs.TransferWithPayload.
    ///
    function completeTransferWithPayload(bytes memory encodedVm)
        external
        returns (bytes memory);

    /// @notice Complete a contract-controlled transfer of WETH, and unwrap to ETH.
    ///
    /// @dev The transaction can only be redeemed by the recipient, typically a
    /// contract.
    ///
    /// @param encodedVm    A byte array containing a VAA signed by the guardians.
    ///
    /// @return The byte array representing a BridgeStructs.TransferWithPayload.
    ///
    function completeTransferAndUnwrapETHWithPayload(bytes memory encodedVm)
        external
        returns (bytes memory);

    /// @notice Complete a transfer of an ERC20 token.
    ///
    /// @dev The msg.sender gets paid the associated fee.
    ///
    /// @param encodedVm A byte array containing a VAA signed by the guardians.
    ///
    function completeTransfer(bytes memory encodedVm) external;

    /// @notice Complete a transfer of WETH and unwrap to eth.
    ///
    /// @dev The msg.sender gets paid the associated fee.
    ///
    /// @param encodedVm A byte array containing a VAA signed by the guardians.
    ///
    function completeTransferAndUnwrapETH(bytes memory encodedVm) external;

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
