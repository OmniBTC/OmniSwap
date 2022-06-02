// SPDX-License-Identifier: MIT

pragma solidity 0.8.13;


interface ISo {
    /// Structs ///

    struct SoData {
        bytes32 transactionId;  //
        address sendingAssetId;
        address receivingAssetId;
        address receiver;
        uint256 destinationChainId;
        uint256 amount;
    }

    /// Events ///

    event SoTransferStarted(
        bytes32 indexed transactionId,
        string bridge,
        address sendingAssetId,
        address receivingAssetId,
        address receiver,
        uint256 amount,
        uint256 destinationChainId,
        bool hasSourceSwap,
        bool hasDestinationSwap
    );

    event SoTransferCompleted(
        bytes32 indexed transactionId,
        address receivingAssetId,
        address receiver,
        uint256 amount,
        uint256 timestamp
    );
}
