# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import json
import os

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, ERC20, LibSwap, config

from scripts.helpful_scripts import change_network, zero_address, read_abi, get_stargate_router, get_token_address, \
    get_swap_info, get_stargate_chain_id

cur_path = os.path.dirname(os.path.realpath(__file__))


def write_file(file: str, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def get_stragate_pool_infos():
    try:
        stargate_router = get_stargate_router()
    except:
        return []
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    bridge_address = stragate.bridge()
    bridge = Contract.from_abi("IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi("ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    ultra_light_node_address = endpoint.defaultSendLibrary()
    factory_address = stragate.factory()
    factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pools_length = factory.allPoolsLength()
    all_stragate_info = {
        "router": stargate_router,
        "bridge": bridge_address,
        "endpoint": endpoint_address,
        "ultra_light_node": ultra_light_node_address,
        "factory": factory_address
    }
    pool_info = []
    for i in range(0, pools_length):
        pool_address = factory.allPools(i)
        if pool_address == zero_address():
            continue
        pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
        pool_id = pool.poolId()
        token_address = pool.token()
        token = Contract.from_abi("ERC20", token_address, ERC20.abi)
        pool_info.append({
            "TokenAddress": token_address,
            "TokenName": token.symbol(),
            "Decimal": token.decimals(),
            "PoolId": pool_id
        })
    all_stragate_info["pools"] = pool_info
    return pool_info, all_stragate_info


# check stargate pool
def check_stargate_pool(
        so_omnichain_info: str = os.path.join(os.path.dirname(cur_path), "export/SoOmnichainInfo.json")):
    output = read_abi(so_omnichain_info)
    nets = list(output.keys())
    for net1 in nets:
        for net2 in nets:
            if net1 == net2:
                continue
            if ("main" in net1 and "main" not in net2) or ("main" not in net1 and "main" in net2):
                continue
            print(f"net1:{net1}, net2:{net2}")
            change_network(net1)
            try:
                stargate_router = get_stargate_router()
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
    stargate_infos = {}
    swap_types = {}
    for net in arg:
        print(f"current net: {net}")
        change_network(net)
        try:
            so_diamond = SoDiamond[-1]
        except:
            continue
        pool_info, stargate_info = get_stragate_pool_infos()
        stargate_infos[net] = stargate_info
        try:
            weth = get_token_address("weth")
        except:
            weth = ""
        swap_router = []
        try:
            swap_info = get_swap_info()
            for swap_type in swap_info:
                cur_swap = swap_info[swap_type]
                swap_router_address = cur_swap["router"]
                if "token_list" in cur_swap:
                    swap_token_list = cur_swap["token_list"]
                else:
                    swap_token_list = ""
                try:
                    quoter_address = cur_swap["quoter"]
                except:
                    quoter_address = ""
                try:
                    swap_name = cur_swap["name"]
                except:
                    swap_name = ""
                swap_router.append({
                    "Name": swap_name,
                    "RouterAddress": swap_router_address,
                    "Type": swap_type,
                    "TokenList": swap_token_list,
                    "QuoterAddressForUniswapV3": quoter_address
                })
                if swap_type not in swap_types:
                    write_file(os.path.join(os.path.dirname(cur_path), f"export/abi/{swap_type}.json"),
                               getattr(interface, swap_type).abi)
                swap_types[swap_type] = True
            write_file(os.path.join(os.path.dirname(cur_path), f"export/abi/IQuoter.json"),
                       getattr(interface, "IQuoter").abi)
        except:
            pass

        output[net] = {
            "SoDiamond": so_diamond.address,
            "ChainId": config["networks"][net]["chainid"],
            "StargateRouter": get_stargate_router(),
            "StargateChainId": get_stargate_chain_id(),
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
    write_file(os.path.join(os.path.dirname(cur_path), "export/StargateInfo.json"), stargate_infos)
    write_file(os.path.join(os.path.dirname(cur_path), "export/abi/IStargate.json"), interface.IStargate.abi)
    write_file(os.path.join(os.path.dirname(cur_path), "export/abi/SoDiamond.json"), so_diamond_abi)
    check_stargate_pool()
