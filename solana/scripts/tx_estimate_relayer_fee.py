import asyncio

from solana.transaction import Transaction
from solders.pubkey import Pubkey

from omniswap.instructions import estimate_relayer_fee
from omniswap.program_id import PROGRAM_ID
from helper import (
    derivePriceManagerKey,
    deriveSoFeeConfigKey,
    deriveForeignContractKey,
    deriveWormholeBridgeDataKey
)
from config import get_client, get_payer, wormhole_devnet
from cross import (
    SoData,
    WormholeData,
    generate_random_bytes32
)

async def omniswap_estimate_relayer_fee():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    chain_id_bsc = 4
    fee_config_key = deriveSoFeeConfigKey(PROGRAM_ID)
    foreign_contract_key = deriveForeignContractKey(PROGRAM_ID, chain_id_bsc)
    price_manager_key = derivePriceManagerKey(PROGRAM_ID, chain_id_bsc)
    wormhole_bridge_data_key = deriveWormholeBridgeDataKey(wormhole_devnet)

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307"),
        sourceChainId=1,
        sendingAssetId=bytes(Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")),
        destinationChainId=4,
        receivingAssetId=bytes.fromhex("51a3cc54eA30Da607974C5D07B8502599801AC08"),
        amount=1000000
    )

    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=5000000000,
        wormholeFee=1000,
        dstSoDiamond=bytes.fromhex("84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc")
    )

    ix = estimate_relayer_fee(
        args={
            "chain_id": chain_id_bsc,
            "so_data": so_data.encode_normalized(),
            "wormhole_data": wormhole_data.encode_normalized(),
            "swap_data_dst": bytes()
        },
        accounts={
            "fee_config": fee_config_key,
            "foreign_contract": foreign_contract_key,
            "price_manager": price_manager_key,
            "wormhole_bridge": wormhole_bridge_data_key
        },
    )

    recent_hash = await client.get_latest_blockhash()
    tx = Transaction(
        recent_blockhash=recent_hash.value.blockhash,
        fee_payer=payer.pubkey()
    ).add(ix)

    tx.sign(payer)

    tx_simulate = await client.simulate_transaction(tx, True)
    return_data = tx_simulate.value.return_data.data

    print(tx_simulate.value.return_data)

    src_fee = int.from_bytes(return_data[:8], 'little')
    consume_value = int.from_bytes(return_data[8:16], 'little')
    dst_max_gas = int.from_bytes(return_data[16:], 'little')

    print(f"src_fee={src_fee}, consume_value={consume_value}, dst_max_gas={dst_max_gas}")

    await client.close()



asyncio.run(omniswap_estimate_relayer_fee())
