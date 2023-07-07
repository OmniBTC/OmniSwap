from brownie import (
    Contract,
    LibSoFeeCelerV1,
    CelerFacet,
)

from scripts.helpful_scripts import change_network


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


def check_price_ratio():
    print_price_ratio("mainnet", "0xf5110f6211a9202c257602CdFb055B161163a99d")

    print_price_ratio("optimism-main", "0x19370bE0D726A88d3e6861301418f3daAe3d798E")

    print_price_ratio("zksync2-main", "0x8bB2d077D0911459d80d5010f85EBa2232ca6d25")

    print_price_ratio("arbitrum-main", "0x937AfcA1bb914405D37D55130184ac900ce5961f")

    print_price_ratio("zkevm-main", "0x66F440252fe99454df8F8e1EB7743EA08FE7D8e2")


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


def check_dst_base_gas():
    print_base_gas("mainnet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("optimism-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("zksync2-main", "0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577")

    print_base_gas("bsc-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("polygon-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("arbitrum-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("avax-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    print_base_gas("zkevm-main", "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449")
