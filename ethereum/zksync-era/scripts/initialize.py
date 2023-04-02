import json

from brownie import (
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    StargateFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    Contract,
    network,
    interface,
    LibSoFeeStargateV1,
    LibCorrectSwapV1,
    SerdeFacet,
)

from scripts.helpful_scripts import (
    get_method_signature_by_abi,
    zero_address,
    change_network,
    get_account,
    get_swap_info,
    get_stargate_router,
    get_stargate_chain_id,
)

FacetCutAction_ADD = 0
FacetCutAction_REPLACE = 1
FacetCutAction_REMOVE = 2

DEPLOYED = "./deployed.json"


def read_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        print(f"Err: open {file}")
        return []


def get_deployed_contracts():
    return read_json(DEPLOYED)


def initialize_cut(account, so_diamond, contracts):
    proxy_cut = Contract.from_abi("DiamondCutFacet", so_diamond, DiamondCutFacet.abi)
    register_funcs = {}
    register_contract = [
        DiamondLoupeFacet,
        DexManagerFacet,
        OwnershipFacet,
        StargateFacet,
        WithdrawFacet,
        GenericSwapFacet,
        SerdeFacet,
    ]
    register_data = []
    for reg in register_contract:
        print(f"Initialize {reg._name}...")
        reg_facet = contracts[reg._name]
        reg_funcs = get_method_signature_by_abi(reg.abi)
        for func_name in list(reg_funcs.keys()):
            if func_name in register_funcs:
                if reg_funcs[func_name] in register_funcs[func_name]:
                    print(f"function:{func_name} has been register!")
                    del reg_funcs[func_name]
                else:
                    register_funcs[func_name].append(reg_funcs[func_name])
            else:
                register_funcs[func_name] = [reg_funcs[func_name]]
        register_data.append([reg_facet, FacetCutAction_ADD, list(reg_funcs.values())])
    proxy_cut.diamondCut(register_data, zero_address(), b"", {"from": account})


def initialize_stargate(account, so_diamond):
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond, StargateFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init stargate...")
    proxy_stargate.initStargate(
        get_stargate_router(), get_stargate_chain_id(), {"from": account}
    )


def initialize_dex_manager(account, so_diamond, correct_swap, stargate_fee):
    proxy_dex = Contract.from_abi("DexManagerFacet", so_diamond, DexManagerFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init dex manager...")
    dexs = []
    sigs = []
    proxy_dex.addCorrectSwap(correct_swap, {"from": account})
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
        reg_funcs = get_method_signature_by_abi(getattr(interface, swap_type).abi)
        for sig in reg_funcs.values():
            sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {"from": account})
    proxy_dex.batchSetFunctionApprovalBySignature(sigs, True, {"from": account})
    # register fee lib
    proxy_dex.addFee(get_stargate_router(), stargate_fee, {"from": account})


def main():
    change_network("zksync2-test")
    contracts = get_deployed_contracts()
    so_diamond = contracts["SoDiamond"]
    correct_swap = contracts["LibCorrectSwapV1"]
    stargate_fee = contracts["LibSoFeeStargateV1"]

    account = get_account()

    print(f"SoDiamond Address:{so_diamond}")
    try:
        initialize_cut(account, so_diamond, contracts)
    except Exception as e:
        print(f"initialize_cut fail:{e}")

    try:
        initialize_stargate(account, so_diamond)
    except Exception as e:
        print(f"initialize_stargate fail:{e}")

    try:
        initialize_dex_manager(account, so_diamond, correct_swap, stargate_fee)
    except Exception as e:
        print(f"initialize_dex_manager fail:{e}")
