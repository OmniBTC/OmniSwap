import functools
from pathlib import Path

import brownie
import ccxt
from brownie import (
    Contract,
    LibSoFeeCelerV1,
    CelerFacet,
    SoDiamond,
)

from scripts.helpful_scripts import change_network, get_account, read_json


def print_price_ratio(network, celer_so_fee):
    print(f"======{network}======")

    change_network(network)
    proxy_celer_fee = Contract.from_abi(
        "LibSoFeeCelerV1", celer_so_fee, LibSoFeeCelerV1.abi
    )
    (r, f) = proxy_celer_fee.getPriceRatio(1)
    print(f"1, ratio={r}, flag={f}")
    (r, f) = proxy_celer_fee.getPriceRatio(10)
    print(f"10, ratio={r}, flag={f}")
    (r, f) = proxy_celer_fee.getPriceRatio(324)
    print(f"324, ratio={r}, flag={f}")
    (r, f) = proxy_celer_fee.getPriceRatio(1101)
    print(f"1101, ratio={r}, flag={f}")
    (r, f) = proxy_celer_fee.getPriceRatio(42161)
    print(f"42161, ratio={r}, flag={f}")


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


def set_price_ratio():
    prices = get_prices()
    ray = 1e27
    multiply = 1.2
    account = get_account()

    data = read_json(Path(__file__).parent.parent.joinpath("export/mainnet/ContractDeployed.json"))
    net = brownie.network.show_active()
    addr = data[net]["LibSoFeeCelerV1"]
    con = Contract.from_abi("LibSoFeeCelerV1", addr, LibSoFeeCelerV1.abi)

    # con.transferOwnership(account.address, {"from": get_account("deploy_key")})

    # For zkevm
    if net in ["mainnet", "arbitrum-main", "zksync2-main", "optimism-main"]:
        con.setPriceRatio(1101, ray, {'from': account})
    elif net in ["bsc-main"]:
        ratio = int(prices["ETH/USDT"] / prices["BNB/USDT"] * ray * multiply)
        con.setPriceRatio(1101, ratio, {'from': account})
    elif net in ["avax-main"]:
        ratio = int(prices["ETH/USDT"] / prices["AVAX/USDT"] * ray * multiply)
        con.setPriceRatio(1101, ratio, {'from': account})
    elif net in ["polygon-main"]:
        ratio = int(prices["ETH/USDT"] / prices["MATIC/USDT"] * ray * multiply)
        con.setPriceRatio(1101, ratio, {'from': account})
    else:
        raise ValueError


def check_price_ratio():
    # print_price_ratio("mainnet", "0xf5110f6211a9202c257602CdFb055B161163a99d")
    #
    # print_price_ratio("optimism-main", "0x19370bE0D726A88d3e6861301418f3daAe3d798E")
    #
    # print_price_ratio("zksync2-main", "0x8bB2d077D0911459d80d5010f85EBa2232ca6d25")

    # print_price_ratio("arbitrum-main", "0x937AfcA1bb914405D37D55130184ac900ce5961f")

    # print_price_ratio("zkevm-main", "0x66F440252fe99454df8F8e1EB7743EA08FE7D8e2")

    print_price_ratio("bsc-main", "0xD7eC4E3DaC58e537Eb24fef4c3F7B011aeA50f30")


def print_nonce(network, so_diamond):
    print(f"======{network}======")

    change_network(network)
    proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)

    print("next_nonce ", proxy_celer.getNonce())


def check_nonce():
    print_nonce("mainnet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("optimism-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("zksync2-main", "0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577")

    print_nonce("bsc-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("polygon-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("arbitrum-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("avax-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_nonce("zkevm-main", "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449")


def print_base_gas(network, so_diamond):
    print(f"======{network}======")

    change_network(network)
    proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)
    print("1 ", proxy_celer.getBaseGas(1))
    print("10 ", proxy_celer.getBaseGas(10))
    print("56 ", proxy_celer.getBaseGas(56))
    print("137 ", proxy_celer.getBaseGas(137))
    print("324 ", proxy_celer.getBaseGas(324))
    print("1101 ", proxy_celer.getBaseGas(1101))
    print("42161 ", proxy_celer.getBaseGas(42161))
    print("43114 ", proxy_celer.getBaseGas(43114))


def set_base_gas(so_diamond=SoDiamond[-1].address):
    network = brownie.network.show_active()
    print(f"======{network}======")

    change_network(network)
    proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)
    account = get_account()

    dst_chain_info = {
        "mainnet": 1,
        "optimism-main": 10,
        "bsc-main": 56,
        "polygon-main": 137,
        "zksync2-main": 324,
        "zkevm-main": 1101,
        "arbitrum-main": 42161,
        "avax-main": 43114,
    }

    base_gas = {
        551250: ["mainnet"],
        700000: ["zkevm-main"],
        1050000: ["bsc-main", "polygon-main", "zksync2-main", "avax-main"],
        6493520: ["optimism-main"],
        4500000: ["arbitrum-main"],
    }

    for gas, dst_chain_nets in base_gas.items():
        dst_chains = [dst_chain_info[net] for net in dst_chain_nets]
        print(f"set net:{dst_chain_nets}, gas:{gas}")
        proxy_celer.setBaseGas(dst_chains, gas, {"from": account})


def check_dst_base_gas():
    print_base_gas("mainnet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("optimism-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("zksync2-main", "0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577")

    print_base_gas("bsc-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("polygon-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("arbitrum-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("avax-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("zkevm-main", "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449")
