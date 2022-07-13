import time

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, config, interface, LibSoFeeV01, MockToken, LibCorrectSwapV1, \
    web3
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account, get_method_signature_by_abi, zero_address, combine_bytes, \
    padding_to_bytes


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
    if network.show_active() in ["rinkeby", "avax-test", "polygon-test", "ftm-test", "bsc-test", "arbitrum-test", "optimism-test"]:
        so_diamond = SoDiamond[-1]
        usdc = Contract.from_abi("MockToken", config["networks"][network.show_active()]["usdc"], MockToken.abi)
        try:
            usdc.mint(account, 100 * 1e4 * 1e6, {"from": account})
            print("mint 1000000 usdc success!\n")
        except Exception as e:
            print(f"usdc mint fail:{e}")
        usdc.transfer(so_diamond.address, int(0.01 * 1e6), {"from": account})
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
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {'from': account})
    for pair in config["networks"][net]["swap"]:
        dexs.append(pair[0])
        reg_funcs = get_method_signature_by_abi(getattr(interface, pair[1]).abi)
        for sig in reg_funcs.values():
            sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {'from': account})
    proxy_dex.batchSetFunctionApprovalBySignature(sigs, True, {'from': account})
    proxy_dex.addFee(config["networks"][net]["stargate_router"], LibSoFeeV01[-1].address, {'from': account})


def reinitialize_dex(old_dex):
    account = get_account()
    net = network.show_active()
    proxy_dex = Contract.from_abi("DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi)
    proxy_dex.removeDex(old_dex, {'from': account})
    dexs = []
    for pair in config["networks"][net]["swap"]:
        dexs.append(pair[0])
    proxy_dex.batchAddDex(dexs, {'from': account})


def initialize_main_for_dstforgas(token: str):
    if token == "usdt":
        decimal = 18
    elif token == "usdc":
        decimal = 6
    else:
        raise "TOKEN FAIL"
    account = get_account()
    net = network.show_active()
    token_address = config["networks"][net][token]
    weth = config["networks"][net]["weth"]
    swap_router = Contract.from_abi(
        "ROUTER",
        config["networks"][net]["swap"][0][0],
        getattr(interface, config["networks"][net]["swap"][0][1]).abi)
    amount = 0.01 * (10 ** decimal)
    swap_router.swapETHForExactTokens(
        amount,
        [weth, token_address],
        SoDiamond[-1].address,
        int(time.time() + 3000),
        {
            "from": account,
            "value": 0.01 * (10 ** 18)
        }
    )
    token_contract = Contract.from_abi("TOKEN", token_address, interface.IERC20.abi)
    print(f"initialize_main_for_dstforgas finish, "
          f"{token} amount in sodiamond is {token_contract.balanceOf(SoDiamond[-1].address) / 10 ** decimal}.")


def initialize_main_for_dstforgas_from_v3(token: str):
    if token == "usdt":
        decimal = 18
    elif token == "usdc":
        decimal = 6
    else:
        raise "TOKEN FAIL"
    account = get_account()
    net = network.show_active()
    token_address = config["networks"][net][token]
    weth = config["networks"][net]["weth"]
    swap_router = Contract.from_abi(
        "ROUTER",
        config["networks"][net]["swap"][0][0],
        getattr(interface, config["networks"][net]["swap"][0][1]).abi)
    amount = 0.01 * (10 ** decimal)
    path = combine_bytes([weth,
                          padding_to_bytes(web3.toHex(int(0.003 * 1e6)), padding="left", length=3),
                          token_address])
    swap_router.exactInput([
        path,
        SoDiamond[-1].address,
        int(time.time() + 3000),
        amount,
        0],
        {
            "from": account,
            "value": int(0.01 * (10 ** 18))
        }
    )
    token_contract = Contract.from_abi("TOKEN", token_address, interface.IERC20.abi)
    print(f"initialize_main_for_dstforgas_from_v3 finish, "
          f"{token} amount in sodiamond is {token_contract.balanceOf(SoDiamond[-1].address) / 10 ** decimal}.")


def reset_so_fee():
    account = get_account()
    so_fee_contract = Contract.from_abi("LibSoFeeV01", LibSoFeeV01[-1].address, LibSoFeeV01.abi)
    so_fee = int(1e-3 * 1e18)
    so_fee_contract.setFee(so_fee, {"from": account})
