import asyncio

from solders.pubkey import Pubkey

from tx_estimate_relayer_fee import omniswap_estimate_relayer_fee
from tx_initialize import (
    omniswap_initialize,
    omniswap_set_so_fee,
    omniswap_register_foreign_contract,
    omniswap_set_price_ratio,
    omniswap_set_wormhole_reserve,
    omniswap_set_redeem_proxy,
    close_pending_request,
)
from cross import SoData, WormholeData, generate_random_bytes32


async def call_omniswap_estimate_relayer_fee():
    bsc_wormhole_chain_id = 4

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307"),
        sourceChainId=30006,
        sendingAssetId=bytes(
            Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
        ),
        destinationChainId=30003,
        receivingAssetId=bytes.fromhex("51a3cc54eA30Da607974C5D07B8502599801AC08"),
        amount=1000000,
    )

    wormhole_data = WormholeData(
        dstWormholeChainId=4,
        dstMaxGasPriceInWeiForRelayer=5000000000,
        wormholeFee=1000,
        dstSoDiamond=bytes.fromhex("84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"),
    )

    src_fee, consume_value, dst_max_gas = await omniswap_estimate_relayer_fee(
        dst_wormhole_chain_id=bsc_wormhole_chain_id,
        wormhole_data=wormhole_data.encode_normalized(),
        so_data=so_data.encode_normalized(),
        swap_data_dst=bytes(),
        network="devnet",
    )

    print(
        f"src_fee={src_fee}, consume_value={consume_value}, dst_max_gas={dst_max_gas}"
    )


async def call_close_pending_request():
    await close_pending_request(
        Pubkey.from_string("EXYRz7j7habG4GfgXz4evBLjbQF3mKkPBQA5nYMqr9nT")
    )


async def call_omniswap_set_redeem_proxy():
    await omniswap_set_redeem_proxy("EiVAUrFzyQNU66S13yQrKnNqaNcJ6nbnWaLKeAXwbA6N")


async def call_set_so_fee():
    # 0.3 %
    so_fee_by_ray = 300_000
    ray = 100_000_000
    print(f"set_so_fee...{so_fee_by_ray / ray}")
    await omniswap_set_so_fee(so_fee_by_ray)


async def call_initialize_all():
    print("initialize...")
    await omniswap_initialize(network="mainnet")

    print("set_so_fee...")
    # 0.1 %
    so_fee_by_ray = 100_000
    ray = 100_000_000
    print(f"set_so_fee...{so_fee_by_ray / ray}")
    await omniswap_set_so_fee(so_fee_by_ray)

    print("register_foreign_contract...")
    await omniswap_register_foreign_contract("bsc-main", network="mainnet")
    await omniswap_register_foreign_contract("eth-main", network="mainnet")

    # print("set_price_ratio...")
    #
    # await omniswap_set_price_ratio("bsc-main", 10_000_000, network="mainnet")
    # await omniswap_set_price_ratio("eth-main", 10_000_000, network="mainnet")

asyncio.run(call_close_pending_request())
