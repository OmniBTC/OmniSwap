import asyncio

import spl.token.instructions
from solana.transaction import Transaction
from solders.compute_budget import set_compute_unit_limit
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.transaction import VersionedTransaction

from omniswap.instructions import (
    so_swap_native_without_swap,
    so_swap_wrapped_without_swap,
    so_swap_native_with_whirlpool,
    so_swap_wrapped_with_whirlpool,
    wrap_sol,
)
from helper import (
    getSendWrappedTransferAccounts,
    deriveTokenTransferMessageKey,
    getSendNativeTransferAccounts,
    decode_address_look_up_table,
)
from solana_config import get_client, get_payer, get_config

from cross import (
    WormholeData,
    SoData,
    generate_random_bytes32,
    SwapData,
    padding_hex_to_bytes,
)
from custom_simulate import custom_simulate
from get_quote_config import get_whirlpool_quote_config
from post_request import post_cross_requset
from get_or_create_ata import get_or_create_associated_token_account

# DstChain
# DstChain SoDiamond
# DstChain Bridge Token(native/wrapped)
# DstChain Bridge Amount
# DstChain Swap: Bridge -> Final
# DstChain Final Token
# DstChain Final Amount
# DstChain Recipient

# SrcChain
# SrcChain SoDiamond
# SrcChain From Token
# SrcChain From Amount
# SrcChain Swap: From -> Bridge
# SrcChain Bridge Token(native/wrapped)
# SrcChain Bridge Amount
# SrcChain Sender


async def omniswap_send_wrapped_token():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(native): 32-bytes-left-padding-zero
    ERC20_BSC = "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1"
    dst_bridge_token_padding = padding_hex_to_bytes(ERC20_BSC, padding="left")
    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = bytes.fromhex(ERC20_BSC.replace("0x", ""))
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])
    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        dst_bridge_token_padding,
    )

    # SrcChain: solana-devnet
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    src_from_token = send_wrapped_accounts["token_bridge_wrapped_mint"]
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount: 1 token
    src_from_ui_amount = "1"
    src_from_amount = int(src_from_ui_amount) * 10**src_from_token_decimals
    # SrcChain Swap: From -> Bridge
    # SrcChain Bridge Token(wrapped)
    src_bridge_wrapped_token = src_from_token
    # SrcChain Bridge Amount: 1 token
    _src_bridge_amount = src_from_amount
    # SrcChain Sender
    src_bridge_token_account = Pubkey.from_string(
        "45dgjgLbiuPVYoYZXy4W3KZYLnR8suxJeVDFpdFh7aeh"
    )

    current_seq_bytes = await client.get_account_info(
        send_wrapped_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")
    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(src_from_token),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    wormhole_data = WormholeData(
        dstWormholeChainId=dst_wormhole_chain,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = so_swap_wrapped_without_swap(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_wrapped_accounts["send_config"],
            "fee_config": send_wrapped_accounts["fee_config"],
            "price_manager": send_wrapped_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": src_bridge_wrapped_token,
            "from_token_account": src_bridge_token_account,
            "tmp_token_account": send_wrapped_accounts["tmp_token_account"],
            "wormhole_program": send_wrapped_accounts["wormhole_program"],
            "token_bridge_program": send_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": send_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": send_wrapped_accounts["token_bridge_config"],
            "token_bridge_authority_signer": send_wrapped_accounts[
                "token_bridge_authority_signer"
            ],
            "wormhole_bridge": send_wrapped_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_wrapped_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_wrapped_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_wrapped_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig.value)


async def omniswap_send_native_token():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(wrapped):
    ERC20_USDC = "0x51a3cc54eA30Da607974C5D07B8502599801AC08"
    dst_bridge_token = bytes.fromhex(ERC20_USDC.replace("0x", ""))

    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = dst_bridge_token
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    src_from_token = Pubkey.from_string(USDC)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount:  1 token
    src_from_ui_amount = "1"
    src_from_amount = int(src_from_ui_amount) * 10**src_from_token_decimals
    # SrcChain Swap: From -> Bridge
    # SrcChain Bridge Token(native)
    src_bridge_native_token = src_from_token
    # SrcChain Bridge Amount
    _src_bridge_amount = src_from_amount
    # SrcChain Sender
    src_bridge_token_account = Pubkey.from_string(
        "68DjnBuZ6UtM6dGoTGhu2rqV5ZSowsPGgv2AWD1xuGB4"
    )

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        src_bridge_native_token,
    )

    current_seq_bytes = await client.get_account_info(
        send_native_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")

    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(src_from_token),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=dst_wormhole_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    data_len = len(so_data) + len(wormhole_data)
    print(f"data_len={data_len}")

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        wormhole_data=wormhole_data,
        # simulate=True
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = so_swap_native_without_swap(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "mint": src_bridge_native_token,
            "from_token_account": src_bridge_token_account,
            "tmp_token_account": send_native_accounts["tmp_token_account"],
            "wormhole_program": send_native_accounts["wormhole_program"],
            "token_bridge_program": send_native_accounts["token_bridge_program"],
            "token_bridge_config": send_native_accounts["token_bridge_config"],
            "token_bridge_custody": send_native_accounts["token_bridge_custody"],
            "token_bridge_authority_signer": send_native_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": send_native_accounts[
                "token_bridge_custody_signer"
            ],
            "wormhole_bridge": send_native_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_native_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_native_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_native_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig.value)

    # resp = await custom_simulate(client, txn, addresses=[usdc_account])
    # print(resp.value.to_json())


async def omniswap_send_native_token_with_whirlpool():
    client = get_client("devnet")
    await client.is_connected()

    # 1. swap(TEST => USDC) on solana
    # 2. bridge(USDC) to bsc

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(wrapped)
    ERC20_USDC = "0x51a3cc54eA30Da607974C5D07B8502599801AC08"
    dst_bridge_token = bytes.fromhex(ERC20_USDC.replace("0x", ""))
    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = dst_bridge_token
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    src_from_token = Pubkey.from_string(TEST)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount: 1 token
    src_from_ui_amount = "10"
    src_from_amount = int(src_from_ui_amount) * 10**src_from_token_decimals

    # SrcChain Swap(Whirlpool): From -> Bridge
    TEST_USDC_POOL = "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV"
    quote_config = get_whirlpool_quote_config(TEST_USDC_POOL, TEST, src_from_ui_amount)

    print("FromToken amount_in: ", quote_config["amount_in"])
    print("BridgeToken estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("BridgeToken min_amount_out: ", quote_config["min_amount_out"])

    # SrcChain Bridge Token(native)
    src_bridge_native_token = Pubkey.from_string(
        "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    )
    assert quote_config["token_mint_b"] == src_bridge_native_token

    # SrcChain Bridge Amount
    # SrcChain Sender

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        src_bridge_native_token,
    )

    current_seq_bytes = await client.get_account_info(
        send_native_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")
    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    assert int(quote_config["amount_in"]) == src_from_amount, src_from_amount

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(src_from_token),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    swap_data_src = SwapData.encode_compact_src(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=bytes(src_from_token),
                receivingAssetId=bytes(src_bridge_native_token),
                fromAmount=quote_config["amount_in"],
                callData=bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii"),
                swapType="Whirlpool",
                swapFuncName="swap",
                swapPath=["TEST", "USDC"],
            )
        ]
    )

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=dst_wormhole_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    data_len = len(so_data) + len(wormhole_data) + len(swap_data_src)
    print(f"data_len={data_len}")

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=303924
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = so_swap_native_with_whirlpool(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "whirlpool_program": quote_config["whirlpool_program"],
            "whirlpool_account": quote_config["whirlpool"],
            "whirlpool_token_owner_account_a": quote_config["token_owner_account_a"],
            "whirlpool_token_vault_a": quote_config["token_vault_a"],
            "whirlpool_token_owner_account_b": quote_config["token_owner_account_b"],
            "whirlpool_token_vault_b": quote_config["token_vault_b"],
            "whirlpool_tick_array0": quote_config["tick_array_0"],
            "whirlpool_tick_array1": quote_config["tick_array_1"],
            "whirlpool_tick_array2": quote_config["tick_array_2"],
            "whirlpool_oracle": quote_config["oracle"],
            "mint": src_bridge_native_token,
            "tmp_token_account": send_native_accounts["tmp_token_account"],
            "wormhole_program": send_native_accounts["wormhole_program"],
            "token_bridge_program": send_native_accounts["token_bridge_program"],
            "token_bridge_config": send_native_accounts["token_bridge_config"],
            "token_bridge_custody": send_native_accounts["token_bridge_custody"],
            "token_bridge_authority_signer": send_native_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": send_native_accounts[
                "token_bridge_custody_signer"
            ],
            "wormhole_bridge": send_native_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_native_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_native_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_native_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    # resp = await custom_simulate(
    #     client,
    #     txn,
    #     addresses=[
    #         quote_config["token_owner_account_a"],
    #         quote_config["token_owner_account_b"]
    #     ]
    # )
    # print(resp)

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_send_wrapped_token_with_whirlpool():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(native):
    ERC20_BSC = "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1"
    dst_bridge_token_padding = padding_hex_to_bytes(ERC20_BSC, padding="left")

    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = bytes.fromhex(ERC20_BSC.replace("0x", ""))
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    src_from_token = Pubkey.from_string(TEST)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount: 1 token
    src_from_ui_amount = "1"
    src_from_amount = int(src_from_ui_amount) * 10**src_from_token_decimals
    # SrcChain Swap(Whirlpool): From -> Bridge
    BSC_TEST_POOL = "AxoxjuJnpvTeqmwwjJLnuMuYLGNP1kg3orMjSuj3KBmc"
    quote_config = get_whirlpool_quote_config(BSC_TEST_POOL, TEST, src_from_ui_amount)

    print("FromToken amount_in: ", quote_config["amount_in"])
    print("BridgeToken estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("BridgeToken min_amount_out: ", quote_config["min_amount_out"])

    # SrcChain Bridge Token(wrapped)
    BSC = "xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"
    src_bridge_wrapped_token = Pubkey.from_string(BSC)
    assert quote_config["token_mint_a"] == src_bridge_wrapped_token
    # SrcChain Bridge Amount
    # SrcChain Sender

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        dst_bridge_token_padding,
    )

    current_seq_bytes = await client.get_account_info(
        send_wrapped_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")
    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    assert quote_config["amount_in"] == src_from_amount

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(src_from_token),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    swap_data_src = SwapData.encode_compact_src(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=bytes(src_from_token),
                receivingAssetId=bytes(src_bridge_wrapped_token),
                fromAmount=quote_config["amount_in"],
                callData=bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii"),
                swapType="Whirlpool",
                swapFuncName="swap",
                swapPath=["TEST", "BSC"],
            )
        ]
    )

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = so_swap_wrapped_with_whirlpool(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_wrapped_accounts["send_config"],
            "fee_config": send_wrapped_accounts["fee_config"],
            "price_manager": send_wrapped_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_wrapped_accounts["foreign_contract"],
            "whirlpool_program": quote_config["whirlpool_program"],
            "whirlpool_account": quote_config["whirlpool"],
            "whirlpool_token_owner_account_a": quote_config["token_owner_account_a"],
            "whirlpool_token_vault_a": quote_config["token_vault_a"],
            "whirlpool_token_owner_account_b": quote_config["token_owner_account_b"],
            "whirlpool_token_vault_b": quote_config["token_vault_b"],
            "whirlpool_tick_array0": quote_config["tick_array_0"],
            "whirlpool_tick_array1": quote_config["tick_array_1"],
            "whirlpool_tick_array2": quote_config["tick_array_2"],
            "whirlpool_oracle": quote_config["oracle"],
            "token_bridge_wrapped_mint": src_bridge_wrapped_token,
            "tmp_token_account": send_wrapped_accounts["tmp_token_account"],
            "wormhole_program": send_wrapped_accounts["wormhole_program"],
            "token_bridge_program": send_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": send_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": send_wrapped_accounts["token_bridge_config"],
            "token_bridge_authority_signer": send_wrapped_accounts[
                "token_bridge_authority_signer"
            ],
            "wormhole_bridge": send_wrapped_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_wrapped_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_wrapped_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_wrapped_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig.value)


async def omniswap_send_native_token_sol():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(wrapped):
    ERC20_SOL = "0x30f19eBba919954FDc020B8A20aEF13ab5e02Af0"
    dst_bridge_token = bytes.fromhex(ERC20_SOL.replace("0x", ""))

    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = dst_bridge_token
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    WSOL = "So11111111111111111111111111111111111111112"
    src_from_token = Pubkey.from_string(WSOL)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount:  1 token
    src_from_ui_amount = "1"
    src_from_amount = int(src_from_ui_amount) * 10**src_from_token_decimals
    # SrcChain Swap: From -> Bridge
    # SrcChain Bridge Token(native)
    src_bridge_native_token = src_from_token
    # SrcChain Bridge Amount
    _src_bridge_amount = src_from_amount
    # SrcChain Sender
    src_bridge_token_account = Pubkey.from_string(
        "6keZXUa7n3hoHkboSnzpGETANuwY43zWZC3FGrCPN1Gh"
    )

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        src_bridge_native_token,
    )

    current_seq_bytes = await client.get_account_info(
        send_native_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")

    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(src_from_token),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=dst_wormhole_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        wormhole_data=wormhole_data,
        # simulate=True
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(300_000)

    ix1 = wrap_sol(
        args={"amount_to_be_wrapped": src_from_amount},
        accounts={
            "payer": payer.pubkey(),
            "wrap_sol_account": src_bridge_token_account,
            "wsol_mint": Pubkey.from_string(
                "So11111111111111111111111111111111111111112"
            ),
        },
    )

    ix2 = so_swap_native_without_swap(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "mint": src_bridge_native_token,
            "from_token_account": src_bridge_token_account,
            "tmp_token_account": send_native_accounts["tmp_token_account"],
            "wormhole_program": send_native_accounts["wormhole_program"],
            "token_bridge_program": send_native_accounts["token_bridge_program"],
            "token_bridge_config": send_native_accounts["token_bridge_config"],
            "token_bridge_custody": send_native_accounts["token_bridge_custody"],
            "token_bridge_authority_signer": send_native_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": send_native_accounts[
                "token_bridge_custody_signer"
            ],
            "wormhole_bridge": send_native_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_native_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_native_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_native_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1, ix2],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig.value)


async def omniswap_send_sol_wsol_usdc():
    client = get_client("devnet")
    await client.is_connected()

    # 1. wrap(SOL -> WSOL)
    # 1. swap(WSOL => USDC)
    # 2. bridge(USDC) to bsc

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(wrapped)
    ERC20_USDC = "0x51a3cc54eA30Da607974C5D07B8502599801AC08"
    dst_bridge_token = bytes.fromhex(ERC20_USDC.replace("0x", ""))
    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = dst_bridge_token
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    SOL = Pubkey.from_string("11111111111111111111111111111111")
    WSOL = "So11111111111111111111111111111111111111112"
    src_from_token = Pubkey.from_string(WSOL)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount:
    src_from_ui_amount = "0.0001"
    src_from_amount = int(float(src_from_ui_amount) * 10**src_from_token_decimals)

    # SrcChain Swap(Whirlpool): From -> Bridge
    WSOL_USDC_POOL = "3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd"
    quote_config = get_whirlpool_quote_config(WSOL_USDC_POOL, WSOL, src_from_ui_amount)

    print("FromToken amount_in: ", quote_config["amount_in"])
    print("BridgeToken estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("BridgeToken min_amount_out: ", quote_config["min_amount_out"])

    # SrcChain Bridge Token(native)
    src_bridge_native_token = Pubkey.from_string(
        "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    )
    assert quote_config["token_mint_b"] == src_bridge_native_token

    # SrcChain Bridge Amount
    # SrcChain Sender

    # get_whirlpool_quote_config return some rand wsol account
    # for our contract, we need the specify wsol account to manage proxy swap
    replaced_wsol_account = Pubkey.from_string(
        "6keZXUa7n3hoHkboSnzpGETANuwY43zWZC3FGrCPN1Gh"
    )
    if quote_config["token_mint_a"] == src_from_token:
        quote_config["token_owner_account_a"] = replaced_wsol_account
    elif quote_config["token_mint_b"] == src_from_token:
        quote_config["token_owner_account_b"] = replaced_wsol_account
    else:
        print("no replace proxy wsol account")

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        src_bridge_native_token,
    )

    current_seq_bytes = await client.get_account_info(
        send_native_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")
    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    assert int(quote_config["amount_in"]) == src_from_amount, src_from_amount

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(SOL),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    swap_data_src = SwapData.encode_compact_src(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=bytes(src_from_token),
                receivingAssetId=bytes(src_bridge_native_token),
                fromAmount=quote_config["amount_in"],
                callData=bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii"),
                swapType="Whirlpool",
                swapFuncName="swap",
                swapPath=["WSOL", "USDC"],
            )
        ]
    )

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=dst_wormhole_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
        # simulate=True,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=303924
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = wrap_sol(
        args={"amount_to_be_wrapped": src_from_amount},
        accounts={
            "payer": payer.pubkey(),
            "wrap_sol_account": replaced_wsol_account,
            "wsol_mint": Pubkey.from_string(
                "So11111111111111111111111111111111111111112"
            ),
        },
    )

    ix2 = so_swap_native_with_whirlpool(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "whirlpool_program": quote_config["whirlpool_program"],
            "whirlpool_account": quote_config["whirlpool"],
            "whirlpool_token_owner_account_a": quote_config["token_owner_account_a"],
            "whirlpool_token_vault_a": quote_config["token_vault_a"],
            "whirlpool_token_owner_account_b": quote_config["token_owner_account_b"],
            "whirlpool_token_vault_b": quote_config["token_vault_b"],
            "whirlpool_tick_array0": quote_config["tick_array_0"],
            "whirlpool_tick_array1": quote_config["tick_array_1"],
            "whirlpool_tick_array2": quote_config["tick_array_2"],
            "whirlpool_oracle": quote_config["oracle"],
            "mint": src_bridge_native_token,
            "tmp_token_account": send_native_accounts["tmp_token_account"],
            "wormhole_program": send_native_accounts["wormhole_program"],
            "token_bridge_program": send_native_accounts["token_bridge_program"],
            "token_bridge_config": send_native_accounts["token_bridge_config"],
            "token_bridge_custody": send_native_accounts["token_bridge_custody"],
            "token_bridge_authority_signer": send_native_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": send_native_accounts[
                "token_bridge_custody_signer"
            ],
            "wormhole_bridge": send_native_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_native_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_native_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_native_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1, ix2],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_send_sol_wsol_bsc():
    client = get_client("devnet")
    await client.is_connected()

    # 1. wrap(SOL -> WSOL)
    # 1. swap(WSOL => BSC)
    # 2. bridge(BSC) to bsc

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # DstChain: bsc-testnet
    dst_omnibtc_chain = 30003
    dst_wormhole_chain = 4
    # DstChain SoDiamond: 32-bytes-left-padding-zero
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # DstChain Bridge Token(native):
    ERC20_BSC = "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1"
    dst_bridge_token_padding = padding_hex_to_bytes(ERC20_BSC, padding="left")

    # DstChain Bridge Amount
    # DstChain Swap: Bridge -> Final
    # DstChain Final Token
    dst_final_token = bytes.fromhex(ERC20_BSC.replace("0x", ""))
    # DstChain Final Amount
    # DstChain Recipient
    dst_recipient = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    # SrcChain
    src_omnibtc_chain = 30006
    # SrcChain SoDiamond
    # SrcChain From Token
    SOL = Pubkey.from_string("11111111111111111111111111111111")
    WSOL = "So11111111111111111111111111111111111111112"
    src_from_token = Pubkey.from_string(WSOL)
    resp = await client.get_account_info_json_parsed(src_from_token)
    src_from_token_decimals = resp.value.data.parsed["info"]["decimals"]
    # SrcChain From Amount: 1 token
    src_from_ui_amount = "0.0001"
    src_from_amount = int(float(src_from_ui_amount) * 10**src_from_token_decimals)

    # SrcChain Swap(Whirlpool): From -> Bridge
    WSOL_BSC_POOL = "6TLSV3E9aTNzJtY4DejLdhGb4wkTfM65gA3cwMESFrpY"
    quote_config = get_whirlpool_quote_config(WSOL_BSC_POOL, WSOL, src_from_ui_amount)

    print("FromToken amount_in: ", quote_config["amount_in"])
    print("BridgeToken estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("BridgeToken min_amount_out: ", quote_config["min_amount_out"])

    # SrcChain Bridge Token(wrapped)
    BSC = "xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"
    src_bridge_wrapped_token = Pubkey.from_string(BSC)
    assert quote_config["token_mint_b"] == src_bridge_wrapped_token
    # SrcChain Bridge Amount
    # SrcChain Sender

    # get_whirlpool_quote_config return some rand wsol account
    # for our contract, we need the specify wsol account to manage proxy swap
    replaced_wsol_account = Pubkey.from_string(
        "6keZXUa7n3hoHkboSnzpGETANuwY43zWZC3FGrCPN1Gh"
    )
    if quote_config["token_mint_a"] == src_from_token:
        quote_config["token_owner_account_a"] = replaced_wsol_account
    elif quote_config["token_mint_b"] == src_from_token:
        quote_config["token_owner_account_b"] = replaced_wsol_account
    else:
        print("no replace proxy wsol account")

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        dst_wormhole_chain,
        dst_bridge_token_padding,
    )

    current_seq_bytes = await client.get_account_info(
        send_wrapped_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")
    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(omniswap_program_id, next_seq)

    assert quote_config["amount_in"] == src_from_amount

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=dst_recipient,
        sourceChainId=src_omnibtc_chain,
        sendingAssetId=bytes(SOL),
        destinationChainId=dst_omnibtc_chain,
        receivingAssetId=dst_final_token,
        amount=src_from_amount,
    ).encode_compact()

    swap_data_src = SwapData.encode_compact_src(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=bytes(src_from_token),
                receivingAssetId=bytes(src_bridge_wrapped_token),
                fromAmount=quote_config["amount_in"],
                callData=bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii"),
                swapType="Whirlpool",
                swapFuncName="swap",
                swapPath=["WSOL", "BSC"],
            )
        ]
    )

    # This value will be automatically corrected
    # on the chain when post_request is called
    default_wormhole_fee = 0
    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=default_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_compact()

    request_key, _total_fee = await post_cross_requset(
        dst_wormhole_chain,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(1_200_000)

    ix1 = wrap_sol(
        args={"amount_to_be_wrapped": src_from_amount},
        accounts={
            "payer": payer.pubkey(),
            "wrap_sol_account": replaced_wsol_account,
            "wsol_mint": Pubkey.from_string(
                "So11111111111111111111111111111111111111112"
            ),
        },
    )

    ix2 = so_swap_wrapped_with_whirlpool(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_wrapped_accounts["send_config"],
            "fee_config": send_wrapped_accounts["fee_config"],
            "price_manager": send_wrapped_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_wrapped_accounts["foreign_contract"],
            "whirlpool_program": quote_config["whirlpool_program"],
            "whirlpool_account": quote_config["whirlpool"],
            "whirlpool_token_owner_account_a": quote_config["token_owner_account_a"],
            "whirlpool_token_vault_a": quote_config["token_vault_a"],
            "whirlpool_token_owner_account_b": quote_config["token_owner_account_b"],
            "whirlpool_token_vault_b": quote_config["token_vault_b"],
            "whirlpool_tick_array0": quote_config["tick_array_0"],
            "whirlpool_tick_array1": quote_config["tick_array_1"],
            "whirlpool_tick_array2": quote_config["tick_array_2"],
            "whirlpool_oracle": quote_config["oracle"],
            "token_bridge_wrapped_mint": src_bridge_wrapped_token,
            "tmp_token_account": send_wrapped_accounts["tmp_token_account"],
            "wormhole_program": send_wrapped_accounts["wormhole_program"],
            "token_bridge_program": send_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": send_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": send_wrapped_accounts["token_bridge_config"],
            "token_bridge_authority_signer": send_wrapped_accounts[
                "token_bridge_authority_signer"
            ],
            "wormhole_bridge": send_wrapped_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_wrapped_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_wrapped_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_wrapped_accounts["wormhole_fee_collector"],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix0, ix1, ix2],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig.value)


# asyncio.run(omniswap_send_native_token())
# asyncio.run(omniswap_send_wrapped_token())
# asyncio.run(omniswap_send_native_token_with_whirlpool())
asyncio.run(omniswap_send_sol_wsol_bsc())
