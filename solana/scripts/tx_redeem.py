import asyncio
from solana.transaction import Transaction
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit

from omniswap.instructions import (
    complete_so_swap_native_without_swap,
    complete_so_swap_wrapped_without_swap,
)
from omniswap.program_id import PROGRAM_ID
from helper import (
    getRedeemWrappedTransferAccounts,
    getRedeemNativeTransferAccounts,
)
from config import get_client, get_payer, wormhole_devnet, token_bridge_devnet
from parse import ParsedVaa, ParsedTransfer


async def omniswap_redeem_wrapped_transfer_with_payload(vaa: str):
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    parsed_vaa = ParsedVaa.parse(vaa)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(
        "vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS"
    )

    redeem_wrapped_accounts = getRedeemWrappedTransferAccounts(
        token_bridge_devnet, wormhole_devnet, PROGRAM_ID, beneficiary_account, vaa
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

    await client.close()


async def omniswap_redeem_native_transfer_with_payload(vaa: str):
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    usdc_mint = Pubkey.from_bytes(parsed_transfer.token_address)

    # collect token so fee
    beneficiary_account = Pubkey.from_string(
        "vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS"
    )
    redeem_native_accounts = getRedeemNativeTransferAccounts(
        token_bridge_devnet,
        wormhole_devnet,
        PROGRAM_ID,
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

    await client.close()


# Precondition: vaa has been posted
vaa_hex = "01000000000100ea335bdd479c310e4fc6cfa0e1c068177828bec2c428c54bbea56ff4ad30a5266be88eb9bbcc65ba5b2b9c10d53fff1609dde23fdf38552d06316604a72edd3500652f3c750000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013920f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001732b4de4d2ba87772ff26294dee2290b13f705084775557a5e81fc65b5bb48cd000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac2073e2b961812bcd66ae7547bb352b9926013bddb495b0a4169d8e12bcc82a8b642038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"

asyncio.run(omniswap_redeem_native_transfer_with_payload(vaa_hex))
