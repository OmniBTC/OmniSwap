# @Time    : 2022/6/6 10:51
# @Author  : WeiDai
# @FileName: initialize.py
from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, config

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    so_diamond = SoDiamond[-1]
    print(f"SoDiamond:{so_diamond}")
    initialize_cut(account, so_diamond)
    initialize_stargate(account, so_diamond)


def initialize_cut(account, so_diamond):
    proxy_cut = Contract.from_abi("DiamondCutFacet", so_diamond.address, DiamondCutFacet.abi)
    zero_addr = "0x0000000000000000000000000000000000000000"

    print("init loupe...")
    loupe = DiamondLoupeFacet[-1]
    loupe_funcs = list(config["signatures"][loupe._name].values())
    proxy_cut.diamondCut([[loupe, 0, loupe_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )

    print("init dex manager...")
    dex_manager = DexManagerFacet[-1]
    dex_manager_funcs = list(config["signatures"][dex_manager._name].values())
    proxy_cut.diamondCut([[dex_manager, 0, dex_manager_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )

    print("init ownership...")
    ownership = OwnershipFacet[-1]
    ownership_funcs = list(config["signatures"][ownership._name].values())
    proxy_cut.diamondCut([[ownership, 0, ownership_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )

    print("init generic swap...")
    generic_swap = GenericSwapFacet[-1]
    generic_swap_funcs = list(config["signatures"][generic_swap._name].values())
    proxy_cut.diamondCut([[generic_swap, 0, generic_swap_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )

    print("init stargate...")
    stargate = StargateFacet[-1]
    stargate_funcs = list(config["signatures"][stargate._name].values())
    proxy_cut.diamondCut([[stargate, 0, stargate_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )

    print("init withdraw...")
    withdraw = WithdrawFacet[-1]
    withdraw_funcs = list(config["signatures"][withdraw._name].values())
    proxy_cut.diamondCut([[withdraw, 0, withdraw_funcs]],
                         zero_addr,
                         b'',
                         {'from': account}
                         )


def initialize_stargate(account, so_diamond):
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init stargate...")
    proxy_stargate.initStargate(
        config["networks"][net]["stargate_router"],
        config["networks"][net]["stargate_chainid"],
        {'from': account}
    )
