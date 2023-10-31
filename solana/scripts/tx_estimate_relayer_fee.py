from solana.transaction import Transaction
from omniswap.instructions import estimate_relayer_fee
from helper import (
    derivePriceManagerKey,
    deriveSoFeeConfigKey,
    deriveForeignContractKey,
    deriveWormholeBridgeDataKey,
)
from solana_config import get_client, get_payer, get_config


async def omniswap_estimate_relayer_fee(
    dst_wormhole_chain_id: int,
    wormhole_data: bytes,
    so_data: bytes,
    swap_data_dst: bytes,
    network="devnet",
):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)
    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, dst_wormhole_chain_id
    )
    price_manager_key = derivePriceManagerKey(
        omniswap_program_id, dst_wormhole_chain_id
    )
    wormhole_bridge_data_key = deriveWormholeBridgeDataKey(wormhole_program_id)

    ix = estimate_relayer_fee(
        args={
            "so_data": so_data,
            "wormhole_data": wormhole_data,
            "swap_data_dst": swap_data_dst,
        },
        accounts={
            "fee_config": fee_config_key,
            "foreign_contract": foreign_contract_key,
            "price_manager": price_manager_key,
            "wormhole_bridge": wormhole_bridge_data_key,
        },
    )

    recent_hash = await client.get_latest_blockhash()
    tx = Transaction(
        recent_blockhash=recent_hash.value.blockhash, fee_payer=payer.pubkey()
    ).add(ix)

    tx.sign(payer)

    tx_simulate = await client.simulate_transaction(tx, True)
    assert tx_simulate is not None, "tx_simulate is none"

    return_data = tx_simulate.value.return_data.data

    src_fee = int.from_bytes(return_data[:8], "little")
    consume_value = int.from_bytes(return_data[8:16], "little")
    dst_max_gas = int.from_bytes(return_data[16:], "little")

    return (src_fee, consume_value, dst_max_gas)
