from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, config, interface, LibSoFeeV01, MockToken, LibCorrectUniswapV2
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account, get_method_signature_by_abi, zero_address


def main():
    if network.show_active() in ["rinkeby"]:
        priority_fee("2 gwei")
    account = get_account()
    so_diamond = SoDiamond[-1]
    print(f"SoDiamond:{so_diamond}")
    try:
        initialize_cut(account, so_diamond)
    except Exception as e:
        print(f"initialize_cut fail:{e}")
    try:
        initialize_stargate(account, so_diamond)
    except Exception as e:
        print(f"initialize_stargate fail:{e}")
    try:
        initialize_dex_manager(account, so_diamond)
    except Exception as e:
        print(f"initialize_dex_manager fail:{e}")
    # Transfer a little to SoDiamond as a handling fee
    if network.show_active() in ["rinkeby", "avax-test", "polygon-test", "ftm-test", "bsc-test", "arbitrum-test"]:
        so_diamond = SoDiamond[-1]
        usdc = Contract.from_abi("MockToken", config["networks"][network.show_active()]["usdc"], MockToken.abi)
        try:
            usdc.mint(account, 100*1e4*1e6, {"from": account})
            print("mint 1000000 usdc success!\n")
        except Exception as e:
            print(f"usdc mint fail:{e}")
        usdc.transfer(so_diamond.address, int(0.01*1e6), {"from": account})
        print("transfer 0.01 usdc success!")


def initialize_cut(account, so_diamond):
    proxy_cut = Contract.from_abi("DiamondCutFacet", so_diamond.address, DiamondCutFacet.abi)
    register_funcs = {}
    register_contract = [DiamondLoupeFacet, DexManagerFacet, OwnershipFacet,
                         StargateFacet, WithdrawFacet, GenericSwapFacet]
    register_data = []
    for reg in register_contract:
        print(f"Initalize {reg._name}...")
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
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init stargate...")
    proxy_stargate.initStargate(
        config["networks"][net]["stargate_router"],
        config["networks"][net]["stargate_chainid"],
        {'from': account}
    )


def initialize_dex_manager(account, so_diamond):
    proxy_dex = Contract.from_abi("DexManagerFacet", so_diamond.address, DexManagerFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init dex manager...")
    dexs = []
    sigs = []
    for pair in config["networks"][net]["swap"]:
        dexs.append(pair[0])
        proxy_dex.addCorrectSwap(
            pair[0], LibCorrectUniswapV2[-1].address, {'from': account})
        reg_funcs = get_method_signature_by_abi(getattr(interface, pair[1]).abi)
        for sig in reg_funcs.values():
            sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {'from': account})
    proxy_dex.batchSetFunctionApprovalBySignature(sigs, True, {'from': account})
    proxy_dex.addFee(config["networks"][net]["stargate_router"], LibSoFeeV01[-1].address, {'from': account})
    
