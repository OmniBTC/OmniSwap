# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import contextlib
import json
import os
from pprint import pprint
import re

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, ERC20, LibSwap, config, LibSoFeeStargateV1, LibCorrectSwapV1, \
    WormholeFacet, LibSoFeeWormholeV1, SerdeFacet

from scripts.helpful_scripts import change_network, get_wormhole_bridge, get_wormhole_chainid, zero_address, read_json, get_stargate_router, get_token_address, \
    get_swap_info, get_stargate_chain_id
from scripts.wormhole import get_all_warpped_token, get_native_token_name, get_net_from_wormhole_chainid, get_stable_coin_address

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omni_swap_file = os.path.join(root_path, "export/OmniSwapInfo.json")
stragate_file = os.path.join(root_path, "export/StargateInfo.json")
deployed_file = os.path.join(root_path, "export/ContractDeployed.json")


def write_file(file: str, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def get_stragate_pool_infos():
    stargate_router_address = get_stargate_router()
    if stargate_router_address == "":
        return []
    stargate_router = Contract.from_abi(
        "IStargate", stargate_router_address, interface.IStargate.abi)
    bridge_address = stargate_router.bridge()
    bridge = Contract.from_abi(
        "IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi(
        "ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    ultra_light_node_address = endpoint.defaultSendLibrary()
    factory_address = stargate_router.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pools_length = factory.allPoolsLength()
    all_stragate_info = {
        "router": stargate_router_address,
        "bridge": bridge_address,
        "endpoint": endpoint_address,
        "ultra_light_node": ultra_light_node_address,
        "factory": factory_address
    }
    pool_info = []
    for i in range(pools_length):
        pool_address = factory.allPools(i)
        if pool_address == zero_address():
            continue
        pool = Contract.from_abi(
            "IStargatePool", pool_address, interface.IStargatePool.abi)
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
    stargate_router_address = get_stargate_router()
    if stargate_router_address == "":
        return
    stargate_router = Contract.from_abi(
        "IStargate", stargate_router_address, interface.IStargate.abi)
    factory_address = stargate_router.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, interface.IStargateFactory.abi)
    for src_pool_info in omni_swap_infos[net1]["StargatePool"]:
        pool_address = factory.getPool(src_pool_info["PoolId"])
        pool = Contract.from_abi(
            "IStargatePool", pool_address, interface.IStargatePool.abi)
        for dst_pool_info in omni_swap_infos[net2]["StargatePool"]:
            flag = False
            try:
                result = pool.getChainPath(
                    omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"])
                flag = result[0]
            except:
                pass
            if not flag:
                continue
            if "ChainPath" not in src_pool_info:
                src_pool_info["ChainPath"] = []
            src_pool_info["ChainPath"].append(
                (omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"]))


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


def get_wormhole_chain_path(net, wormhole_chain_path):
    change_network(net)
    current_net = net
    net_chain_path = []
    for chain_path in wormhole_chain_path:
        if chain_path["SrcWormholeChainId"] == get_wormhole_chainid():
            net_chain_path.append(chain_path)
        if chain_path["DstWormholeChainId"] == get_wormhole_chainid():
            net_chain_path.append({
                "SrcWormholeChainId": chain_path["DstWormholeChainId"],
                "SrcTokenAddress": chain_path["DstTokenAddress"],
                "DstWormholeChainId": chain_path["SrcWormholeChainId"],
                "DstTokenAddress": chain_path["SrcTokenAddress"]
            })

    net_support_token = get_wormhole_support_token(current_net)

    (_, stable_token_address) = get_stable_coin_address(current_net)

    weth_chain_path = []
    stable_chain_path = []
    wrapped_chain_path = []
    for chain_path in net_chain_path:
        if chain_path["SrcTokenAddress"] == zero_address() and chain_path["DstTokenAddress"] == zero_address():
            continue
        if chain_path["SrcTokenAddress"] == zero_address():
            weth_chain_path.append(chain_path)
        elif chain_path["DstTokenAddress"] == zero_address():
            dst_net = get_net_from_wormhole_chainid(
                chain_path["DstWormholeChainId"])
            dst_native_token = get_native_token_name(dst_net)
            net_support_token.append({
                'ChainPath': [chain_path],
                'Decimal': 18,
                'NativeToken': False,
                'TokenName': f'W{dst_native_token}'
            })
        elif chain_path["SrcTokenAddress"] == stable_token_address:
            stable_chain_path.append(chain_path)
        else:
            wrapped_chain_path.append(chain_path)

    for support_token in net_support_token:
        if support_token["NativeToken"] == True:
            support_token["ChainPath"] = stable_chain_path

    net_support_token.append({
        'ChainPath': weth_chain_path,
        'Decimal': 18,
        'NativeToken': True,
        'TokenAddress': zero_address(),
        'TokenName': get_native_token_name(current_net)
    })

    wrapped_tokens = []
    for wrapped_token in wrapped_chain_path:
        erc20 = Contract.from_abi(
            "ERC20", wrapped_token["SrcTokenAddress"], ERC20.abi)
        if not wrapped_tokens:
            wrapped_tokens.append({
                'ChainPath': [wrapped_token],
                'Decimal': erc20.decimals(),
                'NativeToken': False,
                'TokenName': erc20.symbol()
            })
        else:
            exist_wrapped = False
            for token in wrapped_tokens:
                if token["TokenName"] == erc20.symbol():
                    token["ChainPath"].append(wrapped_token)
                    exist_wrapped = True

            if not exist_wrapped:
                wrapped_tokens.append({
                    'ChainPath': [wrapped_token],
                    'Decimal': erc20.decimals(),
                    'NativeToken': False,
                    'TokenName': erc20.symbol()
                })

    net_support_token.extend(wrapped_tokens)

    return net_support_token


def export_wormhole_chain_path(wormhole_chain_path):
    omni_swap_infos = read_json(omni_swap_file)
    nets = list(omni_swap_infos.keys())
    for net in nets:
        net_support_token = get_wormhole_chain_path(
            net, wormhole_chain_path)
        omni_swap_infos[net]["WormholeSupportToken"] = net_support_token
    write_file(omni_swap_file, omni_swap_infos)


def get_wormhole_support_token(net):
    return [{"ChainPath": [], "TokenName": token.upper(), "NativeToken": True, "TokenAddress": config["networks"][net]["token"][token]["address"], "Decimal": config["networks"][net]["token"][token]["decimal"]} for token in config["networks"][net]["token"] if token in ["usdc", "usdt"]]


def export_deployed():
    deployed_contract = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WormholeFacet,
                         WithdrawFacet, OwnershipFacet, GenericSwapFacet, SoDiamond, LibSoFeeStargateV1,
                         LibSoFeeWormholeV1, LibCorrectSwapV1, SerdeFacet]
    return {v._name: v[-1].address for v in deployed_contract}


def export(*arg):
    if not arg:
        arg = list(config["networks"].keys())
        del arg[arg.index("default")]
        del arg[arg.index("live")]
        del arg[arg.index("development")]
    omni_swap_infos = read_json(omni_swap_file)
    stargate_infos = read_json(stragate_file)
    deployed_contracts = read_json(deployed_file)
    swap_types = {}
    wormhole_chain_path = []

    for net in arg:
        print(f"current net: {net}")
        change_network(net)

        try:
            wormhole_chain_path.extend(get_all_warpped_token())
        except Exception:
            continue

        try:
            so_diamond = SoDiamond[-1]
        except Exception:
            continue
        deployed_contracts[net] = export_deployed()

        if get_stragate_pool_infos() == []:
            pool_info, stargate_info = ([], [])
        else:
            pool_info, stargate_info = get_stragate_pool_infos()
        stargate_infos[net] = stargate_info
        try:
            weth = get_token_address("weth")
        except Exception:
            weth = ""
        swap_router = []
        with contextlib.suppress(Exception):
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
            write_file(os.path.join(root_path, "export/abi/IQuoter.json"),
                       getattr(interface, "IQuoter").abi)
        omni_swap_infos[net] = {
            "SoDiamond": so_diamond.address,
            "ChainId": config["networks"][net]["chainid"],
            "WormholeBridge": get_wormhole_bridge(),
            "WormholeChainId": get_wormhole_chainid(),
            "WormholeSupportToken": get_wormhole_support_token(net),
            "StargateRouter": get_stargate_router(),
            "StargateChainId": get_stargate_chain_id(),
            "StargatePool": pool_info,
            "WETH": weth,
            "UniswapRouter": swap_router
        }
    facets = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet,
              WithdrawFacet, OwnershipFacet, GenericSwapFacet, WormholeFacet, SerdeFacet
              ]
    libs = [LibSwap]
    so_diamond_abi = []
    for f in facets + libs:
        so_diamond_abi += f.abi

    write_file(deployed_file, deployed_contracts)
    write_file(omni_swap_file, omni_swap_infos)
    write_file(stragate_file, stargate_infos)
    write_file(os.path.join(root_path, "export/abi/IStargate.json"),
               interface.IStargate.abi)
    write_file(os.path.join(
        root_path, "export/abi/SoDiamond.json"), so_diamond_abi)
    export_wormhole_chain_path(wormhole_chain_path)
    get_stargate_chain_path()
