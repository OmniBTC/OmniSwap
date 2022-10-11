// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;

interface ISo {
    /// Structs ///

    struct SoData {
        bytes32 transactionId; // unique identification id
        address payable receiver; // token receiving account
        uint16 sourceChainId; // source chain id
        address sendingAssetId; // The starting token address of the source chain
        uint16 destinationChainId; // destination chain id
        address receivingAssetId; // The final token address of the destination chain
        uint256 amount; // User enters amount
    }

    struct NormalizedSoData {
        bytes transactionId; // unique identification id
        bytes receiver; // token receiving account
        uint16 sourceChainId; // source chain id
        bytes sendingAssetId; // The starting token address of the source chain
        uint16 destinationChainId; // destination chain id
        bytes receivingAssetId; // The final token address of the destination chain
        uint256 amount; // User enters amount
    }

    /// Events ///

    event SoTransferStarted(
        bytes32 indexed transactionId,
        string bridge,
        bool hasSourceSwap,
        bool hasDestinationSwap,
        SoData soData
    );

    event SoTransferFailed(
        bytes32 indexed transactionId,
        string revertReason,
        bytes otherReason,
        SoData soData
    );

    event SoTransferCompleted(
        bytes32 indexed transactionId,
        address receivingAssetId,
        address receiver,
        uint256 receiveAmount,
        uint256 timestamp,
        SoData soData
    );
}
