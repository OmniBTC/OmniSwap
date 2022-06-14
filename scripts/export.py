# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import copy
import json
import os

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config, network

from scripts.helpful_scripts import change_network

cur_path = os.path.dirname(os.path.realpath(__file__))


def write_file(file: str, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def export(*arg):
    if len(arg) == 0:
        arg = list(config["networks"].keys())
        del arg[arg.index("default")]
        del arg[arg.index("live")]
        del arg[arg.index("development")]
    output = {}
    swap_router_types = {}
    for net in arg:
        print(f"current net: {net}")
        change_network(net)
        try:
            so_diamond = SoDiamond[-1]
        except:
            continue
        proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
        try:
            stargate_pools = proxy_stargate.getStargateAllPools()
        except:
            stargate_pools = [[], [], []]
        pool_info = []
        for i in range(len(stargate_pools[0])):
            pool_info.append({
                "TokenAddress": stargate_pools[1][i],
                "TokenName": stargate_pools[2][i],
                "PoolId": i + 1
            })
        try:
            weth = config["networks"][net]["weth"]
        except:
            weth = ""
        swap_router = []
        try:
            swap_router_address = config["networks"][net]["swap"][0][0]
            swap_router_type = config["networks"][net]["swap"][0][1]
            swap_router.append({
                "address": swap_router_address,
                "type": swap_router_type
            })
            if swap_router_type not in swap_router_types:
                write_file(os.path.join(os.path.dirname(cur_path), f"export/abi/{swap_router_type}.json"),
                           getattr(interface, swap_router_type).abi)
            swap_router_types[swap_router_type] = True
        except:
            pass
        output[net] = {
            "SoDiamond": so_diamond.address,
            "ChainId": network.chain.id,
            "StargateRouter": config["networks"][net]["stargate_router"],
            "StargateChainId": config["networks"][net]["stargate_chainid"],
            "StargatePool": pool_info,
            "WETH": weth,
            "UniswapRouter": swap_router
        }
    write_file(os.path.join(os.path.dirname(cur_path), "export/SoOmnichainInfo.json"), output)
    write_file(os.path.join(os.path.dirname(cur_path), "export/abi/SoDiamond.json"),
               StargateFacet.abi + GenericSwapFacet.abi)
