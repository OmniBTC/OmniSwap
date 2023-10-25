import asyncio
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit

from omniswap.instructions import (
    complete_so_swap_native_without_swap,
    complete_so_swap_wrapped_without_swap,
)
from helper import (
    getRedeemWrappedTransferAccounts,
    getRedeemNativeTransferAccounts,
)
from config import get_client, get_payer, get_config
from parse import ParsedVaa, ParsedTransfer


async def omniswap_redeem_wrapped_transfer_with_payload(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

    config = get_config("devnet")

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]

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

    ix = complete_so_swap_wrapped_without_swap(
        args={"vaa_hash": parsed_vaa.hash, "skip_verify_soswap_message": False},
        accounts={
            "payer": payer.pubkey(),
            "config": redeem_wrapped_accounts["redeemer_config"],
            "fee_config": redeem_wrapped_accounts["fee_config"],
            "beneficiary_token_account": redeem_wrapped_accounts[
                "beneficiary_token_account"
            ],
            "foreign_contract": redeem_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": redeem_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "recipient_token_account": redeem_wrapped_accounts[
                "recipient_token_account"
            ],
            "recipient": redeem_wrapped_accounts["recipient"],
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

    tx = Transaction(fee_payer=payer.pubkey())
    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    tx.add(set_compute_unit_limit(300_000))

    tx.add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)


async def omniswap_redeem_native_transfer_with_payload(vaa: str):
    client = get_client("devnet")
    await client.is_connected()

    payer = get_payer()

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
        args={"vaa_hash": parsed_vaa.hash, "skip_verify_soswap_message": False},
        accounts={
            "payer": payer.pubkey(),
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

    tx = Transaction(fee_payer=payer.pubkey())

    # ExceededMaxInstructions
    # devnet_limit=200_000, real=200933
    tx.add(set_compute_unit_limit(300_000))

    tx.add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)


# Precondition: vaa has been posted
vaa_hex = "01000000000100b0ebb8232182198b50246f7ba2d2bbcfe2ccb029757bc5261ccc35e4190590d209d9d58ee6a0594e117743baead5bbcfa4bb82f8b13fb3ced1585d12ba4c57b000653795ba0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013ac0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001dc3779efc394bf8f4ddc09c41bad9f8aae8345431d4b17a20b99c9ac209c2a80000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20493294b88e30b66848a5977de2a6a10001e8031bdd3682a07005e6674b7d69cc2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"

asyncio.run(omniswap_redeem_native_transfer_with_payload(vaa_hex))
