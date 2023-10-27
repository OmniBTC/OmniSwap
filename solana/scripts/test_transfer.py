import asyncio

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
)
from helper import (
    getSendWrappedTransferAccounts,
    deriveTokenTransferMessageKey,
    getSendNativeTransferAccounts,
    decode_address_look_up_table,
)
from config import get_client, get_payer, get_config

from cross import WormholeData, SoData, generate_random_bytes32, SwapData
from custom_simulate import custom_simulate
from get_quote_config import get_test_usdc_quote_config
from post_request import post_cross_requset


async def omniswap_send_wrapped_token():
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]

    # bsc-testnet
    recipient_chain = 4
    # wrapper token
    token_on_solana = bytes(Pubkey.from_string("todo"))
    token_on_bsc = bytes.fromhex("todo")
    # wrapper token account
    wrapper_token_account = Pubkey.from_string("todo")
    # send amount(decimals=8), 1 coin
    amount = 100000000
    # recipient
    recipient_address = bytes.fromhex("todo")

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
        sendingAssetId=token_on_solana,
        destinationChainId=4,
        receivingAssetId=token_on_bsc,
        amount=amount,
    ).encode_normalized()

    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=0,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key = await post_cross_requset(
        so_data=so_data, wormhole_data=wormhole_data, simulate=True
    )

    ix = so_swap_wrapped_without_swap(
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

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)


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

    wormhole_data = WormholeData(
        dstWormholeChainId=wormhole_dst_chain,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=716184,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key = await post_cross_requset(
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
    omnibtc_chainid_dst = config["dst_chain"]["bsc-test"]["omnibtc_chainid"]
    wormhole_dst_chain = config["dst_chain"]["bsc-test"]["chainid"]

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

    wormhole_data = WormholeData(
        dstWormholeChainId=wormhole_dst_chain,
        dstMaxGasPriceInWeiForRelayer=100000,
        wormholeFee=716184,
        dstSoDiamond=dst_so_diamond_padding,
    ).encode_normalized()

    request_key = await post_cross_requset(
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

    await client.close()


async def omniswap_send_wrapped_token_with_whirlpool():
    quote_config = get_test_usdc_quote_config(
        "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU", "10"
    )

    print(quote_config)


asyncio.run(omniswap_send_native_token())
