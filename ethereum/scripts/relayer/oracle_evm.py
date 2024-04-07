import functools

from brownie import (
    network,
    Contract,
    SoDiamond,
    WormholeFacet,
    LibSoFeeWormholeV1,
    StargateFacet,
    LibSoFeeCelerV1,
)
import ccxt

from scripts.helpful_scripts import get_wormhole_info, get_account, change_network
import aptos_brownie


def set_so_gas_for_test():
    proxy_wormhole = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )

    nets = [
        "goerli",
        "bsc-test",
        "avax-test",
        "polygon-test",
        "aptos-testnet",
        "sui-testnet",
    ]

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


def set_so_gas():
    proxy_wormhole = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )

    nets = [
        "mainnet",
        "bsc-main",
        "avax-main",
        "polygon-main",
        "aptos-mainnet",
        "sui-mainnet",
        "solana-mainnet"
    ]

    gas = {
        "mainnet": {
            "dst_chainid": 2,
            "base_gas": 600000,
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
        # },
    }
    for net in nets:
        if net == network.show_active():
            continue
        if net not in gas:
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
def get_prices(
        symbols=("ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT", "APT/USDT", "SUI/USDT", "SOL/USDT")
):
    api = ccxt.kucoin()
    prices = {}

    for symbol in symbols:
        result = api.fetch_ticker(symbol=symbol)
        price = result["close"]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price
    return prices


def set_celer_bnb_price_on_avax(ratio):
    # bnb
    dst_celer_id = 56
    old_ratio = int(LibSoFeeCelerV1[-1].getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_celer_bnb_price_on_avax]: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
    )

    if old_ratio < ratio or ratio * 1.03 < old_ratio:
        LibSoFeeCelerV1[-1].setPriceRatio(dst_celer_id, ratio, {"from": get_account()})


def set_so_price_for_test():
    prices = get_prices()

    decimal = 1e27
    multiply = 1
    if network.show_active() == "avax-test":
        # bnb
        dst_wormhole_id = 4
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["BNB/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for bnb-main: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        set_celer_bnb_price_on_avax(ratio)

        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "goerli":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "polygon-test":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "bsc-test":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} "
            f"percent: {ratio / old_ratio if old_ratio > 0 else old_ratio}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )


def calc_percent(new_ratio, old_ratio):
    if old_ratio == 0:
        return 0
    else:
        return new_ratio / old_ratio


def set_so_price_for_celer_zkevm():
    change_network("zkevm-main")
    celer_so_fee = "0x66F440252fe99454df8F8e1EB7743EA08FE7D8e2"
    prices = get_prices()
    decimal = 1e27
    multiply = 1

    proxy_celer_so_fee = Contract.from_abi(
        "LibSoFeeCelerV1", celer_so_fee, LibSoFeeCelerV1.abi
    )

    # call once
    # proxy_celer_fee.setPriceRatio(1, 1e27, {"from": account})
    # proxy_celer_fee.setPriceRatio(10, 1e27, {"from": account})
    # proxy_celer_fee.setPriceRatio(324, 1e27, {"from": account})
    # proxy_celer_fee.setPriceRatio(42161, 1e27, {"from": account})

    # bnb/eth
    dst_celer_id = 56
    ratio = int(prices["BNB/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_bnb_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
    )

    if old_ratio < ratio or ratio * 1.03 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})

    # matic/eth
    dst_celer_id = 137
    ratio = int(prices["MATIC/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_matic_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
    )

    if old_ratio < ratio or ratio * 1.03 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})

    # avax/eth
    dst_celer_id = 43114
    ratio = int(prices["AVAX/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_avax_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
    )

    if old_ratio < ratio or ratio * 1.03 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})


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
            f"Set price ratio for bnb-main: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        set_celer_bnb_price_on_avax(ratio)

        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # solana
        dst_wormhole_id = 1
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SOL/USDT"] / prices["AVAX/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for solana-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "mainnet":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # solana
        dst_wormhole_id = 1
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SOL/USDT"] / prices["ETH/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for solana-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "polygon-main":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # solana
        dst_wormhole_id = 1
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SOL/USDT"] / prices["MATIC/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for solana-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

    if network.show_active() == "bsc-main":
        # aptos
        dst_wormhole_id = 22
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["APT/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for aptos-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # sui
        dst_wormhole_id = 21
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SUI/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for sui-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
            LibSoFeeWormholeV1[-1].setPriceRatio(
                dst_wormhole_id, ratio, {"from": get_account()}
            )

        # solana
        dst_wormhole_id = 1
        old_ratio = int(LibSoFeeWormholeV1[-1].getPriceRatio(dst_wormhole_id)[0])
        ratio = int(prices["SOL/USDT"] / prices["BNB/USDT"] * decimal * multiply)
        print(
            f"Set price ratio for solana-mainnet: old: {old_ratio} new: {ratio} percent: {calc_percent(ratio, old_ratio)}"
        )
        if old_ratio < ratio or ratio * 1.03 < old_ratio:
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
