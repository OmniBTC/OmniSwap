import asyncio

from solana.transaction import Transaction
from omniswap.instructions import so_swap_post_cross_request
from helper import (
    deriveCrossRequestKey,
    deriveSenderConfigKey,
    deriveForeignContractKey,
    deriveSoFeeConfigKey,
    derivePriceManagerKey,
    deriveWormholeBridgeDataKey,
)
from config import get_client, get_payer, get_config


async def post_cross_requset(
    dst_wormhole_chain_id,
    so_data=bytes(),
    swap_data_src=bytes(),
    wormhole_data=bytes(),
    swap_data_dst=bytes(),
    network="devnet",
    simulate=False,
):
    client = get_client(network)
    await client.is_connected()

    payer = get_payer()
    config = get_config("devnet")
    omniswap_program_id = config["program"]["SoDiamond"]
    wormhole_program_id = config["program"]["Wormhole"]

    send_config_key = deriveSenderConfigKey(omniswap_program_id)

    sender_config = await client.get_account_info(send_config_key)
    request_seq = int.from_bytes(sender_config.value.data[-8:], byteorder="little")
    print(f"request_seq={request_seq}")

    request_key = deriveCrossRequestKey(omniswap_program_id, request_seq)
    print(f"request_key={request_key}")

    fee_config_key = deriveSoFeeConfigKey(omniswap_program_id)
    foreign_contract_key = deriveForeignContractKey(
        omniswap_program_id, dst_wormhole_chain_id
    )
    price_manager_key = derivePriceManagerKey(
        omniswap_program_id, dst_wormhole_chain_id
    )
    wormhole_bridge_data_key = deriveWormholeBridgeDataKey(wormhole_program_id)

    ix = so_swap_post_cross_request(
        args={
            "so_data": so_data,
            "swap_data_src": swap_data_src,
            "wormhole_data": wormhole_data,
            "swap_data_dst": swap_data_dst,
        },
        accounts={
            "payer": payer.pubkey(),
            "config": send_config_key,
            "request": request_key,
            "fee_config": fee_config_key,
            "foreign_contract": foreign_contract_key,
            "price_manager": price_manager_key,
            "wormhole_bridge": wormhole_bridge_data_key,
        },
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    if simulate:
        tx_simulate = await client.simulate_transaction(tx)
        assert tx_simulate is not None, "tx_simulate is none"

        return request_key

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    while True:
        resp = await client.get_transaction(tx_sig.value)
        if resp.value is not None:
            return request_key
        else:
            print("Transaction not confirmed yet. Waiting...")
            await asyncio.sleep(5)  # 5 seconds
