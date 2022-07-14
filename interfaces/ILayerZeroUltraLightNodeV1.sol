// SPDX-License-Identifier: BUSL-1.1

pragma solidity >=0.7.0;

interface ILayerZeroUltraLightNodeV1 {
    struct ApplicationConfiguration {
        uint16 inboundProofLibraryVersion;
        uint64 inboundBlockConfirmations;
        address relayer;
        uint16 outboundProofType;
        uint64 outboundBlockConfirmations;
        address oracle;
    }

    event AppConfigUpdated(address userApplication, uint configType, bytes newConfig);
    event AddInboundProofLibraryForChain(uint16 chainId, address lib);
    event EnableSupportedOutboundProof(uint16 chainId, uint16 proofType);
    event HashReceived(uint16 srcChainId, address oracle, uint confirmations, bytes32 blockhash);
    event Packet(uint16 chainId, bytes payload);
    event RelayerParams(uint16 chainId, uint64 nonce, uint16 outboundProofType, bytes adapterParams);
    event SetChainAddressSize(uint16 chainId, uint size);
    event SetDefaultConfigForChainId(uint16 chainId, uint16 inboundProofLib, uint64 inboundBlockConfirm, address relayer, uint16 outboundProofType, uint16 outboundBlockConfirm, address oracle);
    event SetDefaultAdapterParamsForChainId(uint16 chainId, uint16 proofType, bytes adapterParams);
    event SetLayerZeroToken(address tokenAddress);
    event SetRelayerFeeContract(address relayerFeeContract);
    event SetRemoteUln(uint16 chainId, bytes32 uln);
    event SetTreasury(address treasuryAddress);
    event WithdrawZRO(address _msgSender, address _to, uint _amount);
    event WithdrawNative(uint8 _type, address _owner, address _msgSender, address _to, uint _amount);

    // a Relayer can execute the validateTransactionProof()
    function validateTransactionProof(uint16 _srcChainId, address _dstAddress, uint _gasLimit, bytes32 _lookupHash, bytes calldata _transactionProof) external;

    // an Oracle delivers the block data using updateHash()
    function updateHash(uint16 _remoteChainId, bytes32 _lookupHash, uint _confirmations, bytes32 _data) external;

    // can only withdraw the receivable of the msg.sender
    function withdrawNative(uint8 _type, address _owner, address payable _to, uint _amount) external;

    function withdrawZRO(address _to, uint _amount) external;

    // view functions
    function oracleQuotedAmount(address _oracle) external view returns (uint);

    function relayerQuotedAmount(address _relayer) external view returns (uint);

    function getAppConfig(uint16 _chainId, address userApplicationAddress) external view returns (ApplicationConfiguration memory);
}
