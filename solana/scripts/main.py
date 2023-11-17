import asyncio
import functools
import time

import ccxt
from solders.pubkey import Pubkey

from cross import SoData, WormholeData, generate_random_bytes32
from helper import derivePriceManagerKey
from solana_config import get_config
from tx_estimate_relayer_fee import omniswap_estimate_relayer_fee
from tx_initialize import (
    omniswap_initialize,
    omniswap_set_so_fee,
    omniswap_register_foreign_contract,
    omniswap_set_redeem_proxy,
    close_pending_request,
    omniswap_set_price_ratio,
)
from helper import deriveCrossRequestKey


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
        wormhole_data=wormhole_data.encode_compact(),
        so_data=so_data.encode_compact(),
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


async def clear_request():
    req_key = deriveCrossRequestKey(
        "4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY",
        Pubkey.from_string("2u7NCWDFym8eTVcVpAGeU2Ls7KAdYzHn1mbKmArL2qzx"),
    )
    await omniswap_set_redeem_proxy("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9")
    await close_pending_request(req_key)
    await omniswap_set_redeem_proxy("BQKfrMULH23qiSBt1S9CNvybSoshx5h4WNzd9wEw8G5U")


async def call_omniswap_set_redeem_proxy():
    await omniswap_set_redeem_proxy("EiVAUrFzyQNU66S13yQrKnNqaNcJ6nbnWaLKeAXwbA6N")


async def call_set_so_fee():
    # 0.3 %
    so_fee_by_ray = 300_000
    ray = 100_000_000
    print(f"set_so_fee...{so_fee_by_ray / ray}")
    await omniswap_set_so_fee(so_fee_by_ray)


async def register_foreign_contracts(network="mainnet"):
    config = get_config(network=network)
    for net in config["wormhole"]["dst_chain"]:
        print(f"\nregister_foreign_contract for net:{net}")
        await omniswap_register_foreign_contract(net, network="mainnet")
        time.sleep(1)


@functools.lru_cache()
def get_prices(
    symbols=(
        "ETH/USDT",
        "BNB/USDT",
        "MATIC/USDT",
        "AVAX/USDT",
        "APT/USDT",
        "SUI/USDT",
        "SOL/USDT",
    )
):
    api = ccxt.kucoin(
        {
            "proxies": {
                "http": "127.0.0.1:7890",
                "https": "127.0.0.1:7890",
            }
        }
    )
    api.load_markets()
    prices = {}

    for symbol in symbols:
        result = api.fetch_ticker(symbol=symbol)
        price = result["close"]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price
    return prices


async def set_price_ratios(network="mainnet"):
    config = get_config(network=network)
    prices = get_prices()

    decimal = 1e8
    multiply = 1.2
    dst_pair = {
        "bsc-main": "BNB/USDT",
        "eth-main": "ETH/USDT",
        "polygon-main": "MATIC/USDT",
        "avax-main": "AVAX/USDT",
        "aptos-main": "APT/USDT",
        "sui-main": "SUI/USDT",
    }
    for net in config["wormhole"]["dst_chain"]:
        if net not in dst_pair:
            continue
        ratio = int(prices[dst_pair[net]] / prices["SOL/USDT"] * decimal * multiply)
        print(f"\nset_price_ratio for net:{net} ratio:{ratio}")
        await omniswap_set_price_ratio(net, ratio, network="mainnet")
        time.sleep(1)


async def call_initialize_all():
    print("initialize...")
    await omniswap_initialize(network="mainnet")

    await register_foreign_contracts(network="mainnet")


asyncio.run(set_price_ratios())
