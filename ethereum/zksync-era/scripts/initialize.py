import json

from brownie import (
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    CelerFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    Contract,
    network,
    interface,
    LibSoFeeCelerV1,
    LibCorrectSwapV1,
    SerdeFacet,
)

from scripts.helpful_scripts import (
    get_method_signature_by_abi,
    zero_address,
    change_network,
    get_account,
    get_swap_info,
    get_celer_info,
    get_celer_chain_id,
    get_celer_message_bus,
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
        CelerFacet,
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


def initialize_celer(account, so_diamond):
    proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init celer...")
    proxy_celer.initCeler(
        get_celer_message_bus(), get_celer_chain_id(), {"from": account}
    )

    # setBaseGas
    gas = get_celer_info()["gas"]
    base_gas = gas["base_gas"]
    dst_chains = gas["dst_chainid"]

    print(f"network:{net}, set base gas: {base_gas}, {dst_chains}")

    proxy_celer.setBaseGas(dst_chains, base_gas, {"from": account})


def initialize_celer_fee(account, celer_fee):
    proxy_celer_fee = Contract.from_abi(
        "LibSoFeeCelerV1", celer_fee, LibSoFeeCelerV1.abi
    )
    proxy_celer_fee.setPriceRatio(1, 1, {"from": account})
    proxy_celer_fee.setPriceRatio(10, 1, {"from": account})
    proxy_celer_fee.setPriceRatio(42161, 1, {"from": account})


def initialize_dex_manager(account, so_diamond, correct_swap, celer_fee):
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
    proxy_dex.addFee(get_celer_message_bus(), celer_fee, {"from": account})


def main():
    change_network("zksync2-main")
    contracts = get_deployed_contracts()
    so_diamond = contracts["SoDiamond"]
    correct_swap = contracts["LibCorrectSwapV1"]
    celer_fee = contracts["LibSoFeeCelerV1"]

    account = get_account()

    print(f"SoDiamond Address:{so_diamond}")
    try:
        initialize_cut(account, so_diamond, contracts)
    except Exception as e:
        print(f"initialize_cut fail:{e}")

    try:
        initialize_celer(account, so_diamond)
    except Exception as e:
        print(f"initialize_celer fail:{e}")

    try:
        initialize_celer_fee(account, celer_fee)
    except Exception as e:
        print(f"initialize_celer_fee fail:{e}")

    try:
        initialize_dex_manager(account, so_diamond, correct_swap, celer_fee)
    except Exception as e:
        print(f"initialize_dex_manager fail:{e}")
