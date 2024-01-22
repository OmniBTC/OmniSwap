import asyncio

from solana.transaction import Transaction
from solders.pubkey import Pubkey

from omniswap.instructions import (
    initialize,
    set_so_fee,
    set_wormhole_reserve,
    register_foreign_contract,
    set_price_ratio,
    set_redeem_proxy,
)
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
from solana_config import (
    get_client,
    get_payer,
    get_config,
    get_price_manager,
    get_payer_by_env,
)
from omniswap.instructions import so_swap_close_pending_request


async def omniswap_initialize(network="devnet"):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer_by_env()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]
    token_bridge_program_id = config["program"]["TokenBridge"]

    beneficiary = Pubkey.from_string(config["beneficiary"])
    redeemer_proxy = Pubkey.from_string(config["redeemer_proxy"])

    actual_reserve = config["wormhole"]["actual_reserve"]
    estimate_reserve = config["wormhole"]["estimate_reserve"]
    so_fee_by_ray = config["so_fee_by_ray"]

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)
    send_config_key = deriveSenderConfigKey(omniswap_program_id)
    redeemer_config_key = deriveRedeemerConfigKey(omniswap_program_id)

    token_bridge_accounts = getTokenBridgeDerivedAccounts(
        token_bridge_program_id, wormhole_program_id
    )

    ix = initialize(
        args={
            "beneficiary": beneficiary,
            "redeemer_proxy": redeemer_proxy,
            "actual_reserve": actual_reserve,
            "estimate_reserve": estimate_reserve,
            "so_fee_by_ray": so_fee_by_ray,
        },
        accounts={
            "owner": payer.pubkey(),
            "fee_config": fee_config_key,
            "sender_config": send_config_key,
            "redeemer_config": redeemer_config_key,
            "wormhole_program": Pubkey.from_string(wormhole_program_id),
            "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
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

    while True:
        resp = await client.get_transaction(tx_sig.value)
        if resp.value is not None:
            print(resp.value.to_json())
            break
        else:
            print("Transaction not confirmed yet. Waiting...")
            await asyncio.sleep(5)  # 5 seconds


async def omniswap_set_so_fee(new_so_fee_by_ray: int, network="devnet"):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer_by_env()

    config = get_config(network)
    omniswap_program_id = config["program"]["SoDiamond"]

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    old = await SoFeeConfig.fetch(conn=client, address=fee_config_key)
    print(f"old={old}")

    ix = set_so_fee(
        args={
            "so_fee_by_ray": new_so_fee_by_ray,
        },
        accounts={"payer": payer.pubkey(), "config": fee_config_key},
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


async def omniswap_set_wormhole_reserve(
    new_actual_reserve_by_ray: int, new_estimate_reserve_by_ray: int, network="devnet"
):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer()

    config = get_config(network)
    omniswap_program_id = config["program"]["SoDiamond"]

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)

    old = await SoFeeConfig.fetch(conn=client, address=fee_config_key)
    print(f"old={old}")

    ix = set_wormhole_reserve(
        args={
            "actual_reserve": new_actual_reserve_by_ray,
            "estimate_reserve": new_estimate_reserve_by_ray,
        },
        accounts={"payer": payer.pubkey(), "config": fee_config_key},
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


async def omniswap_register_foreign_contract(dst_chain: str, network="devnet"):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer_by_env()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]
    token_bridge_program_id = config["program"]["TokenBridge"]

    dst_chain_config = config["wormhole"]["dst_chain"][dst_chain]

    dst_wormhole_chainid = dst_chain_config["chainid"]
    dst_token_bridge_emitter = bytes.fromhex(
        dst_chain_config["token_bridge_emitter"].replace("0x", "")
    )
    dst_omniswap_emitter = bytes.fromhex(
        dst_chain_config["omniswap_emitter"].replace("0x", "")
    )
    dst_base_gas = dst_chain_config["base_gas"]
    dst_gas_per_bytes = dst_chain_config["per_byte_gas"]
    price_manager_owner = dst_chain_config["price_manager"]

    normalized_dst_base_gas_le = list(int(dst_base_gas).to_bytes(32, "little"))
    normalized_dst_gas_per_bytes_le = list(
        int(dst_gas_per_bytes).to_bytes(32, "little")
    )

    # bsc / sol = 0.1
    ray = 1e8
    init_price_ratio = int(ray / 10)

    send_config_key = deriveSenderConfigKey(omniswap_program_id)
    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, dst_wormhole_chainid
    )

    foreign_endpoint_key = deriveForeignEndPointKey(
        token_bridge_program_id,
        dst_wormhole_chainid,
        Pubkey.from_bytes(dst_token_bridge_emitter),
    )

    price_manager_key = derivePriceManagerKey(omniswap_program_id, dst_wormhole_chainid)

    ix = register_foreign_contract(
        args={
            "chain": dst_wormhole_chainid,
            "address": list(dst_omniswap_emitter),
            "normalized_dst_base_gas_le": normalized_dst_base_gas_le,
            "normalized_dst_gas_per_bytes_le": normalized_dst_gas_per_bytes_le,
            "price_manager_owner": Pubkey.from_string(price_manager_owner),
            "init_price_ratio": init_price_ratio,
        },
        accounts={
            "owner": payer.pubkey(),
            "config": send_config_key,
            "foreign_contract": foreign_contract_key,
            "price_manager": price_manager_key,
            "token_bridge_foreign_endpoint": foreign_endpoint_key,
            "token_bridge_program": Pubkey.from_string(token_bridge_program_id),
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


async def omniswap_set_price_ratio(
    dst_chain: str, new_price_ratio_by_ray: int, network="devnet"
):
    client = get_client(network)
    await client.is_connected()

    price_manager = get_payer_by_env()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]

    dst_chain_config = config["wormhole"]["dst_chain"][dst_chain]
    dst_wormhole_chainid = dst_chain_config["chainid"]

    price_manager_key = derivePriceManagerKey(omniswap_program_id, dst_wormhole_chainid)

    old = await PriceManager.fetch(conn=client, address=price_manager_key)
    print(f"old={old}")

    ix = set_price_ratio(
        args={
            "chain": dst_wormhole_chainid,
            "new_price_ratio": new_price_ratio_by_ray,
        },
        accounts={
            "owner": price_manager.pubkey(),
            "price_manager": price_manager_key,
        },
    )

    tx = Transaction(fee_payer=price_manager.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, price_manager)
    print(tx_sig)

    while True:
        resp = await client.get_transaction(tx_sig.value)
        if resp.value is not None:
            print(resp.value.to_json())
            break
        else:
            print("Transaction not confirmed yet. Waiting...")
            await asyncio.sleep(5)  # 5 seconds


async def omniswap_set_redeem_proxy(new_proxy: str, network="devnet"):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]

    redeemer_config_key = deriveRedeemerConfigKey(omniswap_program_id)

    ix = set_redeem_proxy(
        args={"new_proxy": Pubkey.from_string(new_proxy)},
        accounts={
            "owner": payer.pubkey(),
            "config": redeemer_config_key,
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


async def close_pending_request(request_key: Pubkey, network="devnet"):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]

    redeemer_config_key = deriveRedeemerConfigKey(omniswap_program_id)

    ix = so_swap_close_pending_request(
        accounts={
            "payer": payer.pubkey(),
            "recipient": payer.pubkey(),
            "config": redeemer_config_key,
            "request": request_key,
        },
    )

    recent_hash = await client.get_latest_blockhash()
    tx = Transaction(
        recent_blockhash=recent_hash.value.blockhash, fee_payer=payer.pubkey()
    ).add(ix)

    tx.sign(payer)

    tx_resp = await client.send_transaction(tx, payer)
    print(tx_resp.value)
