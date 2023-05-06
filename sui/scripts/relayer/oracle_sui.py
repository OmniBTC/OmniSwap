import functools

from brownie import network
import ccxt

from scripts.serde_sui import get_serde_facet, get_price_ratio
from scripts.struct_sui import omniswap_sui_path, hex_str_to_vector_u8
from sui_brownie import SuiProject, SuiPackage

net = "sui-testnet"
sui_project = SuiProject(omniswap_sui_path, network=net)
if "main" in net:
    package_id = ""
else:
    package_id = ""
sui_package = SuiPackage(package_id=package_id, package_name="OmniSwap")


def set_so_gas():
    serde = get_serde_facet(network.show_active())

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main"]
    storage = sui_project.network_config["Storage"]
    facet_manager = sui_project.network_config["WormholeFacetManager"]

    for net in nets:
        base_gas = sui_project.network_config["wormhole"]["gas"][net]["base_gas"]
        gas_per_bytes = sui_project.network_config["wormhole"]["gas"][net]["per_byte_gas"]
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        base_gas = hex_str_to_vector_u8(str(serde.normalizeU256(base_gas)))
        gas_per_bytes = hex_str_to_vector_u8(str(serde.normalizeU256(gas_per_bytes)))
        sui_package.wormhole_facet.set_wormhole_gas(
            storage,
            facet_manager,
            sui_project.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes
        )


@functools.lru_cache()
def get_prices(symbols=("ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT", "SUI/USDT", "SUI/USDT")):
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

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main", "aptos-mainnet"]
    clock = sui_project.network_config["Clock"]
    price_manager = sui_project.network_config["PriceManager"]

    if "mainnet" in nets:
        wormhole_chain_id = 2
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["ETH/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "bsc-main" in nets:
        wormhole_chain_id = 4
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["BNB/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for bsc-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "polygon-main" in nets:
        wormhole_chain_id = 5
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["MATIC/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for polygon-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "avax-main" in nets:
        wormhole_chain_id = 6
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["AVAX/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for avax-main: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)
    if "aptos-mainnet" in nets:
        wormhole_chain_id = 22
        old_ratio = int(get_price_ratio(sui_package, price_manager, wormhole_chain_id))
        ratio = int(prices["APT/USDT"] / prices["SUI/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {ratio / old_ratio}")
        if old_ratio < ratio or ratio * 1.1 < old_ratio:
            sui_package.so_fee_wormhole.set_price_ratio(clock, price_manager, wormhole_chain_id, ratio)