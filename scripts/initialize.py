from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, config

from scripts.helpful_scripts import get_account, get_method_signature_by_abi


def main():
    account = get_account()
    so_diamond = SoDiamond[-1]
    print(f"SoDiamond:{so_diamond}")
    initialize_cut(account, so_diamond)
    initialize_stargate(account, so_diamond)


def initialize_cut(account, so_diamond):
    proxy_cut = Contract.from_abi("DiamondCutFacet", so_diamond.address, DiamondCutFacet.abi)
    zero_addr = "0x0000000000000000000000000000000000000000"
    register_funcs = {}
    register_contract = [DiamondLoupeFacet, DexManagerFacet, OwnershipFacet,
                         GenericSwapFacet, StargateFacet, WithdrawFacet]
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
        proxy_cut.diamondCut([[reg_facet, 0, list(reg_funcs.values())]],
                             zero_addr,
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
