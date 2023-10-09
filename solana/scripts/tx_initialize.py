import asyncio

from solana.transaction import Transaction
from solders.pubkey import Pubkey

from omniswap.instructions import (
    initialize,
    register_foreign_contract,
)
from omniswap.program_id import PROGRAM_ID
from helper import (
    deriveSenderConfigKey,
    deriveRedeemerConfigKey,
    deriveForeignContractKey,
    getTokenBridgeDerivedAccounts,
    deriveForeignEndPointKey,
)
from config import get_client, get_payer, token_bridge_devnet, wormhole_devnet


async def omniswap_initialize():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    send_config_key = deriveSenderConfigKey(PROGRAM_ID)
    redeemer_config_key = deriveRedeemerConfigKey(PROGRAM_ID)

    token_bridge_accounts = getTokenBridgeDerivedAccounts(
        token_bridge_devnet, wormhole_devnet
    )

    ix = initialize(
        args={"relayer_fee": 1, "relayer_fee_precision": 100000},
        accounts={
            "owner": payer.pubkey(),
            "sender_config": send_config_key,
            "redeemer_config": redeemer_config_key,
            "wormhole_program": Pubkey.from_string(wormhole_devnet),
            "token_bridge_program": Pubkey.from_string(token_bridge_devnet),
            "token_bridge_config": token_bridge_accounts["token_bridge_config"],
            "token_bridge_authority_signer": token_bridge_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": token_bridge_accounts[
                "token_bridge_custody_signer"
            ],
            "token_bridge_mint_authority": token_bridge_accounts[
                "token_bridge_mint_authority"
            ],
            "wormhole_bridge": token_bridge_accounts["wormhole_bridge"],
            "token_bridge_emitter": token_bridge_accounts["token_bridge_emitter"],
            "wormhole_fee_collector": token_bridge_accounts["wormhole_fee_collector"],
            "token_bridge_sequence": token_bridge_accounts["token_bridge_sequence"],
        },
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    await client.close()


async def omniswap_register_foreign_contract():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    send_config_key = deriveSenderConfigKey(PROGRAM_ID)

    chain_id_bsc = 4
    token_bridge_emitter_bsc = bytes.fromhex(
        "0000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09"
    )
    omniswap_emitter_bsc = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )

    foreign_contract_key = deriveForeignContractKey(PROGRAM_ID, chain_id_bsc)
    foreign_endpoint_key = deriveForeignEndPointKey(
        token_bridge_devnet, chain_id_bsc, Pubkey.from_bytes(token_bridge_emitter_bsc)
    )

    ix = register_foreign_contract(
        args={"chain": chain_id_bsc, "address": list(omniswap_emitter_bsc)},
        accounts={
            "owner": payer.pubkey(),
            "config": send_config_key,
            "foreign_contract": foreign_contract_key,
            "token_bridge_foreign_endpoint": foreign_endpoint_key,
            "token_bridge_program": Pubkey.from_string(token_bridge_devnet),
        },
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    while True:
        resp = await client.get_transaction(tx_sig.value)
        if resp.value is not None:
            print(resp.value.to_json())
            break
        else:
            print("Transaction not confirmed yet. Waiting...")
            await asyncio.sleep(5)  # 5 seconds

    await client.close()


asyncio.run(omniswap_register_foreign_contract())
