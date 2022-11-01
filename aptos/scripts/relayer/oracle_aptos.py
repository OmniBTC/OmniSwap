from brownie import network
import ccxt

from scripts.serde_aptos import get_serde_facet
from scripts.struct import omniswap_aptos_path, hex_str_to_vector_u8
from scripts.utils import aptos_brownie


def set_so_gas():
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network="aptos-mainnet"
    )

    serde = get_serde_facet(package, network.show_active())

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main"]

    for net in nets:
        base_gas = hex_str_to_vector_u8(str(serde.normalizeU256(
            package.network_config["wormhole"]["gas"][net]["base_gas"])))
        gas_per_bytes = hex_str_to_vector_u8(str(serde.normalizeU256(
            package.network_config["wormhole"]["gas"][net]["per_byte_gas"])))
        print(f"Set wormhole gas for:{net}")
        package["wormhole_facet::set_wormhole_gas"](
            package.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes
        )


def set_so_price():
    api = ccxt.binance()
    symbols = ["ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT", "APT/USDT"]
    prices = {}

    for symbol in symbols:
        result = api.fetch_ohlcv(symbol=symbol,
                                 timeframe="1m",
                                 limit=1)
        price = result[-1][4]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price

    ratio_decimal = 1e8
    multiply = 1.1
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network="aptos-mainnet"
    )

    nets = ["mainnet", "bsc-main", "avax-main", "polygon-main"]

    if "mainnet" in nets:
        ratio = int(prices["ETH/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for mainnet:{ratio}")
        package["so_fee_wormhole::set_price_ratio"](2, ratio)
    if "bsc-main" in nets:
        ratio = int(prices["BNB/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for bsc-main:{ratio}")
        package["so_fee_wormhole::set_price_ratio"](4, ratio)
    if "polygon-main" in nets:
        ratio = int(prices["MATIC/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for polygon-main:{ratio}")
        package["so_fee_wormhole::set_price_ratio"](5, ratio)
    if "avax-main" in nets:
        ratio = int(prices["AVAX/USDT"] / prices["APT/USDT"] * ratio_decimal * multiply)
        print(f"Set price ratio for avax-main:{ratio}")
        package["so_fee_wormhole::set_price_ratio"](6, ratio)
