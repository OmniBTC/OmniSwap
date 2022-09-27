# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import json
import os

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, ERC20, LibSwap, config, LibSoFeeV01, LibCorrectSwapV1

from scripts.helpful_scripts import change_network, zero_address, read_json, get_stargate_router, get_token_address, \
    get_swap_info, get_stargate_chain_id

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omni_swap_file = os.path.join(root_path, "export/OmniSwapInfo.json")
stragate_file = os.path.join(root_path, "export/StargateInfo.json")
deployed_file = os.path.join(root_path, "export/ContractDeployed.json")


def write_file(file: str, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def get_stragate_pool_infos():
    try:
        stargate_router_address = get_stargate_router()
    except:
        return []
    stargate_router = Contract.from_abi("IStargate", stargate_router_address, interface.IStargate.abi)
    bridge_address = stargate_router.bridge()
    bridge = Contract.from_abi("IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi("ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    ultra_light_node_address = endpoint.defaultSendLibrary()
    factory_address = stargate_router.factory()
    factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pools_length = factory.allPoolsLength()
    all_stragate_info = {
        "router": stargate_router_address,
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


def get_stargate_pair_chain_path(omni_swap_infos, net1, net2):
    print(f"Get stargate pair chain path net1:{net1}, net2:{net2}")
    change_network(net1)
    try:
        stargate_router_address = get_stargate_router()
    except:
        return
    stargate_router = Contract.from_abi("IStargate", stargate_router_address, interface.IStargate.abi)
    factory_address = stargate_router.factory()
    factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
    for src_pool_info in omni_swap_infos[net1]["StargatePool"]:
        pool_address = factory.getPool(src_pool_info["PoolId"])
        pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
        for dst_pool_info in omni_swap_infos[net2]["StargatePool"]:
            flag = False
            try:
                result = pool.getChainPath(omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"])
                flag = result[0]
            except:
                pass
            if not flag:
                continue
            if "ChainPath" not in src_pool_info:
                src_pool_info["ChainPath"] = []
            src_pool_info["ChainPath"].append((omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"]))


def get_stargate_chain_path():
    omni_swap_infos = read_json(omni_swap_file)
    nets = list(omni_swap_infos.keys())
    for net1 in nets:
        for net2 in nets:
            if net1 == net2:
                continue
            if ("main" in net1 and "main" not in net2) or ("main" not in net1 and "main" in net2):
                continue
            get_stargate_pair_chain_path(omni_swap_infos, net1, net2)
    write_file(omni_swap_file, omni_swap_infos)


def export_deployed():
    deployed_contract = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet,
                         WithdrawFacet, OwnershipFacet, GenericSwapFacet, SoDiamond, LibSoFeeV01,
                         LibCorrectSwapV1]
    return {v._name: v[-1].address for v in deployed_contract}


def export(*arg):
    if len(arg) == 0:
        arg = list(config["networks"].keys())
        del arg[arg.index("default")]
        del arg[arg.index("live")]
        del arg[arg.index("development")]
    omni_swap_infos = read_json(omni_swap_file)
    stargate_infos = read_json(stragate_file)
    deployed_contracts = read_json(deployed_file)
    swap_types = {}
    for net in arg:
        print(f"current net: {net}")
        change_network(net)
        try:
            so_diamond = SoDiamond[-1]
        except:
            continue
        if "main" in net:
            deployed_contracts[net] = export_deployed()
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
                swap_token_list = cur_swap.get("token_list", "")
                quoter_address = cur_swap.get("quoter", "")
                swap_name = cur_swap.get("name", "")
                swap_router.append({
                    "Name": swap_name,
                    "RouterAddress": swap_router_address,
                    "Type": swap_type,
                    "TokenList": swap_token_list,
                    "QuoterAddressForUniswapV3": quoter_address
                })
                if swap_type not in swap_types:
                    write_file(os.path.join(root_path, f"export/abi/{swap_type}.json"),
                               getattr(interface, swap_type).abi)
                swap_types[swap_type] = True
            write_file(os.path.join(root_path, f"export/abi/IQuoter.json"), getattr(interface, "IQuoter").abi)
        except:
            pass

        omni_swap_infos[net] = {
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
    write_file(deployed_file, deployed_contracts)
    write_file(omni_swap_file, omni_swap_infos)
    write_file(stragate_file, stargate_infos)
    write_file(os.path.join(root_path, "export/abi/IStargate.json"), interface.IStargate.abi)
    write_file(os.path.join(root_path, "export/abi/SoDiamond.json"), so_diamond_abi)
    get_stargate_chain_path()
