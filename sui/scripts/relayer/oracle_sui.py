import functools

from brownie import network
import ccxt

from scripts import sui_project
from scripts.serde_sui import get_serde_facet, get_price_ratio
from scripts.struct_sui import hex_str_to_vector_u8
from sui_brownie import SuiPackage

net = sui_project.network
package_id = sui_project.network_config["packages"]["OmniSwap"]
sui_package = SuiPackage(package_id=package_id, package_name="OmniSwap")


def set_so_gas_for_test():
    nets = ["goerli", "bsc-test", "avax-test", "polygon-test", "aptos-testnet"]
    storage = sui_project.network_config["objects"]["FacetStorage"]
    facet_manager = sui_project.network_config["objects"]["FacetManager"]

    for net in nets:
        base_gas = sui_project.network_config["wormhole"]["gas"][net]["base_gas"]
        gas_per_bytes = sui_project.network_config["wormhole"]["gas"][net]["per_byte_gas"]
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        sui_package.wormhole_facet.set_wormhole_gas(
            storage,
            facet_manager,
            sui_project.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes,
            gas_budget=1000000000
        )


def set_so_gas():
    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", "aptos-mainnet", "solana-mainnet"]
    storage = sui_project.network_config["objects"]["FacetStorage"]
    facet_manager = sui_project.network_config["objects"]["FacetManager"]
    gas = {
        "mainnet": {
            "dst_chainid": 2,
            "base_gas": 350000,
            "per_byte_gas": 68,
        },
        # "bsc-main": {
        #     "dst_chainid": 4,
        #     "base_gas": 700000,
        #     "per_byte_gas": 68
        # },
        # "polygon-main": {
        #     "dst_chainid": 5,
        #     "base_gas": 2800000,
        #     "per_byte_gas": 68
        # },
        # "avax-main": {
        #     "dst_chainid": 6,
        #     "base_gas": 1400000,
        #     "per_byte_gas": 68
        # },
        # "aptos-mainnet": {
        #     "dst_chainid": 22,
        #     "base_gas": 40000,
        #     "per_byte_gas": 10
        # },
        # "sui-mainnet": {
        #     "dst_chainid": 21,
        #     "base_gas": 840000,
        #     "per_byte_gas": 68
        # },
        # "solana-mainnet": {
        #     "dst_chainid": 1,
        #     "base_gas": 10000000000000000,
        #     "per_byte_gas": 68
        # }
    }

    for net in nets:
        if net not in gas:
            continue
        base_gas = gas[net]["base_gas"]
        gas_per_bytes = gas[net]["per_byte_gas"]
        dst_chainid = gas[net]["dst_chainid"]
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        sui_package.wormhole_facet.set_wormhole_gas(
            storage,
            facet_manager,
            dst_chainid,
            base_gas,
            gas_per_bytes
        )


@functools.lru_cache()
def get_prices(symbols=("ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT", "APT/USDT", "SUI/USDT", "SOL/USDT")):
    api = ccxt.kucoin()
    prices = {}

    for symbol in symbols:
        result = api.fetch_ticker(symbol=symbol)
        price = result["close"]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price
    return prices


def set_so_price_for_test():
    prices = get_prices()

    ratio_decimal = 1e8
    multiply = 1.2

    nets = ["goerli", "bsc-test", "avax-test", "polygon-test", "aptos-testnet"]
    clock = sui_project.network_config["objects"]["Clock"]
    price_manager = sui_project.network_config["objects"]["PriceManager"]

    if "goerli" in nets:
        wormhole_chain_id = 2
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["ETH/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(
            f"Set price ratio for mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "bsc-test" in nets:
        wormhole_chain_id = 4
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["BNB/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for bsc-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "polygon-test" in nets:
        wormhole_chain_id = 5
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["MATIC/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for polygon-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "avax-test" in nets:
        wormhole_chain_id = 6
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["AVAX/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for avax-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "aptos-testnet" in nets:
        wormhole_chain_id = 22
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["APT/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)


def set_so_price():
    prices = get_prices()

    ratio_decimal = 1e8
    multiply = 1.2

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", "aptos-mainnet", "solana-mainnet"]
    clock = sui_project.network_config["objects"]["Clock"]
    price_manager = sui_project.network_config["objects"]["PriceManager"]

    if "mainnet" in nets:
        wormhole_chain_id = 2
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["ETH/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for mainnet: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "bsc-main" in nets:
        wormhole_chain_id = 4
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["BNB/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for bsc-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "polygon-main" in nets:
        wormhole_chain_id = 5
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["MATIC/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for polygon-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "avax-main" in nets:
        wormhole_chain_id = 6
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["AVAX/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for avax-main: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "aptos-mainnet" in nets:
        wormhole_chain_id = 22
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["APT/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)

    if "solana-mainnet" in nets:
        wormhole_chain_id = 1
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["SOL/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for solana-mainnet: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)


if __name__ == "__main__":
    set_so_gas()
