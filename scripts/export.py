# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config, network

from scripts.helpful_scripts import change_network


def export(*arg):
    output = {}
    for net in arg:
        change_network(net)
        so_diamond = SoDiamond[-1]
        proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
        stargate_pools = proxy_stargate.getStargateAllPools()
        print(stargate_pools)
        output[net] = {
            "SoDiamond": so_diamond.address,
            "ChainId": network.chain.id,
            "StargateRouter": config["networks"][net]["stargate_router"],
            "StargateChainId": config["networks"][net]["stargate_chainid"]
        }
    print(output)
