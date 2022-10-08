from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, interface, LibSoFeeStargateV1, MockToken, LibCorrectSwapV1, \
    WormholeFacet, LibSoFeeWormholeV1, web3
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account, get_method_signature_by_abi, get_native_oracle_address, get_oracles, get_wormhole_actual_reserve, get_wormhole_bridge, \
    get_wormhole_chainid, get_wormhole_estimate_reserve, get_wormhole_info, \
    zero_address, get_stargate_router, get_stargate_chain_id, get_token_address, get_swap_info, get_token_decimal, \
    get_stargate_info


def main():
    if network.show_active() in ["rinkeby"]:
        priority_fee("2 gwei")
    account = get_account()
    so_diamond = SoDiamond[-1]
    print(f"SoDiamond Address:{so_diamond}")
    try:
        initialize_cut(account, so_diamond)
    except Exception as e:
        print(f"initialize_cut fail:{e}")
    try:
        initialize_stargate(account, so_diamond)
    except Exception as e:
        print(f"initialize_stargate fail:{e}")
    try:
        initialize_wormhole(account, so_diamond)
    except Exception as e:
        print(f"initialize_wormhole fail: {e}")
    try:
        initialize_wormhole_fee(account)
    except Exception as e:
        print(f"initialize_wormhole_fee fail: {e}")
    try:
        initialize_dex_manager(account, so_diamond)
    except Exception as e:
        print(f"initialize_dex_manager fail:{e}")
    initialize_little_token_for_stargate()


def initialize_wormhole_fee(account):
    # initialize oracle
    oracles = get_oracles()
    native_oracle_address = get_native_oracle_address()
    chainid = get_wormhole_chainid()
    for token in oracles:
        if chainid == oracles[token]["chainid"]:
            continue
        print(f'initialize_wormhole fee oracle: {token}')
        LibSoFeeWormholeV1[-1].setPriceConfig(oracles[token]["chainid"], [
            [oracles[token]["address"], False],
            [native_oracle_address, True]
        ], 0, {'from': account})


def initialize_cut(account, so_diamond):
    proxy_cut = Contract.from_abi(
        "DiamondCutFacet", so_diamond.address, DiamondCutFacet.abi)
    register_funcs = {}
    register_contract = [DiamondLoupeFacet, DexManagerFacet, OwnershipFacet,
                         StargateFacet, WormholeFacet, WithdrawFacet, GenericSwapFacet]
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
        register_data.append([reg_facet, 0, list(reg_funcs.values())])
    proxy_cut.diamondCut(register_data,
                         zero_address(),
                         b'',
                         {'from': account}
                         )


def initialize_stargate(account, so_diamond):
    proxy_stargate = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init stargate...")
    proxy_stargate.initStargate(
        get_stargate_router(),
        get_stargate_chain_id(),
        {'from': account}
    )


def initialize_wormhole(account, so_diamond):
    proxy_stargate = Contract.from_abi(
        "WormholeFacet", so_diamond.address, WormholeFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init wormhole...")
    proxy_stargate.initWormhole(
        get_wormhole_bridge(),
        get_wormhole_chainid(),
        {'from': account}
    )

    ray = 1e27
    # setWormholeReserve
    print(f"network:{net}, set wormhole reserve...")
    proxy_stargate.setWormholeReserve(
        int(get_wormhole_actual_reserve() * ray),
        int(get_wormhole_estimate_reserve() * ray),
        {'from': account}
    )
    # setWormholeGas
    gas = get_wormhole_info()["gas"]
    for chain in gas:
        print(f"network:{net}, set dst chain {chain} wormhole gas...")
        proxy_stargate.setWormholeGas(
            gas[chain]["dst_chainid"],
            gas[chain]["base_gas"],
            gas[chain]["per_byte_gas"],
            {'from': account}
        )


def initialize_dex_manager(account, so_diamond):
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", so_diamond.address, DexManagerFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init dex manager...")
    dexs = []
    sigs = []
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {'from': account})
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
        reg_funcs = get_method_signature_by_abi(
            getattr(interface, swap_type).abi)
        for sig in reg_funcs.values():
            sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {'from': account})
    proxy_dex.batchSetFunctionApprovalBySignature(
        sigs, True, {'from': account})
    proxy_dex.addFee(get_stargate_router(),
                     LibSoFeeStargateV1[-1].address, {'from': account})


def initialize_little_token_for_stargate():
    # Transfer a little to SoDiamond as a handling fee
    if network.show_active() in ["rinkeby", "avax-test", "polygon-test", "ftm-test", "bsc-test", "arbitrum-test",
                                 "optimism-test"]:
        for token_name in get_stargate_info()["poolid"].keys():
            initialize_erc20(token_name)

    if network.show_active() in ["rinkeby", "arbitrum-test", "optimism-test"]:
        initialize_eth()


# redeploy and initialize
def redeploy_stargate():
    account = get_account()

    StargateFacet.deploy({"from": account}, publish_source=True)
    initialize_stargate(account, SoDiamond[-1])
    reinitialize_cut(StargateFacet)


def redeploy_generic_swap():
    account = get_account()
    GenericSwapFacet.deploy({'from': account})
    reinitialize_cut(GenericSwapFacet)


def reinitialize_cut(contract):
    account = get_account()
    register_data = []
    register_funcs = {}
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
    data = [reg_funcs[func_name]
            for func_name in reg_funcs if func_name in ["getSgReceiveForGasPayload"]]
    if len(data):
        register_data.append([reg_facet, 0, data])
    data = [reg_funcs[func_name]
            for func_name in reg_funcs if func_name not in ["getSgReceiveForGasPayload"]]
    if len(data):
        register_data.append([reg_facet, 1, data])
    proxy_cut = Contract.from_abi(
        "DiamondCutFacet", SoDiamond[-1].address, DiamondCutFacet.abi)
    proxy_cut.diamondCut(register_data,
                         zero_address(),
                         b'',
                         {'from': account}
                         )


def reinitialize_dex(old_dex):
    account = get_account()
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi)
    proxy_dex.removeDex(old_dex, {'from': account})
    dexs = []
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
    proxy_dex.batchAddDex(dexs, {'from': account})


def initialize_erc20(token_name: str):
    account = get_account()
    token_address = get_token_address(token_name)
    token_decimal = get_token_decimal(token_name)
    try:
        so_diamond = SoDiamond[-1]
        token = Contract.from_abi(
            "MockToken", token_address, MockToken.abi)
    except Exception as e:
        print(f"get token {token_name} mint fail:{e}")
        return
    try:
        token.mint(account, 100 * 1e4 * token_decimal, {"from": account})
        print(f"mint 1000000 {token_name} success!\n")
    except Exception as e:
        print(f"{token_name} mint fail:{e}")
    token.transfer(so_diamond.address, int(
        0.01 * token_decimal), {"from": account})
    print(f"transfer 0.01 {token_name} success!")


def initialize_eth():
    account = get_account()
    decimal = 18
    stargate_router = get_stargate_router()
    stargate = Contract.from_abi(
        "IStargate", stargate_router, interface.IStargate.abi)
    factory_address = stargate.factory()
    factory = Contract.from_abi(
        "IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pool_address = factory.getPool(13)
    pool = Contract.from_abi(
        "IStargatePool", pool_address, interface.IStargatePool.abi)
    token_address = pool.token()
    token = Contract.from_abi(
        "IStargateEthVault", token_address, interface.IStargateEthVault.abi)
    weth_amount = int(1e-5 * 1e18)
    proxy_diamond = Contract.from_abi(
        "StargateFacet", SoDiamond[-1].address, StargateFacet.abi)
    if token.noUnwrapTo(SoDiamond[-1].address):
        proxy_diamond.deposit(zero_address(), token, weth_amount, {
            "from": account, "value": weth_amount})
        print(f"initialize_eth finish, "
              f"weth:{token} amount in sodiamond:{SoDiamond[-1].address} "
              f"is {token.balanceOf(SoDiamond[-1].address) / 10 ** decimal}.")
    else:
        account.transfer(SoDiamond[-1].address, weth_amount)
        print(f"initialize_eth finish, "
              f"eth amount in sodiamond:{SoDiamond[-1].address} "
              f"is {web3.eth.get_balance(SoDiamond[-1].address) / 10 ** decimal}.")


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
