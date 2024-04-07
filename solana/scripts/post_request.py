import asyncio

from solana.rpc.commitment import Processed
from solana.transaction import Transaction
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from omniswap.instructions import so_swap_post_cross_request
from helper import (
    deriveCrossRequestKey,
    deriveSenderConfigKey,
    deriveForeignContractKey,
    deriveSoFeeConfigKey,
    derivePriceManagerKey,
    deriveWormholeBridgeDataKey,
    decode_address_look_up_table,
)
from solana_config import get_client, get_payer, get_config


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

    request_key = deriveCrossRequestKey(omniswap_program_id, payer.pubkey())
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

    blockhash = await client.get_latest_blockhash()

    if network == "devnet":
        lookup_table_key = Pubkey.from_string(
            "DAyyNuMjPXQWegTY1X5EEkEJn5Wx4Yf3KGwRVtFzcpaL"
        )
        lookup_table_data = await client.get_account_info(lookup_table_key)
        lookup_table_addresses = decode_address_look_up_table(
            lookup_table_data.value.data
        )

        lookup_table = AddressLookupTableAccount(
            key=lookup_table_key, addresses=lookup_table_addresses
        )

        message0 = MessageV0.try_compile(
            payer=payer.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[lookup_table],
            recent_blockhash=blockhash.value.blockhash,
        )
        tx = VersionedTransaction(message0, [payer])
    else:
        tx = Transaction(
            fee_payer=payer.pubkey(), recent_blockhash=blockhash.value.blockhash
        ).add(ix)

    if simulate:
        tx_simulate = await client.simulate_transaction(tx, commitment=Processed)
        assert tx_simulate.value is not None, "tx_simulate is none"

        return_data = tx_simulate.value.return_data.data
        total_fee = int.from_bytes(return_data, "little")
        print(f"total_fee={total_fee}")

        return request_key, total_fee

    if network == "devnet":
        tx_sig = await client.send_transaction(tx)
    else:
        tx_sig = await client.send_transaction(tx, payer)

    print(tx_sig)

    while True:
        v = 1 if network == "devnet" else None
        resp = await client.get_transaction(
            tx_sig.value, max_supported_transaction_version=v
        )
        if resp.value is not None:
            return_data = resp.value.transaction.meta.return_data.data
            total_fee = int.from_bytes(return_data, "little")
            print(f"total_fee={total_fee}")

            return request_key, total_fee
        else:
            print("Transaction not confirmed yet. Waiting...")
            await asyncio.sleep(5)  # 5 seconds


if __name__ == "__main__":
    q = deriveCrossRequestKey(
        "4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY",
        Pubkey.from_string("G9uUceCFmCbiP6ZcyBw5Q33ZZPuv3BF8a7ejJWnVE1vZ"),
    )

    print(q)
