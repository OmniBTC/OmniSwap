import functools

from brownie import network
import ccxt

from scripts.serde_aptos import get_serde_facet, get_price_resource
from scripts.serde_struct import omniswap_aptos_path, hex_str_to_vector_u8
import aptos_brownie


def set_so_gas():
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network="aptos-mainnet"
    )

    serde = get_serde_facet(package, network.show_active())

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", "sui-mainnet", "solana-mainnet"]

    gas = {
        # "mainnet": {
        #     "dst_chainid": 2,
        #     "base_gas": 700000,
        #     "per_byte_gas": 68,
        # },
        # "bsc-main": {
        #     "dst_chainid": 4,
        #     "base_gas": 700000,
        #     "per_byte_gas": 68
        # },
        "polygon-main": {
            "dst_chainid": 5,
            "base_gas": 2800000,
            "per_byte_gas": 68
        },
        "avax-main": {
            "dst_chainid": 6,
            "base_gas": 1400000,
            "per_byte_gas": 68
        },
        "aptos-mainnet": {
            "dst_chainid": 22,
            "base_gas": 40000,
            "per_byte_gas": 10
        },
        "sui-mainnet": {
            "dst_chainid": 21,
            "base_gas": 840000,
            "per_byte_gas": 68
        },
        "solana-mainnet": {
            "dst_chainid": 1,
            "base_gas": 10000000000000000,
            "per_byte_gas": 68
        },
    }

    for net in nets:
        if net not in gas:
            continue
        base_gas = gas[net]["base_gas"]
        gas_per_bytes = gas[net]["per_byte_gas"]
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        base_gas = hex_str_to_vector_u8(str(serde.normalizeU256(base_gas)))
        gas_per_bytes = hex_str_to_vector_u8(str(serde.normalizeU256(gas_per_bytes)))
        package["wormhole_facet::set_wormhole_gas"](
            gas[net]["dst_chainid"],
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


def set_so_price():
    prices = get_prices()

    ratio_decimal = 1e8
    multiply = 1.2
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network="aptos-mainnet"
    )

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", 'sui-mainnet']

    if "mainnet" in nets:
        wormhole_chain_id = 2
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["ETH/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)
    if "bsc-main" in nets:
        wormhole_chain_id = 4
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["BNB/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for bsc-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)
    if "polygon-main" in nets:
        wormhole_chain_id = 5
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["MATIC/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for polygon-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)
    if "avax-main" in nets:
        wormhole_chain_id = 6
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["AVAX/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for avax-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)

    if "sui-mainnet" in nets:
        wormhole_chain_id = 21
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["SUI/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)

    if "solana-mainnet" in nets:
        wormhole_chain_id = 1
        price_resource = get_price_resource(package, str(package.account.account_address), wormhole_chain_id)
        price_manage = package.account_resource(
            price_resource, f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager")
        old_ratio = int(price_manage["data"]["price_data"]["current_price_ratio"])
        ratio = int(prices["SOL/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} "
              f"percent: {ratio / old_ratio if old_ratio > 0 else 0}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            package["so_fee_wormhole::set_price_ratio"](wormhole_chain_id, ratio)
