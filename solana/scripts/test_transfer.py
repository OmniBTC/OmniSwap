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

from cross import WormholeData, SoData, generate_random_bytes32, SwapData
from custom_simulate import custom_simulate
from get_quote_config import get_test_usdc_quote_config, get_bsc_test_quote_config
from post_request import post_cross_requset
from get_or_create_ata import get_or_create_associated_token_account


async def omniswap_send_wrapped_token():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    # bsc-testnet
    recipient_chain = 4
    # wrapped token
    token_on_bsc = bytes.fromhex(
        "0000000000000000000000008CE306D8A34C99b23d3054072ba7fc013684e8a1"
    )

    # wrapper token account
    wrapper_token_account = Pubkey.from_string(
        "45dgjgLbiuPVYoYZXy4W3KZYLnR8suxJeVDFpdFh7aeh"
    )
    # send amount(decimals=8), 1 coin
    amount = 100000000
    # recipient
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")

    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        recipient_chain,
        token_on_bsc,
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
        receiver=recipient_address,
        sourceChainId=1,
        sendingAssetId=bytes(send_wrapped_accounts["token_bridge_wrapped_mint"]),
        destinationChainId=4,
        receivingAssetId=token_on_bsc,
        amount=amount,
    ).encode_normalized()

    # This value will be automatically corrected
    # on the chain when post_request is called
    defult_wormhole_fee = 0
    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=defult_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key, _total_fee = await post_cross_requset(
        4,
        so_data=so_data,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(300_000)

    ix1 = so_swap_wrapped_without_swap(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_wrapped_accounts["send_config"],
            "fee_config": send_wrapped_accounts["fee_config"],
            "price_manager": send_wrapped_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": send_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "from_token_account": wrapper_token_account,
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

    omnibtc_chainid_src = config["omnibtc_chainid"]
    omnibtc_chainid_dst = config["wormhole"]["dst_chain"]["bsc-test"]["omnibtc_chainid"]
    wormhole_dst_chain = config["wormhole"]["dst_chain"]["bsc-test"]["chainid"]

    usdc_mint = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
    usdc_token_on_solana = bytes(usdc_mint)
    # usdc account
    usdc_account = Pubkey.from_string("68DjnBuZ6UtM6dGoTGhu2rqV5ZSowsPGgv2AWD1xuGB4")
    # send 1 usdc
    amount = 1000000
    # recipient
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")
    usdc_token_on_bsc = bytes.fromhex("51a3cc54eA30Da607974C5D07B8502599801AC08")
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        wormhole_dst_chain,
        usdc_mint,
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
        receiver=recipient_address,
        sourceChainId=omnibtc_chainid_src,
        sendingAssetId=usdc_token_on_solana,
        destinationChainId=omnibtc_chainid_dst,
        receivingAssetId=usdc_token_on_bsc,
        amount=amount,
    ).encode_normalized()

    # This value will be automatically corrected
    # on the chain when post_request is called
    defult_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=wormhole_dst_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=defult_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key, _total_fee = await post_cross_requset(
        wormhole_dst_chain,
        so_data=so_data,
        wormhole_data=wormhole_data,
        # simulate=True
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(300_000)

    ix1 = so_swap_native_without_swap(
        accounts={
            "payer": payer.pubkey(),
            "request": request_key,
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "mint": usdc_mint,
            "from_token_account": usdc_account,
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

    omnibtc_chainid_src = config["omnibtc_chainid"]
    omnibtc_chainid_dst = config["wormhole"]["dst_chain"]["bsc-test"]["omnibtc_chainid"]
    wormhole_dst_chain = config["wormhole"]["dst_chain"]["bsc-test"]["chainid"]

    # TEST is tokenA
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    # USDC is tokenB
    USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

    # 10.1 TEST
    ui_amount = "10.1"
    quote_config = get_test_usdc_quote_config(TEST, ui_amount)

    print("TEST amount_in: ", quote_config["amount_in"])
    print("USDC estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("USDC min_amount_out: ", quote_config["min_amount_out"])

    usdc_mint = Pubkey.from_string(USDC)
    sendingAssetId = bytes(Pubkey.from_string(TEST))

    # recipient
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")
    usdc_token_on_bsc = bytes.fromhex("51a3cc54eA30Da607974C5D07B8502599801AC08")
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        wormhole_dst_chain,
        usdc_mint,
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
        receiver=recipient_address,
        sourceChainId=omnibtc_chainid_src,
        sendingAssetId=sendingAssetId,
        destinationChainId=omnibtc_chainid_dst,
        receivingAssetId=usdc_token_on_bsc,
        amount=quote_config["amount_in"],
    ).encode_normalized()

    swap_data_src = SwapData.encode_normalized(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=sendingAssetId,
                receivingAssetId=bytes(Pubkey.from_string(USDC)),
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
    defult_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=wormhole_dst_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=defult_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key, _total_fee = await post_cross_requset(
        wormhole_dst_chain,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
        # simulate=True,
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
            "mint": usdc_mint,
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

    # TEST is tokenB
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    # 5 TEST
    ui_amount = "5"
    quote_config = get_bsc_test_quote_config(TEST, ui_amount)

    print("TEST amount_in: ", quote_config["amount_in"])
    print("BSC estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("BSC min_amount_out: ", quote_config["min_amount_out"])

    sendingAssetId = bytes(Pubkey.from_string(TEST))

    # recipient
    recipient_chain = 4
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")
    token_on_bsc = bytes.fromhex("8CE306D8A34C99b23d3054072ba7fc013684e8a1")
    token_on_bsc_padding = bytes.fromhex(
        "0000000000000000000000008CE306D8A34C99b23d3054072ba7fc013684e8a1"
    )
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        recipient_chain,
        token_on_bsc_padding,
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
        receiver=recipient_address,
        sourceChainId=1,
        sendingAssetId=bytes(send_wrapped_accounts["token_bridge_wrapped_mint"]),
        destinationChainId=4,
        receivingAssetId=token_on_bsc,
        amount=quote_config["amount_in"],
    ).encode_normalized()

    swap_data_src = SwapData.encode_normalized(
        [
            SwapData(
                callTo=bytes(quote_config["whirlpool"]),
                approveTo=bytes(quote_config["whirlpool"]),
                sendingAssetId=sendingAssetId,
                receivingAssetId=bytes(
                    send_wrapped_accounts["token_bridge_wrapped_mint"]
                ),
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
    defult_wormhole_fee = 0
    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=defult_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key, _total_fee = await post_cross_requset(
        4,
        so_data=so_data,
        swap_data_src=swap_data_src,
        wormhole_data=wormhole_data,
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(1200000)

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
            "token_bridge_wrapped_mint": send_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
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

    omnibtc_chainid_src = config["omnibtc_chainid"]
    omnibtc_chainid_dst = config["wormhole"]["dst_chain"]["bsc-test"]["omnibtc_chainid"]
    wormhole_dst_chain = config["wormhole"]["dst_chain"]["bsc-test"]["chainid"]

    wsol_mint = Pubkey.from_string("So11111111111111111111111111111111111111112")
    wsol_on_solana = bytes(wsol_mint)
    # wsol account
    wsol_account = Pubkey.from_string("6keZXUa7n3hoHkboSnzpGETANuwY43zWZC3FGrCPN1Gh")
    # send 1 wsol
    bridge_amount = 1_000_000_000
    # recipient
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")
    wsol_token_on_bsc = bytes.fromhex("30f19eBba919954FDc020B8A20aEF13ab5e02Af0")
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        wormhole_dst_chain,
        wsol_mint,
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
        receiver=recipient_address,
        sourceChainId=omnibtc_chainid_src,
        sendingAssetId=wsol_on_solana,
        destinationChainId=omnibtc_chainid_dst,
        receivingAssetId=wsol_token_on_bsc,
        amount=bridge_amount,
    ).encode_normalized()

    # This value will be automatically corrected
    # on the chain when post_request is called
    defult_wormhole_fee = 0
    # 10 Gwei
    dst_gas_price = 10_000_000_000
    wormhole_data = WormholeData(
        dstWormholeChainId=wormhole_dst_chain,
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=defult_wormhole_fee,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key, _total_fee = await post_cross_requset(
        wormhole_dst_chain,
        so_data=so_data,
        wormhole_data=wormhole_data,
        # simulate=True
    )

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=248782
    ix0 = set_compute_unit_limit(300_000)

    ix1 = wrap_sol(
        args={"amount_to_be_wrapped": bridge_amount},
        accounts={
            "payer": payer.pubkey(),
            "wrap_sol_account": wsol_account,
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
            "mint": wsol_mint,
            "from_token_account": wsol_account,
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


asyncio.run(omniswap_send_native_token_sol())
