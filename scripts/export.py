# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import json
import os

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config, network, ERC20, LibSwap

from scripts.helpful_scripts import change_network, zero_address, read_abi

cur_path = os.path.dirname(os.path.realpath(__file__))


def write_file(file: str, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def get_stragate_pool_infos(net):
    try:
        stargate_router = config["networks"][net]["stargate_router"]
    except:
        return []
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    factory_address = stragate.factory()
    factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pools_length = factory.allPoolsLength()
    pool_info = []
    for i in range(1, pools_length + 1):
        pool_address = factory.getPool(i)
        if pool_address == zero_address():
            continue
        pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
        token_address = pool.token()
        token = Contract.from_abi("ERC20", token_address, ERC20.abi)
        pool_info.append({
            "TokenAddress": token_address,
            "TokenName": token.symbol(),
            "PoolId": i
        })
    return pool_info


# check stargate pool
def check_stargate_pool(
        so_omnichain_info: str = os.path.join(os.path.dirname(cur_path), "export/SoOmnichainInfo.json")):
    output = read_abi(so_omnichain_info)
    nets = list(output.keys())
    for net1 in nets:
        change_network(net1)
        for net2 in nets:
            if net1 == net2:
                continue
            try:
                stargate_router = config["networks"][net1]["stargate_router"]
            except:
                return
            stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
            factory_address = stragate.factory()
            factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
            for src_pool_info in output[net1]["StargatePool"]:
                pool_address = factory.getPool(src_pool_info["PoolId"])
                pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
                for dst_pool_info in output[net2]["StargatePool"]:
                    flag = False
                    try:
                        result = pool.getChainPath(output[net2]["StargateChainId"],
                                                   dst_pool_info["PoolId"]
                                                   )
                        flag = result[0]
                    except:
                        pass
                    if flag:
                        if "ChainPath" not in src_pool_info:
                            src_pool_info["ChainPath"] = []
                        src_pool_info["ChainPath"].append((output[net2]["StargateChainId"], dst_pool_info["PoolId"]))
    write_file(os.path.join(os.path.dirname(cur_path), "export/SoOmnichainInfo.json"), output)


def export(*arg):
    if len(arg) == 0:
        arg = list(config["networks"].keys())
        del arg[arg.index("default")]
        del arg[arg.index("live")]
        del arg[arg.index("development")]
    so_omnichain_info = os.path.join(os.path.dirname(cur_path), "export/SoOmnichainInfo.json")
    output = read_abi(so_omnichain_info)
    swap_router_types = {}
    for net in arg:
        print(f"current net: {net}")
        change_network(net)
        try:
            so_diamond = SoDiamond[-1]
        except:
            continue
        pool_info = get_stragate_pool_infos(net)
        try:
            weth = config["networks"][net]["weth"]
        except:
            weth = ""
        swap_router = []
        try:
            for k in range(len(config["networks"][net]["swap"])):
                swap_router_address = config["networks"][net]["swap"][k][0]
                swap_router_type = config["networks"][net]["swap"][k][1]
                if len(config["networks"][net]["swap"][k]) > 2:
                    swap_token_list = config["networks"][net]["swap"][k][2]
                else:
                    swap_token_list = ""
                swap_router.append({
                    "Address": swap_router_address,
                    "Type": swap_router_type,
                    "TokenList": swap_token_list
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
    facets = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet,
              WithdrawFacet, OwnershipFacet, GenericSwapFacet
              ]
    libs = [LibSwap]
    so_diamond_abi = []
    for f in facets + libs:
        so_diamond_abi += f.abi
    write_file(so_omnichain_info, output)
    write_file(os.path.join(os.path.dirname(cur_path), "export/abi/SoDiamond.json"), so_diamond_abi)
