# @Time    : 2022/6/14 13:57
# @Author  : WeiDai
# @FileName: export.py
import contextlib
import functools
import json
import multiprocessing
import os
import traceback
from pathlib import Path
from pprint import pprint

try:
    from brownie import (
        DiamondCutFacet,
        SoDiamond,
        DiamondLoupeFacet,
        DexManagerFacet,
        StargateFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        CoreBridgeFacet,
        interface,
        Contract,
        ERC20,
        LibSwap,
        config,
        LibSoFeeStargateV1,
        LibCorrectSwapV1,
        WormholeFacet,
        LibSoFeeWormholeV1,
        SerdeFacet,
        network,
        CelerFacet,
        LibSoFeeCelerV1,
        MultiChainFacet,
        LibSoFeeMultiChainV1,
        BoolFacet, project
    )
except:
    pass
from sui_brownie.parallelism import ProcessExecutor

from scripts.helpful_scripts import (
    change_network,
    get_wormhole_bridge,
    get_wormhole_chainid,
    zero_address,
    read_json,
    get_stargate_router,
    get_token_address,
    get_swap_info,
    get_stargate_chain_id,
)

from scripts.wormhole import (
    get_all_warpped_token,
    get_native_token_name,
    get_net_from_wormhole_chainid,
    get_usdc_address,
    get_usdt_address,
)

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omni_swap_file = os.path.join(root_path, "export/OmniSwapInfo.json")
stragate_file = os.path.join(root_path, "export/StargateInfo.json")
deployed_file = os.path.join(root_path, "export/ContractDeployed.json")

mainnet_swap_file = os.path.join(root_path, "export/mainnet/OmniSwapInfo.json")
lock = multiprocessing.Lock()


def write_file(file: str, data):
    print("save to:", file)
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def fit_mainnet_stargate_chain_path():
    omni_swap_infos = read_json(omni_swap_file)
    mainnet_swap_infos = read_json(mainnet_swap_file)
    nets = list(omni_swap_infos.keys())
    for net in nets:
        if "main" in net:
            print(f"replace {net} stargate pool")
            try:
                omni_swap_infos[net]["StargatePool"] = mainnet_swap_infos[net][
                    "StargatePool"
                ]
            except Exception:
                continue
    write_file(omni_swap_file, omni_swap_infos)


def get_stragate_pool_infos():
    omni_swap_infos = read_json(mainnet_swap_file)
    stargate_router_address = get_stargate_router()
    if stargate_router_address == "":
        return [], []

    stargate_router = Contract.from_abi(
        "IStargate", stargate_router_address, interface.IStargate.abi
    )
    bridge_address = stargate_router.bridge()
    bridge = Contract.from_abi(
        "IStargateBridge", bridge_address, interface.IStargateBridge.abi
    )
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi(
        "ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi
    )
    ultra_light_node_address = endpoint.defaultSendLibrary()
    factory_address = stargate_router.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, interface.IStargateFactory.abi
    )
    pools_length = factory.allPoolsLength()
    all_stragate_info = {
        "router": stargate_router_address,
        "bridge": bridge_address,
        "endpoint": endpoint_address,
        "ultra_light_node": ultra_light_node_address,
        "factory": factory_address,
    }
    pool_info = []
    for i in range(pools_length):
        pool_address = factory.allPools(i)
        if pool_address == zero_address():
            continue
        pool = Contract.from_abi(
            "IStargatePool", pool_address, interface.IStargatePool.abi
        )
        pool_id = pool.poolId()
        token_address = pool.token()
        token = Contract.from_abi("ERC20", token_address, ERC20.abi)
        pool_info.append(
            {
                "TokenAddress": token_address,
                "TokenName": token.symbol(),
                "Decimal": token.decimals(),
                "PoolId": pool_id,
            }
        )
    all_stragate_info["pools"] = pool_info
    pprint(all_stragate_info)
    omni_swap_infos[network.show_active()]["StargatePool"] = pool_info
    write_file(mainnet_swap_file, omni_swap_infos)
    return pool_info, all_stragate_info


def get_stargate_pair_chain_path(omni_swap_infos, net1, net2):
    from brownie import project, Contract
    p = project.load(project_path=Path(__file__).parent.parent, raise_if_loaded=False)
    p.load_config()
    if "aptos" in net1 or "aptos" in net2:
        return
    change_network(net1)
    stargate_router_address = get_stargate_router()
    if stargate_router_address == "":
        return
    stargate_router = Contract.from_abi(
        "IStargate", stargate_router_address, p.interface.IStargate.abi
    )
    factory_address = stargate_router.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, p.interface.IStargateFactory.abi
    )
    for src_pool_info in omni_swap_infos[net1]["StargatePool"]:
        pool_address = factory.getPool(src_pool_info["PoolId"])
        pool = Contract.from_abi(
            "IStargatePool", pool_address, p.interface.IStargatePool.abi
        )
        if "ChainPath" not in src_pool_info:
            src_pool_info["ChainPath"] = []
        src_pool_info["ChainPath"] = [tuple(d) for d in src_pool_info["ChainPath"]]
        for dst_pool_info in omni_swap_infos[net2]["StargatePool"]:
            flag = False
            try:
                result = pool.getChainPath(
                    omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"]
                )
                flag = result[0]
            except:
                pass
            if not flag:
                continue
            tp = (omni_swap_infos[net2]["StargateChainId"], dst_pool_info["PoolId"])
            if tp not in src_pool_info["ChainPath"]:
                src_pool_info["ChainPath"].append(
                    tp
                )
    with lock:
        data = read_json(mainnet_swap_file)
        data[net1]["StargatePool"] = omni_swap_infos[net1]["StargatePool"]
        write_file(mainnet_swap_file, data)


def get_stargate_net_chain_path(omni_swap_infos, net1, nets):
    for net2 in nets:
        if "StargateChainId" not in omni_swap_infos[net1]:
            continue
        if "StargateChainId" not in omni_swap_infos[net2]:
            continue
        if net1 == net2:
            continue
        print(f"Get stargate pair chain path net1:{net1}, net2:{net2}")
        try:
            get_stargate_pair_chain_path(omni_swap_infos, net1, net2)
        except:
            import traceback
            err = traceback.format_exc()
            print(f"{net1} -- {net2} err:{err}")


# step1: brownie run --network avax-main scripts/export.py get_stragate_pool_infos
# step2: brownie run --network arbitrum-main scripts/export.py get_stargate_chain_path
def get_stargate_chain_path():
    omni_swap_infos = read_json(mainnet_swap_file)
    nets = list(omni_swap_infos.keys())
    pt = ProcessExecutor(executor=len(nets))
    funcs = []
    for net1 in nets:
        funcs.append(functools.partial(get_stargate_net_chain_path, omni_swap_infos, net1, nets))
    pt.run(funcs)
    # write_file(mainnet_swap_file, omni_swap_infos)


def get_wormhole_chain_path(net, wormhole_chain_path):
    change_network(net)
    current_net = net
    net_chain_path = []
    for chain_path in wormhole_chain_path:
        if chain_path["SrcWormholeChainId"] == get_wormhole_chainid():
            net_chain_path.append(chain_path)
        if chain_path["DstWormholeChainId"] == get_wormhole_chainid():
            net_chain_path.append(
                {
                    "SrcWormholeChainId": chain_path["DstWormholeChainId"],
                    "SrcTokenAddress": chain_path["DstTokenAddress"],
                    "DstWormholeChainId": chain_path["SrcWormholeChainId"],
                    "DstTokenAddress": chain_path["SrcTokenAddress"],
                }
            )

    net_support_token = get_wormhole_support_token(current_net)

    weth_chain_path = []
    usdt_chain_path = []
    usdc_chain_path = []
    wrapped_chain_path = []
    for chain_path in net_chain_path:
        if (
                chain_path["SrcTokenAddress"] == zero_address()
                and chain_path["DstTokenAddress"] == zero_address()
        ):
            continue
        if chain_path["SrcTokenAddress"] == zero_address():
            weth_chain_path.append(chain_path)
        elif chain_path["DstTokenAddress"] == zero_address():
            dst_net = get_net_from_wormhole_chainid(chain_path["DstWormholeChainId"])
            dst_native_token = get_native_token_name(dst_net)
            net_support_token.append(
                {
                    "ChainPath": [chain_path],
                    "Decimal": 18,
                    "NativeToken": False,
                    "TokenName": f"W{dst_native_token}",
                }
            )
        elif get_usdt_address(current_net) and chain_path[
            "SrcTokenAddress"
        ] == get_usdt_address(current_net):
            usdt_chain_path.append(chain_path)
        elif get_usdc_address(current_net) and chain_path[
            "SrcTokenAddress"
        ] == get_usdc_address(current_net):
            usdc_chain_path.append(chain_path)
        else:
            wrapped_chain_path.append(chain_path)

    for support_token in net_support_token:
        if support_token["NativeToken"] == True:
            if support_token["TokenName"] == "USDT":
                support_token["ChainPath"] = usdt_chain_path
            if support_token["TokenName"] == "USDC":
                support_token["ChainPath"] = usdc_chain_path

    net_support_token.append(
        {
            "ChainPath": weth_chain_path,
            "Decimal": 18,
            "NativeToken": True,
            "TokenAddress": zero_address(),
            "TokenName": get_native_token_name(current_net),
        }
    )

    wrapped_tokens = []
    for wrapped_token in wrapped_chain_path:
        erc20 = Contract.from_abi("ERC20", wrapped_token["SrcTokenAddress"], ERC20.abi)
        if not wrapped_tokens:
            wrapped_tokens.append(
                {
                    "ChainPath": [wrapped_token],
                    "Decimal": erc20.decimals(),
                    "NativeToken": False,
                    "TokenName": erc20.symbol(),
                }
            )
        else:
            exist_wrapped = False
            for token in wrapped_tokens:
                if token["TokenName"] == erc20.symbol():
                    token["ChainPath"].append(wrapped_token)
                    exist_wrapped = True

            if not exist_wrapped:
                wrapped_tokens.append(
                    {
                        "ChainPath": [wrapped_token],
                        "Decimal": erc20.decimals(),
                        "NativeToken": False,
                        "TokenName": erc20.symbol(),
                    }
                )

    net_support_token.extend(wrapped_tokens)

    return net_support_token


def export_wormhole_chain_path(networks):
    wormhole_chain_path = []
    for net in networks:
        print(f"[export_wormhole_chain_path] current net: {net}")
        try:
            change_network(net)
            wormhole_chain_path.extend(get_all_warpped_token())
        except Exception:
            continue

    omni_swap_infos = read_json(omni_swap_file)
    for net in networks:
        if "aptos" in net:
            continue
        net_support_token = get_wormhole_chain_path(net, wormhole_chain_path)
        try:
            omni_swap_infos[net]["WormholeSupportToken"] = net_support_token
        except Exception:
            omni_swap_infos[net].append({"WormholeSupportToken": []})
            omni_swap_infos[net]["WormholeSupportToken"] = net_support_token
    write_file(omni_swap_file, omni_swap_infos)


# Modify the NativeToken information manually,
# add the newly added chain information, and
# import the WrappedToken information automatically.
def reexport_wormhole_chainpath():
    reexport_file = mainnet_swap_file
    omni_swap_infos = read_json(reexport_file)

    support_tokens = {}
    native_tokens = []
    all_networks = list(omni_swap_infos.keys())
    networks = []
    for net in all_networks:
        if "WormholeSupportToken" in omni_swap_infos[net]:
            networks.append(net)

    print(networks)

    for net in networks:
        tokens = []
        for token in omni_swap_infos[net]["WormholeSupportToken"]:
            if token["NativeToken"]:
                native_tokens.append(token)
                tokens.append(token)
        support_tokens[net] = tokens

    for net in networks:
        wrapped_tokens = []
        for native_token in native_tokens:
            wrapped_chain_paths = []

            for path in native_token["ChainPath"]:
                # todo! add mapping wormhole chain id -> chain name
                dst_net = get_net_from_wormhole_chainid(path["DstWormholeChainId"])
                if dst_net == net:
                    wrapped_chain_paths.append(
                        {
                            "DstTokenAddress": path["SrcTokenAddress"],
                            "DstWormholeChainId": path["SrcWormholeChainId"],
                            "SrcTokenAddress": path["DstTokenAddress"],
                            "SrcWormholeChainId": path["DstWormholeChainId"],
                        }
                    )

            if len(wrapped_chain_paths) > 0:
                src_token_address = wrapped_chain_paths[0]["SrcTokenAddress"]
                src_wormhole_chain_id = wrapped_chain_paths[0]["SrcWormholeChainId"]
                for path in native_token["ChainPath"]:
                    if src_wormhole_chain_id != path["DstWormholeChainId"]:
                        wrapped_chain_paths.append(
                            {
                                "DstTokenAddress": path["DstTokenAddress"],
                                "DstWormholeChainId": path["DstWormholeChainId"],
                                "SrcTokenAddress": src_token_address,
                                "SrcWormholeChainId": src_wormhole_chain_id,
                            }
                        )

                token_name = native_token["TokenName"]
                native_net = get_net_from_wormhole_chainid(
                    native_token["ChainPath"][0]["SrcWormholeChainId"]
                )
                if token_name in ["USDT", "USDC"]:
                    net_suffix = "eth"
                    if native_net != "mainnet":
                        net_suffix = native_net.split("-")[0]

                    wrapped_tokens.append(
                        {
                            "ChainPath": wrapped_chain_paths,
                            "Decimal": native_token["Decimal"],
                            "NativeToken": False,
                            "TokenName": f"{token_name}{net_suffix}",
                        }
                    )
                else:
                    wrapped_tokens.append(
                        {
                            "ChainPath": wrapped_chain_paths,
                            "Decimal": native_token["Decimal"],
                            "NativeToken": False,
                            "TokenName": f"W{token_name}",
                        }
                    )
        support_tokens[net].extend(wrapped_tokens)

    for net in networks:
        omni_swap_infos[net]["WormholeSupportToken"] = support_tokens[net]
    write_file(reexport_file, omni_swap_infos)


def get_wormhole_support_token(net):
    return [
        {
            "ChainPath": [],
            "TokenName": token.upper(),
            "NativeToken": True,
            "TokenAddress": config["networks"][net]["token"][token]["address"],
            "Decimal": config["networks"][net]["token"][token]["decimal"],
        }
        for token in config["networks"][net]["token"]
        if token in ["usdt", "usdc"]
    ]


def export_deployed():
    deployed_contract = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        StargateFacet,
        CelerFacet,
        MultiChainFacet,
        WormholeFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        SoDiamond,
        LibSoFeeStargateV1,
        LibSoFeeWormholeV1,
        LibSoFeeCelerV1,
        LibSoFeeMultiChainV1,
        LibCorrectSwapV1,
        SerdeFacet,
    ]
    out = {}
    for v in deployed_contract:
        if v._name == "LibSoFeeStargateV1":
            if network.show_active() in [
                "avax-main",
                "polygon-main",
                "bsc-main",
                "mainnet",
            ]:
                out[v._name] = "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449"
            continue
        try:
            out[v._name] = v[-1].address
        except:
            continue
    return out


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
                swap_router.append(
                    {
                        "Name": swap_name,
                        "RouterAddress": swap_router_address,
                        "Type": swap_type,
                        "TokenList": swap_token_list,
                        "QuoterAddressForUniswapV3": quoter_address,
                    }
                )
                if swap_type not in swap_types:
                    write_file(
                        os.path.join(root_path, f"export/abi/{swap_type}.json"),
                        getattr(interface, swap_type).abi,
                    )
                swap_types[swap_type] = True
            write_file(
                os.path.join(root_path, "export/abi/IQuoter.json"),
                getattr(interface, "IQuoter").abi,
            )
        omni_swap_infos[net] = {
            "OmniBtcChainId": config["networks"][net]["omnibtc_chainid"],
            "SoDiamond": so_diamond.address,
            "ChainId": config["networks"][net]["chainid"],
            "WormholeBridge": get_wormhole_bridge(),
            "WormholeChainId": get_wormhole_chainid(),
            "WormholeSupportToken": get_wormhole_support_token(net),
            "StargateRouter": get_stargate_router(),
            "StargateChainId": get_stargate_chain_id(),
            "StargatePool": pool_info,
            "WETH": weth,
            "UniswapRouter": swap_router,
        }
    facets = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        StargateFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        WormholeFacet,
        SerdeFacet,
        CelerFacet,
        MultiChainFacet,
    ]
    libs = [LibSwap]
    so_diamond_abi = []
    for f in facets + libs:
        so_diamond_abi += f.abi

    write_file(deployed_file, deployed_contracts)


def new_export(*args):
    networks = select_networks(args)

    export_so_diamond_abi()
    export_stargate_abi()
    export_celer_abi()
    export_multichain_abi()
    export_swap_abi(networks)
    export_deployed_contracts(networks)

    # export_stargate_info(networks)
    # export_omniswap_info(networks)


def export_so_diamond_abi():
    contrats = [
        # facets
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        StargateFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        WormholeFacet,
        SerdeFacet,
        CelerFacet,
        MultiChainFacet,
        BoolFacet,
        CoreBridgeFacet,
        # libs
        LibSwap,
    ]

    so_diamond_abi = []
    for c in contrats:
        so_diamond_abi += c.abi

    write_file(os.path.join(root_path, "export/abi/SoDiamond.json"), so_diamond_abi)


def export_stargate_abi():
    write_file(
        os.path.join(root_path, "export/abi/IStargate.json"), interface.IStargate.abi
    )


def export_celer_abi():
    write_file(
        os.path.join(root_path, "export/abi/ICelerBridge.json"),
        interface.ICelerBridge.abi,
    )


def export_multichain_abi():
    write_file(
        os.path.join(root_path, "export/abi/IMultiChainV7Router.json"),
        interface.IMultiChainV7Router.abi,
    )


def export_swap_abi(networks):
    swap_types = {}

    for net in networks:
        print(f"[export_swap_abi] current net: {net}")

        try:
            change_network(net)
        except:
            continue

        with contextlib.suppress(Exception):
            swap_info = get_swap_info()

            for swap_type in swap_info:
                if swap_type not in swap_types:
                    write_file(
                        os.path.join(root_path, f"export/abi/{swap_type}.json"),
                        getattr(interface, swap_type).abi,
                    )
                swap_types[swap_type] = True

    write_file(
        os.path.join(root_path, "export/abi/IQuoter.json"),
        getattr(interface, "IQuoter").abi,
    )


def export_deployed_contracts(networks):
    deployed_contracts = {}

    for net in networks:
        print(f"[export_deployed_contracts] current net: {net}")

        try:
            change_network(net)
            deployed_contracts[net] = export_deployed()
        except:
            traceback.print_exc()

    write_file(deployed_file, deployed_contracts)


def export_stargate_info(networks):
    stargate_infos = {}
    for net in networks:
        print(f"[export_stargate_info] current net: {net}")

        try:
            change_network(net)
            _pool_info, stargate_info = get_stragate_pool_infos()
            stargate_infos[net] = stargate_info
        except:
            continue

    write_file(stragate_file, stargate_infos)


def export_omniswap_info(networks=["base-main"]):
    omni_swap_infos = {}

    for net in networks:
        print(f"[export_omniswap_info] current net: {net}")

        try:
            change_network(net)
            so_diamond = SoDiamond[-1]
            pool_info, _stargate_info = get_stragate_pool_infos()
        except:
            continue

        try:
            weth = get_token_address("weth")
        except:
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

                swap_router.append(
                    {
                        "Name": swap_name,
                        "RouterAddress": swap_router_address,
                        "Type": swap_type,
                        "TokenList": swap_token_list,
                        "QuoterAddressForUniswapV3": quoter_address,
                    }
                )

        omni_swap_infos[net] = {
            "OmniBtcChainId": config["networks"][net]["omnibtc_chainid"],
            "SoDiamond": so_diamond.address,
            "ChainId": config["networks"][net]["chainid"],
            # "WormholeBridge": get_wormhole_bridge(),
            # "WormholeChainId": get_wormhole_chainid(),
            # "WormholeSupportToken": get_wormhole_support_token(net),
            "StargateRouter": get_stargate_router(),
            "StargateChainId": get_stargate_chain_id(),
            "StargatePool": pool_info,
            "WETH": weth,
            "UniswapRouter": swap_router,
        }

    write_file(omni_swap_file, omni_swap_infos)


def export_celer():
    deployed_contracts = {}
    for net in ["goerli", "avax-test"]:
        change_network(net)
        deployed_contracts[net] = export_deployed()
    write_file("celer_test_contracts.json", deployed_contracts)


def select_networks(args):
    main_networks = [
        # "aptos-mainnet",
        "mainnet",
        "bsc-main",
        "avax-main",
        "polygon-main",
        "arbitrum-main",
        "optimism-main",
        # "ftm-main",
    ]

    test_networks = [
        # "aptos-testnet",
        # "goerli",
        "bsc-test",
        # "avax-test",
        "polygon-test",
        # "arbitrum-test",
        # "optimism-test",
        # "ftm-test",
    ]

    export_networks = []

    if len(args) != 0 and args[0] == "main":
        export_networks.extend(main_networks)
    elif len(args) != 0 and args[0] == "test":
        export_networks.extend(test_networks)
    else:
        export_networks.extend(test_networks)

    print(export_networks)

    return export_networks


if __name__ == "__main__":
    pass
