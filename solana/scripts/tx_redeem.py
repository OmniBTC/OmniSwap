import asyncio
from solana.transaction import Transaction
from solders.instruction import AccountMeta
from solders.pubkey import Pubkey

from omniswap.instructions import (
    redeem_wrapped_transfer_with_payload,
    redeem_native_transfer_with_payload,
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

    redeem_wrapped_accounts = getRedeemWrappedTransferAccounts(
        token_bridge_devnet, wormhole_devnet, PROGRAM_ID, payer.pubkey(), vaa
    )

    ix = redeem_wrapped_transfer_with_payload(
        args={"vaa_hash": parsed_vaa.hash},
        accounts={
            "payer": payer.pubkey(),
            "payer_token_account": redeem_wrapped_accounts["payer_token_key"],
            "config": redeem_wrapped_accounts["redeemer_config_key"],
            "foreign_contract": redeem_wrapped_accounts["foreign_contract_key"],
            "token_bridge_wrapped_mint": redeem_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "recipient_token_account": redeem_wrapped_accounts[
                "recipient_token_account"
            ],
            "recipient": redeem_wrapped_accounts["recipient"],
            "tmp_token_account": redeem_wrapped_accounts["tmp_token_key"],
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

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

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

    redeem_native_accounts = getRedeemNativeTransferAccounts(
        token_bridge_devnet, wormhole_devnet, PROGRAM_ID, payer.pubkey(), vaa, usdc_mint
    )

    ix = redeem_native_transfer_with_payload(
        args={"vaa_hash": parsed_vaa.hash},
        accounts={
            "payer": payer.pubkey(),
            "payer_token_account": redeem_native_accounts["payer_token_account"],
            "config": redeem_native_accounts["redeemer_config"],
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

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    await client.close()


# Precondition: vaa has been posted
vaa_hex = "01000000000100a27a9ee47f5cc670f2f959e3a993fe393940dcfc55d7ecf36f75734e27f31d6c6045d835cf9d81b418383bc2a61ce3e1d8aa2ae0b9fccabe88917fa2b66d621901652212a80000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09000000000000136b0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea700017ef1dcda48c0b739dfd4da982c187838573cc044d8ded9fe382b84ceb6fa6b53000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20d5006ba1ae36806c379a926d648b5e0783e966eddde87b8920717a7e819436982038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"

asyncio.run(omniswap_redeem_native_transfer_with_payload(vaa_hex))
