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
    MockToken,
    LibCorrectSwapV1,
    WormholeFacet,
    SerdeFacet,
    LibSoFeeWormholeV1,
    BoolFacet,
    LibSoFeeBoolV1,
    web3,
    CelerFacet,
    LibSoFeeCelerV1,
    MultiChainFacet,
    LibSoFeeMultiChainV1,
    LibSoFeeCCTPV1,
    CCTPFacet
)
from brownie.network import priority_fee, max_fee

FacetCutAction_ADD = 0
FacetCutAction_REPLACE = 1
FacetCutAction_REMOVE = 2

from scripts.helpful_scripts import (
    get_bool_pools,
    get_bool_router,
    get_bool_chainid,
    get_account,
    get_method_signature_by_abi,
    get_native_oracle_address,
    get_oracles,
    get_wormhole_actual_reserve,
    get_wormhole_bridge,
    get_wormhole_chainid,
    get_wormhole_estimate_reserve,
    get_wormhole_info,
    zero_address,
    get_stargate_router,
    get_stargate_chain_id,
    get_token_address,
    get_swap_info,
    get_token_decimal,
    get_stargate_info,
    get_celer_chain_id,
    get_celer_oracles,
    get_celer_message_bus,
    get_celer_info,
    get_multichain_router,
    get_multichain_id,
    get_multichain_info,
    get_cctp_token_messenger,
    get_cctp_message_transmitter
)

if "arbitrum" in network.show_active():
    priority_fee("1 gwei")
    max_fee("1.25 gwei")


def main():
    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("1 gwei")

    account = get_account()
    so_diamond = SoDiamond[-1]
    print(f"SoDiamond Address:{so_diamond}")
    try:
        initialize_cut(account, so_diamond)
    except Exception as e:
        print(f"initialize_cut fail:{e}")
    # try:
    #     initialize_stargate(account, so_diamond)
    # except Exception as e:
    #     print(f"initialize_stargate fail:{e}")
    try:
        initialize_bool(account, so_diamond)
    except Exception as e:
        print(f"initialize_bool fail:{e}")
        initialize_cctp(account, so_diamond)
    except Exception as e:
        print(f"initialize_cctp fail:{e}")
    # try:
    #     initialize_stargate(account, so_diamond)
    # except Exception as e:
    #     print(f"initialize_stargate fail:{e}")
    # try:
    #     initialize_celer(account, so_diamond)
    # except Exception as e:
    #     print(f"initialize_celer fail:{e}")
    # try:
    #     initialize_celer_fee(account)
    # except Exception as e:
    #     print(f"initialize_celer_fee fail: {e}")
    # try:
    #     initialize_multichain(account, so_diamond)
    # except Exception as e:
    #     print(f"initialize_multichain fail:{e}")
    # try:
    #     initialize_wormhole(account, so_diamond)
    # except Exception as e:
    #     print(f"initialize_wormhole fail: {e}")
    # try:
    #     initialize_wormhole_fee(account)
    # except Exception as e:
    #     print(f"initialize_wormhole_fee fail: {e}")
    try:
        initialize_dex_manager(account, so_diamond)
    except Exception as e:
        print(f"initialize_dex_manager fail:{e}")
    # initialize_little_token_for_stargate()
    batch_set_bool_allowed_address(account, so_diamond)


def initialize_wormhole_fee(account):
    # initialize oracle
    oracles = get_oracles()
    native_oracle_address = get_native_oracle_address()
    chainid = get_wormhole_chainid()
    for token in oracles:
        if chainid == oracles[token]["chainid"]:
            continue
        print(f"initialize_wormhole fee oracle: {token}")
        if oracles[token]["currency"] == "USD":

            LibSoFeeWormholeV1[-1].setPriceConfig(
                oracles[token]["chainid"],
                [[oracles[token]["address"], False], [native_oracle_address, True]],
                60,
                {"from": account},
            )
        elif oracles[token]["currency"] == "ETH":
            LibSoFeeWormholeV1[-1].setPriceConfig(
                oracles[token]["chainid"],
                [[oracles[token]["address"], False]],
                60,
                {"from": account},
            )


def initialize_celer_fee(account):
    # initialize oracle
    chain_oracles = get_celer_oracles()
    if chain_oracles is None:
        return

    chainid = get_celer_chain_id()

    native_oracle_address = ""
    for chain in chain_oracles:
        if chainid == chain_oracles[chain]["chainid"]:
            native_oracle_address = chain_oracles[chain]["address"]

    for chain in chain_oracles:
        if chainid == chain_oracles[chain]["chainid"]:
            continue
        print(f"initialize_celer_fee destination chain: {chain}")
        print("pair:", chain_oracles[chain]["pair"])

        LibSoFeeCelerV1[-1].setPriceConfig(
            chain_oracles[chain]["chainid"],
            [[chain_oracles[chain]["address"], False], [native_oracle_address, True]],
            60,
            {"from": account},
        )

    # LibSoFeeCelerV1[-1].updatePriceRatio(5, {'from': account})

    # LibSoFeeCelerV1[-1].setPriceRatio(5, 10, {'from': account})


def initialize_cut(account, so_diamond):
    proxy_cut = Contract.from_abi(
        "DiamondCutFacet", so_diamond.address, DiamondCutFacet.abi
    )
    register_funcs = {}
    register_contract = [
        DiamondLoupeFacet,
        DexManagerFacet,
        OwnershipFacet,
        # CelerFacet,
        # MultiChainFacet,
        # StargateFacet,
        BoolFacet,
        CCTPFacet,
        # CelerFacet,
        # MultiChainFacet,
        # StargateFacet,
        # WormholeFacet,
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


def initialize_stargate(account, so_diamond):
    proxy_stargate = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi
    )
    net = network.show_active()
    print(f"network:{net}, init stargate...")
    proxy_stargate.initStargate(
        get_stargate_router(), get_stargate_chain_id(), {"from": account}
    )


def initialize_bool(account, so_diamond):
    proxy_bool = Contract.from_abi(
        "BoolFacet", so_diamond.address, BoolFacet.abi
    )
    net = network.show_active()
    print(f"network:{net}, init bool...")
    proxy_bool.initBoolSwap(get_bool_router(), get_bool_chainid(), {"from": account})


def batch_set_bool_allowed_address(account, so_diamond):
    networks = ['optimism-main', 'arbitrum-main']
    cur_net = network.show_active()
    bool_facet = Contract.from_abi(
        "BoolFacet", so_diamond.address, BoolFacet.abi
    )
    print("set bool allowed addresses...")

    pool_addresses = []
    allow = []
    for net in networks:
        if net == cur_net:
            continue
        pools = get_bool_pools()
        for pool in pools:
            pool_addresses.append(pools[pool]["pool_address"])
            allow.append(True)

    bool_facet.batchSetBoolAllowedAddresses(pool_addresses, allow, {"from": account})

def initialize_cctp(account, so_diamond):
    proxy_cctp = Contract.from_abi("CCTPFacet", so_diamond.address, CCTPFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init cctp...")
    proxy_cctp.initCCTP(
        get_cctp_token_messenger(), get_cctp_message_transmitter(), {"from": account}
    )

    dst_domain_info = {
        "mainnet": 0,
        "avax-main": 1,
        "arbitrum-main": 3,
        "goerli": 0,
        "avax-test": 1,
        "arbitrum-test": 3
    }
    if "main" in net:
        dst_domains = {k: v for k, v in dst_domain_info.items() if "main" in k}
    else:
        dst_domains = {k: v for k, v in dst_domain_info.items() if "main" not in k}
    dstBaseGas = 700000
    dstGasPerBytes = 68
    print(f"Set dst net:{list(dst_domains.keys())} base gas:{dstBaseGas} gas per bytes:{dstGasPerBytes}")
    proxy_cctp.setCCTPBaseGas(list(dst_domains.values()), dstBaseGas, {"from": account})
    proxy_cctp.setCCTPGasPerBytes(list(dst_domains.values()), dstGasPerBytes, {"from": account})


def initialize_celer(account, so_diamond):
    proxy_celer = Contract.from_abi("CelerFacet", so_diamond.address, CelerFacet.abi)
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


def set_celer_base_gas():
    account = get_account()
    so_diamond = SoDiamond[-1]
    base_gas = 700000
    dst_chains = [324]

    proxy_celer = Contract.from_abi("CelerFacet", so_diamond.address, CelerFacet.abi)

    net = network.show_active()
    print(f"network:{net}, set base gas: {base_gas}, {dst_chains}")

    proxy_celer.setBaseGas(dst_chains, base_gas, {"from": account})


def initialize_multichain(account, so_diamond):
    proxy_multichain = Contract.from_abi(
        "MultiChainFacet", so_diamond.address, MultiChainFacet.abi
    )
    net = network.show_active()

    print(f"network:{net}, init multichain...")
    proxy_multichain.initMultiChain(
        get_multichain_router(), get_multichain_id(), {"from": account}
    )

    print(f"network:{net}, init multichain: updateAddressMappings")

    bridge_tokens = get_multichain_info()["token"]

    for name, token_info in bridge_tokens.items():
        if "anytoken" not in token_info:
            continue
        print(token_info)
        proxy_multichain.updateAddressMappings(
            [token_info["anytoken"]], {"from": account}
        )

    is_valid = proxy_multichain.isValidMultiChainConfig()
    print("isValidMultiChainConfig:", is_valid)


def set_wormhole_gas():
    so_diamond = SoDiamond[-1]
    proxy_stargate = Contract.from_abi(
        "WormholeFacet", so_diamond.address, WormholeFacet.abi
    )
    proxy_stargate.setWormholeGas(22, 70000, 68, {"from": get_account()})


def initialize_wormhole(account, so_diamond):
    proxy_stargate = Contract.from_abi(
        "WormholeFacet", so_diamond.address, WormholeFacet.abi
    )
    net = network.show_active()
    print(f"network:{net}, init wormhole...")
    proxy_stargate.initWormhole(
        get_wormhole_bridge(), get_wormhole_chainid(), {"from": account}
    )

    ray = 1e27
    # setWormholeReserve
    print(f"network:{net}, set wormhole reserve...")
    proxy_stargate.setWormholeReserve(
        int(get_wormhole_actual_reserve() * ray),
        int(get_wormhole_estimate_reserve() * ray),
        {"from": account},
    )
    # setWormholeGas
    gas = get_wormhole_info()["gas"]
    for chain in gas:
        print(f"network:{net}, set dst chain {chain} wormhole gas...")
        proxy_stargate.setWormholeGas(
            gas[chain]["dst_chainid"],
            gas[chain]["base_gas"],
            gas[chain]["per_byte_gas"],
            {"from": account},
        )


def initialize_dex_manager(account, so_diamond):
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", so_diamond.address, DexManagerFacet.abi
    )
    net = network.show_active()
    print(f"network:{net}, init dex manager...")
    dexs = []
    sigs = []
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {"from": account})
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
    # proxy_dex.addFee(
    #     get_stargate_router(), LibSoFeeStargateV1[-1].address, {"from": account}
    # )
    proxy_dex.addFee(
        get_bool_router(), LibSoFeeBoolV1[-1].address, {"from": account}
    )
    # proxy_dex.addFee(
    #     get_wormhole_bridge(), LibSoFeeWormholeV1[-1].address, {"from": account}
    # )
    # proxy_dex.addFee(
    #     get_multichain_router(), LibSoFeeMultiChainV1[-1].address, {"from": account}
    # )
    # proxy_dex.addFee(
    #     get_celer_message_bus(), LibSoFeeCelerV1[-1].address, {"from": account}
    # )
    proxy_dex.addFee(
        get_cctp_token_messenger(), LibSoFeeCCTPV1[-1].address, {"from": account}
    )
    # proxy_dex.addFee(
    #     get_wormhole_bridge(), LibSoFeeWormholeV1[-1].address, {"from": account}
    # )
    # proxy_dex.addFee(
    #     get_multichain_router(), LibSoFeeMultiChainV1[-1].address, {"from": account}
    # )
    # proxy_dex.addFee(
    #     get_celer_message_bus(), LibSoFeeCelerV1[-1].address, {"from": account}
    # )


def initialize_little_token_for_stargate():
    # Transfer a little to SoDiamond as a handling fee
    if network.show_active() in [
        "rinkeby",
        "avax-test",
        "polygon-test",
        "ftm-test",
        "bsc-test",
        "arbitrum-test",
        "optimism-test",
    ]:
        for token_name in get_stargate_info()["poolid"].keys():
            initialize_erc20(token_name)

    if network.show_active() in ["rinkeby", "arbitrum-test", "optimism-test"]:
        initialize_eth()


def redeploy_serde():
    remove_facet(SerdeFacet)
    SerdeFacet.deploy({"from": get_account()})
    add_cut([SerdeFacet])


def redeploy_cctp():
    if "arbitrum-test" in network.show_active():
        priority_fee("1 gwei")
        max_fee("1.25 gwei")
    account = get_account()

    try:
        remove_facet(CCTPFacet)
    except:
        pass

    CCTPFacet.deploy({"from": account})
    add_cut([CCTPFacet])
    initialize_cctp(account, SoDiamond[-1])
    #
    # proxy_dex = Contract.from_abi(
    #     "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    # )
    #
    # so_fee = 1e-3
    # ray = 1e27
    #
    # print("deploy LibSoFeeCCTPV1.sol...")
    # LibSoFeeCCTPV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("AddFee ...")
    # proxy_dex.addFee(
    #     get_cctp_token_messenger(), LibSoFeeCCTPV1[-1].address, {"from": account}
    # )


def redeploy_wormhole():
    account = get_account()

    remove_facet(WormholeFacet)

    WormholeFacet.deploy({"from": account})
    add_cut([WormholeFacet])
    initialize_wormhole(account, SoDiamond[-1])

    # proxy_dex = Contract.from_abi(
    #     "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi)

    # so_fee = 1e-3
    # ray = 1e27
    # print("Deploy LibSoFeeWormholeV1...")
    # LibSoFeeWormholeV1.deploy(int(so_fee * ray), {'from': account})
    # print("AddFee ...")
    # proxy_dex.addFee(get_wormhole_bridge(),
    #                  LibSoFeeWormholeV1[-1].address, {'from': account})
    # initialize_wormhole_fee(account)


def set_relayer_fee():
    decimal = 1e27
    if network.show_active() == "avax-main":
        # bnb
        dst_wormhole_id = 2
        LibSoFeeWormholeV1[-1].setPriceRatio(
            dst_wormhole_id, int(300 / 15 * decimal), {"from": get_account()}
        )
        # aptos
        dst_wormhole_id = 22
        LibSoFeeWormholeV1[-1].setPriceRatio(
            dst_wormhole_id, int(8 / 15 * decimal), {"from": get_account()}
        )

    if network.show_active() == "mainnet":
        # aptos
        dst_wormhole_id = 22
        LibSoFeeWormholeV1[-1].setPriceRatio(
            dst_wormhole_id, int(8 / 1250 * decimal), {"from": get_account()}
        )

    if network.show_active() == "polygon-main":
        # aptos
        dst_wormhole_id = 22
        LibSoFeeWormholeV1[-1].setPriceRatio(
            dst_wormhole_id, int(8 / 0.7 * decimal), {"from": get_account()}
        )

    if network.show_active() == "bsc-main":
        # aptos
        dst_wormhole_id = 22
        LibSoFeeWormholeV1[-1].setPriceRatio(
            dst_wormhole_id, int(8 / 250 * decimal), {"from": get_account()}
        )


def remove_facet(facet):
    account = get_account()

    proxy_loupe = Contract.from_abi(
        "DiamondLoupeFacet", SoDiamond[-1].address, DiamondLoupeFacet.abi
    )

    funcs = proxy_loupe.facetFunctionSelectors(facet[-1].address)

    register_data = [[zero_address(), 2, list(funcs)]]

    proxy_cut = Contract.from_abi(
        "DiamondCutFacet", SoDiamond[-1].address, DiamondCutFacet.abi
    )

    proxy_cut.diamondCut(register_data, zero_address(), b"", {"from": account})


def redeploy_generic_swap():
    account = get_account()
    remove_facet(GenericSwapFacet)
    GenericSwapFacet.deploy({"from": account})
    add_cut([GenericSwapFacet])


# redeploy and initialize
def redeploy_stargate():
    account = get_account()

    # remove_facet(StargateFacet)

    StargateFacet.deploy({"from": account})
    add_cut([StargateFacet])
    initialize_stargate(account, SoDiamond[-1])


def redeploy_bool():
    account = get_account()

    # 1. deploy bool's lib so fee

    # so_fee = 1e-3
    # ray = 1e27
    # LibSoFeeBoolV1.deploy(int(so_fee * ray), {"from": account})

    # 2. add bool's lib so fee to diamond
    # proxy_dex = Contract.from_abi(
    #     "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    # )
    # proxy_dex.addFee(
    #     get_bool_router(), LibSoFeeBoolV1[-1].address, {"from": account}
    # )

    remove_facet(BoolFacet)

    # 3. deploy BoolFacet
    BoolFacet.deploy({'from': account})
    add_cut([BoolFacet])
    initialize_bool(account, SoDiamond[-1])
    batch_set_bool_allowed_address(account, SoDiamond[-1])


# redeploy and initialize
def redeploy_celer():
    account = get_account()

    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("2 gwei")

    # proxy_celer = Contract.from_abi("CelerFacet", SoDiamond[-1].address, CelerFacet.abi)
    # lastNonce = proxy_celer.getNonce()
    # print(f"last nonce: {lastNonce}")
    #
    # remove_facet(CelerFacet)

    CelerFacet.deploy({"from": account})
    add_cut([CelerFacet])

    initialize_celer(account, SoDiamond[-1])

    # proxy_celer = Contract.from_abi("CelerFacet", SoDiamond[-1].address, CelerFacet.abi)
    # proxy_celer.setNonce(lastNonce, {"from": account})

    # proxy_dex = Contract.from_abi(
    #     "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    # )
    #
    # so_fee = 1e-3
    # ray = 1e27
    #
    # print("Deploy LibSoFeeCelerV1...")
    # LibSoFeeCelerV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("AddFee ...")
    # proxy_dex.addFee(
    #     get_celer_message_bus(), LibSoFeeCelerV1[-1].address, {"from": account}
    # )
    #
    # print("Initialize celer fee...")
    # initialize_celer_fee(account)

    # LibSoFeeCelerV1[-1].setPriceRatio(43113, ray, {'from': account})
    # LibSoFeeCelerV1[-1].updatePriceRatio(43113, {'from': account})


# redeploy and initialize
def redeploy_multichain():
    account = get_account()

    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("2 gwei")

    # remove_facet(MultiChainFacet)
    MultiChainFacet.deploy({"from": account})
    add_cut([MultiChainFacet])

    initialize_multichain(account, SoDiamond[-1])

    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    )

    so_fee = 1e-3
    ray = 1e27

    print("Deploy LibSoFeeMultiChainV1...")
    LibSoFeeMultiChainV1.deploy(int(so_fee * ray), {"from": account})
    print("AddFee ...")
    proxy_dex.addFee(
        get_multichain_router(), LibSoFeeMultiChainV1[-1].address, {"from": account}
    )


def remove_dump(a: list, b: list):
    result = []
    for k in a:
        if str(k.hex()) not in b:
            result.append(k)
    return result


def add_cut(contracts: list = None):
    proxy_loupe = Contract.from_abi(
        "DiamondLoupeFacet", SoDiamond[-1].address, DiamondLoupeFacet.abi
    )
    all_facets = proxy_loupe.facets()
    func_sigs = [str(d2) for d1 in all_facets for d2 in d1[1]]

    if contracts is None:
        contracts = []
    account = get_account()
    register_data = []
    register_funcs = {}
    for contract in contracts:
        print(f"Initialize {contract._name}...")
        reg_facet = contract[-1]
        reg_funcs = get_method_signature_by_abi(contract.abi)
        for func_name in list(reg_funcs.keys()):
            if func_name in register_funcs:
                if reg_funcs[func_name] in register_funcs[func_name]:
                    print(f"function:{func_name} has been register!")
                    del reg_funcs[func_name]
                else:
                    register_funcs[func_name].append(reg_funcs[func_name])
            else:
                register_funcs[func_name] = [reg_funcs[func_name]]
        result = remove_dump(reg_funcs.values(), func_sigs)
        register_data.append([reg_facet, 0, result])

    if not register_data:
        return
    proxy_cut = Contract.from_abi(
        "DiamondCutFacet", SoDiamond[-1].address, DiamondCutFacet.abi
    )
    proxy_cut.diamondCut(register_data, zero_address(), b"", {"from": account})


def add_dex(dex_address):
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    )
    proxy_dex.addDex(
        dex_address, {"from": get_account()}
    )
    proxy_dex.batchSetFunctionApprovalBySignature(
        [v + "0" * 56 for v in list(interface.ISwapRouter.selectors.keys())],
        True,
        {"from": get_account()},
    )


def reinitialize_dex(old_dex):
    account = get_account()
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    )
    proxy_dex.removeDex(old_dex, {"from": account})
    dexs = []
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
    proxy_dex.batchAddDex(dexs, {"from": account})


def initialize_erc20(token_name: str):
    account = get_account()
    token_address = get_token_address(token_name)
    token_decimal = get_token_decimal(token_name)
    try:
        so_diamond = SoDiamond[-1]
        token = Contract.from_abi("MockToken", token_address, MockToken.abi)
    except Exception as e:
        print(f"get token {token_name} mint fail:{e}")
        return
    try:
        token.mint(account, 100 * 1e4 * token_decimal, {"from": account})
        print(f"mint 1000000 {token_name} success!\n")
    except Exception as e:
        print(f"{token_name} mint fail:{e}")
    token.transfer(so_diamond.address, int(0.01 * token_decimal), {"from": account})
    print(f"transfer 0.01 {token_name} success!")


def initialize_eth():
    account = get_account()
    decimal = 18
    stargate_router = get_stargate_router()
    stargate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    factory_address = stargate.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, interface.IStargateFactory.abi
    )
    pool_address = factory.getPool(13)
    pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
    token_address = pool.token()
    token = Contract.from_abi(
        "IStargateEthVault", token_address, interface.IStargateEthVault.abi
    )
    weth_amount = int(1e-5 * 1e18)
    proxy_diamond = Contract.from_abi(
        "StargateFacet", SoDiamond[-1].address, StargateFacet.abi
    )
    if token.noUnwrapTo(SoDiamond[-1].address):
        proxy_diamond.deposit(
            zero_address(), token, weth_amount, {"from": account, "value": weth_amount}
        )
        print(
            f"initialize_eth finish, "
            f"weth:{token} amount in sodiamond:{SoDiamond[-1].address} "
            f"is {token.balanceOf(SoDiamond[-1].address) / 10 ** decimal}."
        )
    else:
        account.transfer(SoDiamond[-1].address, weth_amount)
        print(
            f"initialize_eth finish, "
            f"eth amount in sodiamond:{SoDiamond[-1].address} "
            f"is {web3.eth.get_balance(SoDiamond[-1].address) / 10 ** decimal}."
        )


def reset_so_fee():
    account = get_account()
    so_fee = int(1e-3 * 1e18)
    LibSoFeeStargateV1[-1].setFee(so_fee, {"from": account})
    print("Cur soFee is", LibSoFeeStargateV1[-1].soFee() / 1e18)


def reset_so_gas():
    account = get_account()
    gas = 30000
    LibSoFeeStargateV1[-1].setTransferForGas(gas, {"from": account})
    print("Cur gas is", LibSoFeeStargateV1[-1].getTransferForGas())


def redeploy_correct_swap():
    account = get_account()
    LibCorrectSwapV1.deploy({"from": account})
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    )
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {"from": account})
