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
)
from cross import SoData, WormholeData, generate_random_bytes32


async def call_omniswap_estimate_relayer_fee():
    bsc_wormhole_chain_id = 4

    so_data = SoData(
        transactionId=bytes.fromhex(generate_random_bytes32().replace("0x", "")),
        receiver=bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307"),
        sourceChainId=1,
        sendingAssetId=bytes(
            Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
        ),
        destinationChainId=4,
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


async def call_initialize_all():
    print("initialize...")
    await omniswap_initialize()

    print("set_so_fee...")
    await omniswap_set_so_fee(0)

    print("register_foreign_contract...")
    await omniswap_register_foreign_contract("bsc-test")

    print("set_price_ratio...")
    await omniswap_set_price_ratio("bsc-test", 10_000_000)


asyncio.run(call_initialize_all())