from brownie import (
    Contract,
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    LibCorrectSwapV1,
    SerdeFacet,
    LibSoFeeCelerV1,
    CelerFacet,
    network,
    interface,
)

from scripts.helpful_scripts import (
    get_account,
    change_network,
    get_celer_message_bus,
    get_celer_chain_id,
    get_celer_info,
    get_swap_info,
    get_method_signature_by_abi,
    zero_address,
)

FacetCutAction_ADD = 0
FacetCutAction_REPLACE = 1
FacetCutAction_REMOVE = 2


def deploy():
    account = get_account()
    change_network("zkevm-main")

    deploy_facets = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        CelerFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        SerdeFacet,
    ]
    for facet in deploy_facets:
        print(f"deploy {facet._name}.sol...")
        facet.deploy({"from": account})

    print("deploy SoDiamond.sol...")
    SoDiamond.deploy(account, DiamondCutFacet[-1], {"from": account})

    so_fee = 1e-3
    ray = 1e27

    print("deploy LibSoFeeCelerV1.sol...")
    LibSoFeeCelerV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibCorrectSwapV1...")
    LibCorrectSwapV1.deploy({"from": account})

    print("deploy end!")


def initialize():
    change_network("zkevm-main")
    so_diamond = SoDiamond[-1]
    correct_swap = LibCorrectSwapV1[-1]
    celer_fee = LibSoFeeCelerV1[-1]

    account = get_account()

    print(f"SoDiamond Address:{so_diamond}")
    try:
        initialize_cut(account, so_diamond)
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


def compensate_set_celer_base_gas():
    set_celer_base_gas("mainnet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    set_celer_base_gas("optimism-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    set_celer_base_gas("zksync2-main", "0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577")

    set_celer_base_gas("bsc-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    set_celer_base_gas("polygon-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    set_celer_base_gas("arbitrum-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")

    set_celer_base_gas("avax-main", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820")


def compensate_set_price_ratio():
    set_price_ratio("mainnet", "0xf5110f6211a9202c257602CdFb055B161163a99d")

    set_price_ratio("optimism-main", "0x19370bE0D726A88d3e6861301418f3daAe3d798E")

    set_price_ratio("zksync2-main", "0x8bB2d077D0911459d80d5010f85EBa2232ca6d25")

    set_price_ratio("arbitrum-main", "0x937AfcA1bb914405D37D55130184ac900ce5961f")


def reinitialize():
    change_network("zkevm-main")
    so_diamond = "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449"

    account = get_account()

    print(f"SoDiamond Address:{so_diamond}")

    try:
        proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)

        proxy_celer.initCeler(
            "0x9Bb46D5100d2Db4608112026951c9C965b233f4D", 1101, {"from": account}
        )

        proxy_celer.setAllowedAddress(
            "0x9a98a376D30f2c9A0A7332715c15D940dE3da0e2", False, {"from": account}
        )

        proxy_dex = Contract.from_abi(
            "DexManagerFacet",
            "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449",
            DexManagerFacet.abi,
        )

        proxy_dex.addFee(
            "0x9Bb46D5100d2Db4608112026951c9C965b233f4D",
            "0x66F440252fe99454df8F8e1EB7743EA08FE7D8e2",
            {"from": account},
        )
    except Exception as e:
        print(f"initialize_celer fail:{e}")


def set_price_ratio(network, celer_so_fee):
    print(f"====={network}=====")
    account = get_account()
    change_network(network)

    proxy_celer_fee = Contract.from_abi(
        "LibSoFeeCelerV1", celer_so_fee, LibSoFeeCelerV1.abi
    )

    proxy_celer_fee.setPriceRatio(1011, 1e27, {"from": account})


def set_celer_base_gas(network, so_diamond):
    account = get_account()
    change_network(network)

    base_gas = 700000
    dst_chains = [1101]

    proxy_celer = Contract.from_abi("CelerFacet", so_diamond, CelerFacet.abi)
    print(f"network:{network}, set base gas: {base_gas}, {dst_chains}")

    proxy_celer.setBaseGas(dst_chains, base_gas, {"from": account})


def initialize_cut(account, so_diamond):
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
        reg_facet = reg[-1]
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
    proxy_celer_fee.setPriceRatio(1, 1e27, {"from": account})
    proxy_celer_fee.setPriceRatio(10, 1e27, {"from": account})
    proxy_celer_fee.setPriceRatio(324, 1e27, {"from": account})
    proxy_celer_fee.setPriceRatio(42161, 1e27, {"from": account})


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
