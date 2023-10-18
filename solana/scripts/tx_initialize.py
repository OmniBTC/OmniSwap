import asyncio

from solana.transaction import Transaction
from solders.pubkey import Pubkey

from omniswap.instructions import (
    initialize,
    set_so_fee,
    set_wormhole_reserve,
    register_foreign_contract,
    set_price_ratio,
)
from omniswap.program_id import PROGRAM_ID
from omniswap.accounts import SoFeeConfig, PriceManager
from helper import (
    derivePriceManagerKey,
    deriveSoFeeConfigKey,
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

    fee_config_key = deriveSoFeeConfigKey(PROGRAM_ID)
    send_config_key = deriveSenderConfigKey(PROGRAM_ID)
    redeemer_config_key = deriveRedeemerConfigKey(PROGRAM_ID)

    token_bridge_accounts = getTokenBridgeDerivedAccounts(
        token_bridge_devnet, wormhole_devnet
    )

    ix = initialize(
        args={
            "beneficiary": Pubkey.from_string(
                "vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS"
            ),
            "actual_reserve": 110000000,
            "estimate_reserve": 120000000,
            "so_fee_by_ray": 0,
        },
        accounts={
            "owner": payer.pubkey(),
            "fee_config": fee_config_key,
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


async def omniswap_set_so_fee():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    fee_config_key = deriveSoFeeConfigKey(PROGRAM_ID)

    o = await SoFeeConfig.fetch(conn=client, address=fee_config_key)
    print(o)

    so_fee_by_ray = 100000000

    ix = set_so_fee(
        args={
            "so_fee_by_ray": so_fee_by_ray,
        },
        accounts={"payer": payer.pubkey(), "config": fee_config_key},
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    await client.close()


async def omniswap_set_wormhole_reserve():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    fee_config_key = deriveSoFeeConfigKey(PROGRAM_ID)

    o = await SoFeeConfig.fetch(conn=client, address=fee_config_key)
    print(o)

    actual_reserve = 110000000
    estimate_reserve = 120000000

    ix = set_wormhole_reserve(
        args={"actual_reserve": actual_reserve, "estimate_reserve": estimate_reserve},
        accounts={"payer": payer.pubkey(), "config": fee_config_key},
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

    ray = 1e8
    normalized_dst_base_gas_le = list(int(700000).to_bytes(32, "little"))
    normalized_dst_gas_per_bytes_le = list(int(68).to_bytes(32, "little"))
    price_manager_owner = payer.pubkey()
    init_price_ratio = int(ray / 10)

    foreign_contract_key = deriveForeignContractKey(PROGRAM_ID, chain_id_bsc)
    foreign_endpoint_key = deriveForeignEndPointKey(
        token_bridge_devnet, chain_id_bsc, Pubkey.from_bytes(token_bridge_emitter_bsc)
    )

    price_manager_key = derivePriceManagerKey(PROGRAM_ID, chain_id_bsc)

    ix = register_foreign_contract(
        args={
            "chain": chain_id_bsc,
            "address": list(omniswap_emitter_bsc),
            "normalized_dst_base_gas_le": normalized_dst_base_gas_le,
            "normalized_dst_gas_per_bytes_le": normalized_dst_gas_per_bytes_le,
            "price_manager_owner": price_manager_owner,
            "init_price_ratio": init_price_ratio,
        },
        accounts={
            "owner": payer.pubkey(),
            "config": send_config_key,
            "foreign_contract": foreign_contract_key,
            "price_manager": price_manager_key,
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


async def omniswap_set_price_ratio():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    chain_id_bsc = 4

    ray = 1e8
    new_price_ratio = int(ray / 10)

    price_manager_key = derivePriceManagerKey(PROGRAM_ID, chain_id_bsc)

    o = await PriceManager.fetch(conn=client, address=price_manager_key)
    print(o)

    ix = set_price_ratio(
        args={
            "chain": chain_id_bsc,
            "new_price_ratio": new_price_ratio,
        },
        accounts={
            "owner": payer.pubkey(),
            "price_manager": price_manager_key,
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


asyncio.run(omniswap_set_price_ratio())
