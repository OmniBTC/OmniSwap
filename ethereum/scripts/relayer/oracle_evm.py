import functools

from brownie import (
    network,
    Contract,
    SoDiamond,
    WormholeFacet,
    LibSoFeeWormholeV1,
    StargateFacet,
)
import ccxt

from scripts.helpful_scripts import get_wormhole_info, get_account, change_network
import aptos_brownie


def set_so_gas():
    proxy_wormhole = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", "aptos-mainnet"]

    gas = get_wormhole_info()["gas"]
    for net in nets:
        if net == network.show_active():
            continue
        print(
            f"network:{network.show_active()}, "
            f"set dst net {net} wormhole gas: "
            f"base_gas:{gas[net]['base_gas']},"
            f"per_byte_gas:{gas[net]['per_byte_gas']}"
        )
        proxy_wormhole.setWormholeGas(
            gas[net]["dst_chainid"],
            gas[net]["base_gas"],
            gas[net]["per_byte_gas"],
            {"from": get_account()},
        )


@functools.lru_cache()
def get_prices(symbols=("ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT", "APT/USDT")):
    api = ccxt.kucoin()
    prices = {}

    for symbol in symbols:
        result = api.fetch_ticker(symbol=symbol)
        price = result["close"]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price
    return prices


def set_so_price():
    prices = get_prices()

    decimal = 1e27
    multiply = 1.2
    if network.show_active() == "avax-main":
        # bnb
        dst_wormhole_id = 4
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["BNB/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for bnb-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "mainnet":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "polygon-main":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "bsc-main":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )


def set_so_gass():
    nets = ["mainnet", "avax-main", "bsc-main", "polygon-main"]
    for net in nets:
        print(f"Change net into {net}...")
        change_network(net)
        set_so_gas()


def set_so_prices():
    nets = ["mainnet", "avax-main", "bsc-main", "polygon-main"]
    for net in nets:
        print(f"Change net into {net}...")
        change_network(net)
        set_so_price()


def allow_sg_receive():
    addr = "0x429b786a05de2175C041a4C1A273a187D376E9ff"
    nets = [
        "mainnet",
        "avax-main",
        "bsc-main",
        "polygon-main",
        "arbitrum-main",
        "optimism-main",
    ]
    for net in nets:
        print(f"Change net into {net}...")
        change_network(net)
        proxy_stargate = Contract.from_abi(
            "StargateFacet", SoDiamond[-1].address, StargateFacet.abi
        )

        proxy_stargate.setAllowedAddress(addr, True, {"from": get_account()})
