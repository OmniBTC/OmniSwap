import functools
import ccxt
from brownie import (
    Contract,
    SoDiamond,
    LibSoFeeCelerV1,
)

from scripts.helpful_scripts import get_account, change_network


@functools.lru_cache()
def get_prices(symbols=("ETH/USDT", "BNB/USDT", "MATIC/USDT", "AVAX/USDT")):
    api = ccxt.kucoin()
    prices = {}

    for symbol in symbols:
        result = api.fetch_ticker(symbol=symbol)
        price = result["close"]
        print(f"Symbol:{symbol}, price:{price}")
        prices[symbol] = price
    return prices


def calc_percent(new_ratio, old_ratio):
    if old_ratio == 0:
        return 0
    else:
        return new_ratio / old_ratio


def set_so_prices():
    change_network("zksync2-main")
    celer_so_fee = "0x8bB2d077D0911459d80d5010f85EBa2232ca6d25"
    prices = get_prices()
    decimal = 1e27
    multiply = 1.2

    proxy_celer_so_fee = Contract.from_abi(
        "LibSoFeeCelerV1", celer_so_fee, LibSoFeeCelerV1.abi
    )

    # call once
    # proxy_celer_so_fee.setPriceRatio(1, 1, {"from": get_account()})
    # proxy_celer_so_fee.setPriceRatio(10, 1, {"from": get_account()})
    # proxy_celer_so_fee.setPriceRatio(42161, 1, {"from": get_account()})

    # bnb/eth
    dst_celer_id = 56
    ratio = int(prices["BNB/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_bnb_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: { calc_percent(ratio, old_ratio) }"
    )

    if old_ratio < ratio or ratio * 1.1 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})

    # matic/eth
    dst_celer_id = 137
    ratio = int(prices["MATIC/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_matic_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: { calc_percent(ratio, old_ratio) }"
    )

    if old_ratio < ratio or ratio * 1.1 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})

    # avax/eth
    dst_celer_id = 43114
    ratio = int(prices["AVAX/USDT"] / prices["ETH/USDT"] * decimal * multiply)
    old_ratio = int(proxy_celer_so_fee.getPriceRatio(dst_celer_id)[0])
    print(
        f"[set_avax_eth_price_ratio]: old: {old_ratio} new: {ratio} percent: { calc_percent(ratio, old_ratio) }"
    )

    if old_ratio < ratio or ratio * 1.1 < old_ratio:
        proxy_celer_so_fee.setPriceRatio(dst_celer_id, ratio, {"from": get_account()})
