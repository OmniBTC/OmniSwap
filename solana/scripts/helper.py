import spl.token.instructions
from solders.pubkey import Pubkey
from typing import Union
from spl.token.instructions import get_associated_token_address
from parse import ParsedVaa, ParsedTransfer


def deriveWormholeEmitterKey(token_bridge_program_id: str):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address([b"emitter"], program_id)
    return program_address


def deriveEmitterSequenceKey(emitter: Pubkey, wormhole_program_id: str):
    program_id = Pubkey.from_string(wormhole_program_id)
    seed = [b"Sequence"]
    seed.append(bytes(emitter))
    program_address, _nonce = Pubkey.find_program_address(seed, program_id)

    return program_address


def deriveWormholeBridgeDataKey(wormhole_program_id: str):
    program_id = Pubkey.from_string(wormhole_program_id)
    program_address, _nonce = Pubkey.find_program_address([b"Bridge"], program_id)
    return program_address


def deriveFeeCollectorKey(wormhole_program_id: str):
    program_id = Pubkey.from_string(wormhole_program_id)
    program_address, _nonce = Pubkey.find_program_address(
        [b"fee_collector"], program_id
    )
    return program_address


def deriveSoFeeConfigKey(omniswap_program_id: Union[str, Pubkey]):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id
    program_address, _nonce = Pubkey.find_program_address([b"so_fee"], program_id)
    return program_address


def deriveSenderConfigKey(omniswap_program_id: Union[str, Pubkey]):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id
    program_address, _nonce = Pubkey.find_program_address([b"sender"], program_id)
    return program_address


def deriveRedeemerConfigKey(omniswap_program_id: Union[str, Pubkey]):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id
    program_address, _nonce = Pubkey.find_program_address([b"redeemer"], program_id)
    return program_address


def deriveForeignContractKey(omniswap_program_id: Union[str, Pubkey], chain: int):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [b"foreign_contract"]
    seed.append(chain.to_bytes(length=2, byteorder="little", signed=False))
    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def derivePriceManagerKey(omniswap_program_id: Union[str, Pubkey], chain: int):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [
        b"foreign_contract",
        chain.to_bytes(length=2, byteorder="little", signed=False),
        b"price_manager",
    ]

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveTokenTransferMessageKey(
    omniswap_program_id: Union[str, Pubkey], next_seq: int
):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [b"bridged"]
    seed.append(next_seq.to_bytes(length=8, byteorder="little", signed=False))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveCrossRequestKey(omniswap_program_id: Union[str, Pubkey], requester: Pubkey):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [b"request"]
    seed.append(bytes(requester))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveForeignEndPointKey(
    token_bridge_program_id: str, chain: int, foreign_contract: Pubkey
):
    assert (
        chain != 1
    ), "emitterChain == CHAIN_ID_SOLANA cannot exist as foreign token bridge emitter"

    program_id = Pubkey.from_string(token_bridge_program_id)

    seed = [chain.to_bytes(length=2, byteorder="big", signed=False)]
    seed.append(bytes(foreign_contract))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def getEmitterKeys(token_bridge_program_id: str, wormhole_program_id: str):
    emitter = deriveWormholeEmitterKey(token_bridge_program_id)
    sequence = deriveEmitterSequenceKey(emitter, wormhole_program_id)

    return emitter, sequence


def getWormholeDerivedAccounts(token_bridge_program_id: str, wormhole_program_id: str):
    token_bridge_emitter, token_bridge_sequence = getEmitterKeys(
        token_bridge_program_id, wormhole_program_id
    )
    wormhole_bridge_data = deriveWormholeBridgeDataKey(wormhole_program_id)
    wormhole_fee_collector = deriveFeeCollectorKey(wormhole_program_id)

    return (
        wormhole_bridge_data,
        token_bridge_emitter,
        wormhole_fee_collector,
        token_bridge_sequence,
    )


def deriveTokenBridgeConfigKey(token_bridge_program_id: str):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address([b"config"], program_id)
    return program_address


def deriveAuthoritySignerKey(token_bridge_program_id: str):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address(
        [b"authority_signer"], program_id
    )
    return program_address


def deriveCustodyKey(
    token_bridge_program_id: str,
    native_mint: Pubkey,
):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address(
        [bytes(native_mint)], program_id
    )
    return program_address


def deriveCustodySignerKey(token_bridge_program_id: str):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address(
        [b"custody_signer"], program_id
    )
    return program_address


def deriveMintAuthorityKey(token_bridge_program_id: str):
    program_id = Pubkey.from_string(token_bridge_program_id)
    program_address, _nonce = Pubkey.find_program_address([b"mint_signer"], program_id)
    return program_address


def getTokenBridgeDerivedAccounts(
    token_bridge_program_id: str, wormhole_program_id: str
):
    wormhole_accounts = getWormholeDerivedAccounts(
        token_bridge_program_id, wormhole_program_id
    )

    return {
        "token_bridge_config": deriveTokenBridgeConfigKey(token_bridge_program_id),
        "token_bridge_authority_signer": deriveAuthoritySignerKey(
            token_bridge_program_id
        ),
        "token_bridge_custody_signer": deriveCustodySignerKey(token_bridge_program_id),
        "token_bridge_mint_authority": deriveMintAuthorityKey(token_bridge_program_id),
        "wormhole_bridge": wormhole_accounts[0],
        "token_bridge_emitter": wormhole_accounts[1],
        "wormhole_fee_collector": wormhole_accounts[2],
        "token_bridge_sequence": wormhole_accounts[3],
    }


def deriveWrappedMintKey(
    token_bridge_program_id: str, token_chain: int, token_address: Union[str, bytes]
):
    assert (
        token_chain != 1
    ), "tokenChain == CHAIN_ID_SOLANA does not have wrapped mint key"

    if isinstance(token_address, str):
        token_address = bytes.fromhex(token_address.replace("0x", ""))

    program_id = Pubkey.from_string(token_bridge_program_id)

    seed = [b"wrapped"]
    seed.append(token_chain.to_bytes(length=2, byteorder="big", signed=False))
    seed.append(token_address)

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def derivePostedVaaKey(wormhole_program_id: str, hash: Union[str, bytes]):
    if isinstance(hash, str):
        hash = bytes.fromhex(hash.replace("0x", ""))

    program_id = Pubkey.from_string(wormhole_program_id)

    seed = [b"PostedVAA"]
    seed.append(hash)

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveGuardianSetKey(wormhole_program_id: str, index: int):
    program_id = Pubkey.from_string(wormhole_program_id)

    seed = [b"GuardianSet"]
    seed.append(index.to_bytes(length=4, byteorder="big", signed=False))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveClaimKey(
    token_bridge_program_id: str,
    emitter_address: Union[str, bytes],
    emitter_chain: int,
    sequence: int,
):
    if isinstance(emitter_address, str):
        emitter_address = bytes.fromhex(emitter_address.replace("0x", ""))

    assert len(emitter_address) == 32, "address.length != 32"

    program_id = Pubkey.from_string(token_bridge_program_id)

    seed = [emitter_address]
    seed.append(emitter_chain.to_bytes(length=2, byteorder="big", signed=False))
    seed.append(sequence.to_bytes(length=8, byteorder="big", signed=False))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveWrappedMetaKey(token_bridge_program_id: str, mint_key: Pubkey):
    program_id = Pubkey.from_string(token_bridge_program_id)

    seed = [b"meta"]
    seed.append(bytes(mint_key))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveTmpTokenAccountKey(
    omniswap_program_id: Union[str, Pubkey], wrapped_mint: Pubkey
):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [b"tmp"]
    seed.append(bytes(wrapped_mint))

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveUnwrapSolAccountKey(omniswap_program_id: Union[str, Pubkey]):
    if isinstance(omniswap_program_id, str):
        program_id = Pubkey.from_string(omniswap_program_id)
    else:
        program_id = omniswap_program_id

    seed = [b"unwrap"]

    program_address, _nonce = Pubkey.find_program_address(seed, program_id)
    return program_address


def deriveWhirlpoolOracleKey(whirlpool_program: Pubkey, whirlpool: Pubkey):
    seed = [b"oracle"]
    seed.append(bytes(whirlpool))

    program_address, _nonce = Pubkey.find_program_address(seed, whirlpool_program)
    return program_address


def getRedeemWrappedTransferAccounts(
    token_bridge_program_id: str,
    wormhole_program_id: str,
    omniswap_program_id: str,
    beneficiary: Pubkey,
    vaa: Union[str, bytes],
):
    parsed_vaa = ParsedVaa.parse(vaa)
    token_transfer = ParsedTransfer.parse(parsed_vaa.payload)

    wrapped_mint_key = deriveWrappedMintKey(
        token_bridge_program_id,
        token_transfer.token_chain,
        token_transfer.token_address,
    )

    tmp_token_key = deriveTmpTokenAccountKey(omniswap_program_id, wrapped_mint_key)

    recipient_key = Pubkey.from_bytes(token_transfer.recipient())

    recipient_token_key = get_associated_token_address(recipient_key, wrapped_mint_key)
    beneficiary_token_key = get_associated_token_address(beneficiary, wrapped_mint_key)

    redeemer_config_key = deriveRedeemerConfigKey(omniswap_program_id)
    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, parsed_vaa.emitter_chain
    )

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    return {
        "vaa": derivePostedVaaKey(wormhole_program_id, parsed_vaa.hash),
        "tmp_token_account": tmp_token_key,
        "redeemer_config": redeemer_config_key,
        "beneficiary_token_account": beneficiary_token_key,
        "fee_config": fee_config_key,
        "recipient": recipient_key,
        "recipient_token_account": recipient_token_key,
        "foreign_contract": foreign_contract_key,
        "token_bridge_config": deriveTokenBridgeConfigKey(token_bridge_program_id),
        "token_bridge_claim": deriveClaimKey(
            token_bridge_program_id,
            parsed_vaa.emitter_address,
            parsed_vaa.emitter_chain,
            parsed_vaa.sequence,
        ),
        "token_bridge_foreign_endpoint": deriveForeignEndPointKey(
            token_bridge_program_id,
            parsed_vaa.emitter_chain,
            parsed_vaa.emitter_address,
        ),
        "token_bridge_wrapped_mint": wrapped_mint_key,
        "token_bridge_wrapped_meta": deriveWrappedMetaKey(
            token_bridge_program_id, wrapped_mint_key
        ),
        "token_bridge_mint_authority": deriveMintAuthorityKey(token_bridge_program_id),
        "wormhole_program": Pubkey.from_string(wormhole_program_id),
        "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
    }


def getRedeemNativeTransferAccounts(
    token_bridge_program_id: str,
    wormhole_program_id: str,
    omniswap_program_id: str,
    beneficiary: Pubkey,
    vaa: Union[str, bytes],
    native_mint: Pubkey,
):
    parsed_vaa = ParsedVaa.parse(vaa)
    token_transfer = ParsedTransfer.parse(parsed_vaa.payload)

    tmp_token_key = deriveTmpTokenAccountKey(omniswap_program_id, native_mint)

    recipient_key = Pubkey.from_bytes(token_transfer.recipient())

    recipient_token_key = get_associated_token_address(recipient_key, native_mint)
    beneficiary_token_key = get_associated_token_address(beneficiary, native_mint)

    redeemer_config_key = deriveRedeemerConfigKey(omniswap_program_id)
    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, parsed_vaa.emitter_chain
    )

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    return {
        "fee_config": fee_config_key,
        "beneficiary_token_account": beneficiary_token_key,
        "redeemer_config": redeemer_config_key,
        "foreign_contract": foreign_contract_key,
        "recipient_token_account": recipient_token_key,
        "recipient": recipient_key,
        "tmp_token_account": tmp_token_key,
        "wormhole_program": Pubkey.from_string(wormhole_program_id),
        "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
        "token_bridge_config": deriveTokenBridgeConfigKey(token_bridge_program_id),
        "vaa": derivePostedVaaKey(wormhole_program_id, parsed_vaa.hash),
        "token_bridge_claim": deriveClaimKey(
            token_bridge_program_id,
            parsed_vaa.emitter_address,
            parsed_vaa.emitter_chain,
            parsed_vaa.sequence,
        ),
        "token_bridge_foreign_endpoint": deriveForeignEndPointKey(
            token_bridge_program_id,
            parsed_vaa.emitter_chain,
            parsed_vaa.emitter_address,
        ),
        "token_bridge_custody": deriveCustodyKey(token_bridge_program_id, native_mint),
        "token_bridge_custody_signer": deriveCustodySignerKey(token_bridge_program_id),
    }


def getSendWrappedTransferAccounts(
    token_bridge_program_id: str,
    wormhole_program_id: str,
    omniswap_program_id: str,
    recipient_chain: int,
    recipient_token: bytes,
):
    wrapped_mint_key = deriveWrappedMintKey(
        token_bridge_program_id, recipient_chain, recipient_token
    )

    tmp_token_key = deriveTmpTokenAccountKey(omniswap_program_id, wrapped_mint_key)

    send_config_key = deriveSenderConfigKey(omniswap_program_id)

    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, recipient_chain
    )

    token_bridge_emitter, token_bridge_sequence = getEmitterKeys(
        token_bridge_program_id, wormhole_program_id
    )

    bridge_data_key = deriveWormholeBridgeDataKey(wormhole_program_id)
    fee_collector_key = deriveFeeCollectorKey(wormhole_program_id)

    authority_signer_key = deriveAuthoritySignerKey(token_bridge_program_id)

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    price_manager_key = derivePriceManagerKey(omniswap_program_id, recipient_chain)

    return {
        "send_config": send_config_key,
        "fee_config": fee_config_key,
        "price_manager": price_manager_key,
        "foreign_contract": foreign_contract_key,
        "token_bridge_wrapped_mint": wrapped_mint_key,
        "tmp_token_account": tmp_token_key,
        "wormhole_program": Pubkey.from_string(wormhole_program_id),
        "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
        "token_bridge_wrapped_meta": deriveWrappedMetaKey(
            token_bridge_program_id, wrapped_mint_key
        ),
        "token_bridge_config": deriveTokenBridgeConfigKey(token_bridge_program_id),
        "token_bridge_authority_signer": authority_signer_key,
        "wormhole_bridge": bridge_data_key,
        "token_bridge_emitter": token_bridge_emitter,
        "token_bridge_sequence": token_bridge_sequence,
        "wormhole_fee_collector": fee_collector_key,
    }


def getSendNativeTransferAccounts(
    token_bridge_program_id: str,
    wormhole_program_id: str,
    omniswap_program_id: str,
    recipient_chain: int,
    native_mint_key: Pubkey,
):
    tmp_token_key = deriveTmpTokenAccountKey(omniswap_program_id, native_mint_key)

    send_config_key = deriveSenderConfigKey(omniswap_program_id)

    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, recipient_chain
    )

    token_bridge_emitter, token_bridge_sequence = getEmitterKeys(
        token_bridge_program_id, wormhole_program_id
    )

    bridge_data_key = deriveWormholeBridgeDataKey(wormhole_program_id)
    fee_collector_key = deriveFeeCollectorKey(wormhole_program_id)

    authority_signer_key = deriveAuthoritySignerKey(token_bridge_program_id)

    token_bridge_config = deriveTokenBridgeConfigKey(token_bridge_program_id)
    token_bridge_custody = deriveCustodyKey(token_bridge_program_id, native_mint_key)

    custody_signer_key = deriveCustodySignerKey(token_bridge_program_id)

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    price_manager_key = derivePriceManagerKey(omniswap_program_id, recipient_chain)

    return {
        "send_config": send_config_key,
        "fee_config": fee_config_key,
        "price_manager": price_manager_key,
        "foreign_contract": foreign_contract_key,
        "tmp_token_account": tmp_token_key,
        "wormhole_program": Pubkey.from_string(wormhole_program_id),
        "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
        "token_bridge_config": token_bridge_config,
        "token_bridge_custody": token_bridge_custody,
        "token_bridge_authority_signer": authority_signer_key,
        "token_bridge_custody_signer": custody_signer_key,
        "wormhole_bridge": bridge_data_key,
        "token_bridge_emitter": token_bridge_emitter,
        "token_bridge_sequence": token_bridge_sequence,
        "wormhole_fee_collector": fee_collector_key,
    }


def decode_address_look_up_table(data):
    # https://github.com/solana-labs/solana-web3.js/blob/c7ef49cc49ee61422a4777d439a814160f6d7ce4/packages/library-legacy/src/programs/address-lookup-table/state.ts#L23
    LOOKUP_TABLE_META_SIZE = 56

    data_len = len(data)
    assert (
        data_len > LOOKUP_TABLE_META_SIZE
        and (data_len - LOOKUP_TABLE_META_SIZE) % 32 == 0
    ), data_len

    keys = []
    i = LOOKUP_TABLE_META_SIZE
    while i < data_len:
        keys.append(Pubkey.from_bytes(data[i : i + 32]))
        i += 32

    return keys
