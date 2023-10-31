import asyncio
from solana.transaction import Transaction
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit
from solders.transaction import VersionedTransaction
from spl.token.instructions import get_associated_token_address

from omniswap.instructions import (
    complete_so_swap_native_without_swap,
    complete_so_swap_wrapped_without_swap,
    complete_so_swap_native_with_whirlpool,
    complete_so_swap_wrapped_with_whirlpool,
)
from helper import (
    getRedeemWrappedTransferAccounts,
    getRedeemNativeTransferAccounts,
    decode_address_look_up_table,
    deriveUnwrapSolAccountKey,
)
from solana_config import get_client, get_config, get_proxy
from parse import ParsedVaa, ParsedTransfer
from get_quote_config import get_test_usdc_quote_config, get_bsc_test_quote_config
from get_or_create_ata import get_or_create_associated_token_account


def denormalize_amount(amount: int, mint_decimals: int):
    MAX_WRAPPED_ASSET_DECIMALS = 8

    amount_adjustment = 1
    if mint_decimals > MAX_WRAPPED_ASSET_DECIMALS:
        amount_adjustment = 10 ** (mint_decimals - MAX_WRAPPED_ASSET_DECIMALS)

    return amount * amount_adjustment


def to_ui_amount(amount: int, mint_decimals: int):
    return str(amount / (10**mint_decimals))


async def omniswap_redeem_wrapped_token(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    parsed_vaa = ParsedVaa.parse(vaa)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_wrapped_accounts = getRedeemWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
    )

    beneficiary_token_account = get_or_create_associated_token_account(
        str(redeem_wrapped_accounts["token_bridge_wrapped_mint"]), config["beneficiary"]
    )
    print(f"beneficiary_token_account={beneficiary_token_account}")

    recipient_token_account = get_or_create_associated_token_account(
        str(redeem_wrapped_accounts["token_bridge_wrapped_mint"]),
        str(redeem_wrapped_accounts["recipient"]),
    )
    print(f"recipient_token_account={recipient_token_account}")

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    ix0 = set_compute_unit_limit(300_000)

    ix1 = complete_so_swap_wrapped_without_swap(
        args={"vaa_hash": parsed_vaa.hash, "skip_verify_soswap_message": False},
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_wrapped_accounts["redeemer_config"],
            "fee_config": redeem_wrapped_accounts["fee_config"],
            "beneficiary_token_account": beneficiary_token_account,
            "foreign_contract": redeem_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": redeem_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "recipient_token_account": recipient_token_account,
            "tmp_token_account": redeem_wrapped_accounts["tmp_token_account"],
            "wormhole_program": redeem_wrapped_accounts["wormhole_program"],
            "token_bridge_program": redeem_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": redeem_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": redeem_wrapped_accounts["token_bridge_config"],
            "vaa": redeem_wrapped_accounts["vaa"],
            "token_bridge_claim": redeem_wrapped_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_wrapped_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_mint_authority": redeem_wrapped_accounts[
                "token_bridge_mint_authority"
            ],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer_proxy.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer_proxy])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_redeem_wrapped_token_with_whirlpool(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    bridge_token = Pubkey.from_bytes(parsed_transfer.bridge_token())
    dst_token = Pubkey.from_bytes(parsed_transfer.dst_token())

    # wrapped-bsc decimals=8
    # todo: get decimals
    bridge_token_amount = denormalize_amount(parsed_transfer.amount, 8)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_wrapped_accounts = getRedeemWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
    )

    beneficiary_bridge_token_account = get_or_create_associated_token_account(
        str(bridge_token), config["beneficiary"]
    )
    print(f"beneficiary_bridge_token_account={beneficiary_bridge_token_account}")

    recipient_bridge_token_account = get_or_create_associated_token_account(
        str(bridge_token),
        str(redeem_wrapped_accounts["recipient"]),
    )
    print(f"recipient_bridge_token_account={recipient_bridge_token_account}")

    recipient_dst_token_account = get_or_create_associated_token_account(
        str(dst_token),
        str(redeem_wrapped_accounts["recipient"]),
    )
    print(f"recipient_dst_token_account={recipient_dst_token_account}")

    ui_amount = to_ui_amount(bridge_token_amount, 8)
    quote_config = get_bsc_test_quote_config(str(bridge_token), ui_amount)

    print("BSC amount_in: ", quote_config["amount_in"])
    print("TEST estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("TEST min_amount_out: ", quote_config["min_amount_out"])

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    ix0 = set_compute_unit_limit(300_000)

    ix1 = complete_so_swap_wrapped_with_whirlpool(
        args={"vaa_hash": parsed_vaa.hash},
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_wrapped_accounts["redeemer_config"],
            "fee_config": redeem_wrapped_accounts["fee_config"],
            "beneficiary_token_account": beneficiary_bridge_token_account,
            "foreign_contract": redeem_wrapped_accounts["foreign_contract"],
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
            "token_bridge_wrapped_mint": redeem_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "recipient_token_account": recipient_dst_token_account,
            "recipient_bridge_token_account": recipient_bridge_token_account,
            "tmp_token_account": redeem_wrapped_accounts["tmp_token_account"],
            "wormhole_program": redeem_wrapped_accounts["wormhole_program"],
            "token_bridge_program": redeem_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": redeem_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": redeem_wrapped_accounts["token_bridge_config"],
            "vaa": redeem_wrapped_accounts["vaa"],
            "token_bridge_claim": redeem_wrapped_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_wrapped_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_mint_authority": redeem_wrapped_accounts[
                "token_bridge_mint_authority"
            ],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer_proxy.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer_proxy])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_redeem_wrapped_token_skip_verify(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    parsed_vaa = ParsedVaa.parse(vaa)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_wrapped_accounts = getRedeemWrappedTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
    )

    beneficiary_token_account = get_or_create_associated_token_account(
        str(redeem_wrapped_accounts["token_bridge_wrapped_mint"]), config["beneficiary"]
    )
    print(f"beneficiary_token_account={beneficiary_token_account}")

    recipient_token_account = get_or_create_associated_token_account(
        str(redeem_wrapped_accounts["token_bridge_wrapped_mint"]),
        str(redeem_wrapped_accounts["recipient"]),
    )
    print(f"recipient_token_account={recipient_token_account}")

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    ix0 = set_compute_unit_limit(300_000)

    ix1 = complete_so_swap_wrapped_without_swap(
        args={"vaa_hash": parsed_vaa.hash, "skip_verify_soswap_message": False},
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_wrapped_accounts["redeemer_config"],
            "fee_config": redeem_wrapped_accounts["fee_config"],
            "beneficiary_token_account": beneficiary_token_account,
            "foreign_contract": redeem_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": redeem_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "recipient_token_account": recipient_token_account,
            "tmp_token_account": redeem_wrapped_accounts["tmp_token_account"],
            "wormhole_program": redeem_wrapped_accounts["wormhole_program"],
            "token_bridge_program": redeem_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": redeem_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": redeem_wrapped_accounts["token_bridge_config"],
            "vaa": redeem_wrapped_accounts["vaa"],
            "token_bridge_claim": redeem_wrapped_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_wrapped_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_mint_authority": redeem_wrapped_accounts[
                "token_bridge_mint_authority"
            ],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer_proxy.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer_proxy])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_redeem_native_token(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    bridge_token_mint = Pubkey.from_bytes(parsed_transfer.dst_token())
    skip_verify_soswap_message = False
    if (
        not skip_verify_soswap_message
        and str(bridge_token_mint) == "11111111111111111111111111111111"
    ):
        bridge_token_mint = Pubkey.from_string(
            "So11111111111111111111111111111111111111112"
        )
        unwrap_sol_account = deriveUnwrapSolAccountKey(omniswap_program_id)
        wsol_mint = Pubkey.from_string("So11111111111111111111111111111111111111112")
        recipient = Pubkey.from_bytes(parsed_transfer.recipient())
    else:
        unwrap_sol_account = None
        wsol_mint = None
        recipient = None

    print(f"bridge_token_mint={bridge_token_mint}")
    print(f"unwrap_sol_account={unwrap_sol_account}")
    print(f"recipient={recipient}")

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_native_accounts = getRedeemNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
        bridge_token_mint,
    )

    beneficiary_token_account = get_or_create_associated_token_account(
        str(bridge_token_mint), config["beneficiary"]
    )
    print(f"beneficiary_token_account={beneficiary_token_account}")

    recipient_token_account = get_or_create_associated_token_account(
        str(bridge_token_mint),
        str(redeem_native_accounts["recipient"]),
    )
    print(f"recipient_token_account={recipient_token_account}")

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    ix0 = set_compute_unit_limit(300_000)

    ix1 = complete_so_swap_native_without_swap(
        args={
            "vaa_hash": parsed_vaa.hash,
            "skip_verify_soswap_message": skip_verify_soswap_message,
        },
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_native_accounts["redeemer_config"],
            "fee_config": redeem_native_accounts["fee_config"],
            "beneficiary_token_account": beneficiary_token_account,
            "foreign_contract": redeem_native_accounts["foreign_contract"],
            "unwrap_sol_account": unwrap_sol_account,
            "wsol_mint": wsol_mint,
            "recipient": recipient,
            "mint": bridge_token_mint,
            "recipient_token_account": recipient_token_account,
            "tmp_token_account": redeem_native_accounts["tmp_token_account"],
            "wormhole_program": redeem_native_accounts["wormhole_program"],
            "token_bridge_program": redeem_native_accounts["token_bridge_program"],
            "token_bridge_config": redeem_native_accounts["token_bridge_config"],
            "vaa": redeem_native_accounts["vaa"],
            "token_bridge_claim": redeem_native_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_native_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_custody": redeem_native_accounts["token_bridge_custody"],
            "token_bridge_custody_signer": redeem_native_accounts[
                "token_bridge_custody_signer"
            ],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer_proxy.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer_proxy])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_redeem_native_token_with_whirlpool(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]
    lookup_table_key = Pubkey.from_string(config["lookup_table"]["key"])

    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    usdc_mint = Pubkey.from_bytes(parsed_transfer.token_address)
    test_mint_hex = parsed_transfer.parsed_transfer_payload.format_json()[
        "swap_data_list"
    ][0]["receivingAssetId"]
    test_mint = Pubkey.from_bytes(bytes.fromhex(test_mint_hex.replace("0x", "")))
    # usdc decimals=6
    usdc_amount = denormalize_amount(parsed_transfer.amount, 6)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_native_accounts = getRedeemNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
        usdc_mint,
    )

    recipient_bridge_token_account = get_associated_token_address(
        redeem_native_accounts["recipient"], usdc_mint
    )
    recipient_dst_token_account = get_associated_token_address(
        redeem_native_accounts["recipient"], test_mint
    )

    ui_amount = to_ui_amount(usdc_amount, 6)
    quote_config = get_test_usdc_quote_config(str(usdc_mint), ui_amount)

    print("USDC amount_in: ", quote_config["amount_in"])
    print("TEST estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("TEST min_amount_out: ", quote_config["min_amount_out"])

    # This four token account must be initialized
    # whirlpool_token_owner_account_a
    # whirlpool_token_owner_account_b
    # recipient_token_account: swap dst_token
    # recipient_bridge_token_account: if swap dst_token fail, this account will be receive the bridge_token

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    ix0 = set_compute_unit_limit(1200000)

    ix1 = complete_so_swap_native_with_whirlpool(
        args={"vaa_hash": parsed_vaa.hash},
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_native_accounts["redeemer_config"],
            "fee_config": redeem_native_accounts["fee_config"],
            "beneficiary_token_account": redeem_native_accounts[
                "beneficiary_token_account"
            ],
            "foreign_contract": redeem_native_accounts["foreign_contract"],
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
            "recipient_token_account": recipient_dst_token_account,
            "recipient_bridge_token_account": recipient_bridge_token_account,
            "tmp_token_account": redeem_native_accounts["tmp_token_account"],
            "wormhole_program": redeem_native_accounts["wormhole_program"],
            "token_bridge_program": redeem_native_accounts["token_bridge_program"],
            "token_bridge_config": redeem_native_accounts["token_bridge_config"],
            "vaa": redeem_native_accounts["vaa"],
            "token_bridge_claim": redeem_native_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_native_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_custody": redeem_native_accounts["token_bridge_custody"],
            "token_bridge_custody_signer": redeem_native_accounts[
                "token_bridge_custody_signer"
            ],
        },
    )

    blockhash = await client.get_latest_blockhash()

    lookup_table_data = await client.get_account_info(lookup_table_key)
    lookup_table_addresses = decode_address_look_up_table(lookup_table_data.value.data)

    lookup_table = AddressLookupTableAccount(
        key=lookup_table_key, addresses=lookup_table_addresses
    )

    message0 = MessageV0.try_compile(
        payer=payer_proxy.pubkey(),
        instructions=[ix0, ix1],
        address_lookup_table_accounts=[lookup_table],
        recent_blockhash=blockhash.value.blockhash,
    )
    print(message0.address_table_lookups)

    txn = VersionedTransaction(message0, [payer_proxy])

    tx_sig = await client.send_transaction(txn)
    print(tx_sig)


async def omniswap_redeem_native_token_skip_verify(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer_proxy = get_proxy()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]

    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    usdc_mint = Pubkey.from_bytes(parsed_transfer.token_address)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(config["beneficiary"])

    redeem_native_accounts = getRedeemNativeTransferAccounts(
        token_bridge_program_id,
        wormhole_program_id,
        omniswap_program_id,
        beneficiary_account,
        vaa,
        usdc_mint,
    )

    ix = complete_so_swap_native_without_swap(
        args={"vaa_hash": parsed_vaa.hash, "skip_verify_soswap_message": True},
        accounts={
            "payer": payer_proxy.pubkey(),
            "config": redeem_native_accounts["redeemer_config"],
            "fee_config": redeem_native_accounts["fee_config"],
            "beneficiary_token_account": redeem_native_accounts[
                "beneficiary_token_account"
            ],
            "foreign_contract": redeem_native_accounts["foreign_contract"],
            "mint": usdc_mint,
            "recipient_token_account": redeem_native_accounts[
                "recipient_token_account"
            ],
            "recipient": redeem_native_accounts["recipient"],
            "tmp_token_account": redeem_native_accounts["tmp_token_account"],
            "wormhole_program": redeem_native_accounts["wormhole_program"],
            "token_bridge_program": redeem_native_accounts["token_bridge_program"],
            "token_bridge_config": redeem_native_accounts["token_bridge_config"],
            "vaa": redeem_native_accounts["vaa"],
            "token_bridge_claim": redeem_native_accounts["token_bridge_claim"],
            "token_bridge_foreign_endpoint": redeem_native_accounts[
                "token_bridge_foreign_endpoint"
            ],
            "token_bridge_custody": redeem_native_accounts["token_bridge_custody"],
            "token_bridge_custody_signer": redeem_native_accounts[
                "token_bridge_custody_signer"
            ],
        },
    )

    tx = Transaction(fee_payer=payer_proxy.pubkey())

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    tx.add(set_compute_unit_limit(300_000))

    tx.add(ix)

    tx_sig = await client.send_transaction(tx, payer_proxy)
    print(tx_sig)


# Precondition: vaa has been posted
vaa_hex = "0100000000010019c9469347188ba1dd54550b822d9fdf72c5f5c342fcc09511fb6e4bc00a37392ccee23355eda90b3d5c6ee03929061f958c8fbd9a4670b98e57fabf30fc0fb50065411f340000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013e80f0300000000000000000000000000000000000000000000000000000000000f4240069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f0000000000100013636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20e2deb5206cd68c25b4edc31a2ba648a6ca5e14e76ce496bba217de48c246cde12038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938200000000000000000000000000000000000000000000000000000000000000000"
asyncio.run(omniswap_redeem_native_token(vaa_hex))
