import time

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, Contract, network, interface, LibSoFeeV01, MockToken, LibCorrectSwapV1, \
    web3
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account, get_method_signature_by_abi, zero_address, combine_bytes, \
    padding_to_bytes, get_stargate_router, get_stargate_chain_id, get_token_address, get_swap_info, get_token_decimal


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
    initialize_for_test_fee()


def initialize_for_test_fee():
    account = get_account()
    # Transfer a little to SoDiamond as a handling fee
    if network.show_active() in ["rinkeby", "avax-test", "polygon-test", "ftm-test", "bsc-test", "arbitrum-test",
                                 "optimism-test"]:
        so_diamond = SoDiamond[-1]
        usdc = Contract.from_abi("MockToken", get_token_address("usdc"), MockToken.abi)
        try:
            usdc.mint(account, 100 * 1e4 * 1e6, {"from": account})
            print("mint 1000000 usdc success!\n")
        except Exception as e:
            print(f"usdc mint fail:{e}")
        usdc.transfer(so_diamond.address, int(0.01 * 1e6), {"from": account})
        print("transfer 0.01 usdc success!")
    if network.show_active() in ["rinkeby", "arbitrum-test", "optimism-test"]:
        initialize_eth_for_dstforgas()


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


def redeploy_stargate():
    account = get_account()

    LibCorrectSwapV1.deploy({'from': account})
    StargateFacet.deploy({"from": account})
    initialize_stargate(account, SoDiamond[-1])
    reinitialize_cut(StargateFacet)
    reset_so_gas()

    proxy_dex = Contract.from_abi("DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi)
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {'from': account})

    dexs = ["0xE592427A0AEce92De3Edee1F18E0157C05861564"]
    swapType = "ISwapRouter"
    sigs = []
    reg_funcs = get_method_signature_by_abi(getattr(interface, swapType).abi)
    for sig in reg_funcs.values():
        sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {'from': account})
    proxy_dex.batchSetFunctionApprovalBySignature(sigs, True, {'from': account})
    initialize_for_test_fee()


def redeploy_generic_swap():
    account = get_account()
    GenericSwapFacet.deploy({'from': account})
    reinitialize_cut(GenericSwapFacet)


def reinitialize_cut(contract):
    account = get_account()
    register_data = []
    register_funcs = {}
    print(f"Initalize {contract._name}...")
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
    data = [reg_funcs[func_name] for func_name in reg_funcs if func_name in ["withdraw", "deposit"]]
    if len(data):
        register_data.append([reg_facet, 0, data])
    data = [reg_funcs[func_name] for func_name in reg_funcs if func_name not in ["withdraw", "deposit"]]
    if len(data):
        register_data.append([reg_facet, 1, data])
    proxy_cut = Contract.from_abi("DiamondCutFacet", SoDiamond[-1].address, DiamondCutFacet.abi)
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
        get_stargate_router(),
        get_stargate_chain_id(),
        {'from': account}
    )


def initialize_dex_manager(account, so_diamond):
    proxy_dex = Contract.from_abi("DexManagerFacet", so_diamond.address, DexManagerFacet.abi)
    net = network.show_active()
    print(f"network:{net}, init dex manager...")
    dexs = []
    sigs = []
    proxy_dex.addCorrectSwap(LibCorrectSwapV1[-1].address, {'from': account})
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
        reg_funcs = get_method_signature_by_abi(getattr(interface, swap_type).abi)
        for sig in reg_funcs.values():
            sigs.append(sig.hex() + "0" * 56)
    proxy_dex.batchAddDex(dexs, {'from': account})
    proxy_dex.batchSetFunctionApprovalBySignature(sigs, True, {'from': account})
    proxy_dex.addFee(get_stargate_router(), LibSoFeeV01[-1].address, {'from': account})


def reinitialize_dex(old_dex):
    account = get_account()
    proxy_dex = Contract.from_abi("DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi)
    proxy_dex.removeDex(old_dex, {'from': account})
    dexs = []
    swap_info = get_swap_info()
    for swap_type in swap_info:
        cur_swap = swap_info[swap_type]
        dexs.append(cur_swap["router"])
    proxy_dex.batchAddDex(dexs, {'from': account})


def initialize_main_for_dstforgas(token: str):
    account = get_account()
    token_address = get_token_address(token)
    decimal = get_token_decimal(token)
    weth = get_token_address("weth")
    swap_router = Contract.from_abi(
        "ROUTER",
        get_swap_info()["IUniswapV2Router02"]["router"],
        getattr(interface, "IUniswapV2Router02").abi)
    amount = 0.01 * decimal
    weth_amount = int(amount * (10 ** 18) / decimal / 1000)
    swap_router.swapETHForExactTokens(
        amount,
        [weth, token_address],
        SoDiamond[-1].address,
        int(time.time() + 3000),
        {
            "from": account,
            "value": weth_amount
        }
    )
    token_contract = Contract.from_abi("TOKEN", token_address, interface.IERC20.abi)
    print(f"initialize_main_for_dstforgas finish, "
          f"{token} amount in sodiamond:{SoDiamond[-1].address} is "
          f"{token_contract.balanceOf(SoDiamond[-1].address) / decimal}.")


def initialize_main_for_dstforgas_from_v3(token: str):
    decimal = get_token_decimal(token)
    account = get_account()
    token_address = get_token_address(token)
    weth = get_token_address("weth")
    swap_router = Contract.from_abi(
        "ROUTER",
        get_swap_info()["ISwapRouter"]["router"],
        getattr(interface, "ISwapRouter").abi)
    amount = int(0.01 * decimal)
    weth_max_amount = int(amount * (10 ** 18) / decimal / 1000)
    path = combine_bytes([weth,
                          padding_to_bytes(web3.toHex(int(0.003 * 1e6)), padding="left", length=3),
                          token_address])
    swap_router.exactInput([
        path,
        SoDiamond[-1].address,
        int(time.time() + 3000),
        weth_max_amount,
        0],
        {
            "from": account,
            "value": weth_max_amount
        }
    )
    token_contract = Contract.from_abi("TOKEN", token_address, interface.IERC20.abi)
    print(f"initialize_main_for_dstforgas_from_v3 finish, "
          f"{token} amount in sodiamond:{SoDiamond[-1].address} is "
          f"{token_contract.balanceOf(SoDiamond[-1].address) / 10 ** decimal}.")


def initialize_eth_for_dstforgas():
    account = get_account()
    decimal = 18
    stargate_router = get_stargate_router()
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    factory_address = stragate.factory()
    factory = Contract.from_abi("IStargateFactory", factory_address, interface.IStargateFactory.abi)
    pool_address = factory.getPool(13)
    pool = Contract.from_abi("IStargatePool", pool_address, interface.IStargatePool.abi)
    token_address = pool.token()
    token = Contract.from_abi("IStargateEthVault", token_address, interface.IStargateEthVault.abi)
    weth_amount = int(1e-5 * 1e18)
    proxy_diamond = Contract.from_abi(
        "StargateFacet", SoDiamond[-1].address, StargateFacet.abi)
    if token.noUnwrapTo(SoDiamond[-1].address):
        proxy_diamond.deposit(zero_address(), token, weth_amount, {"from": account, "value": weth_amount})
        print(f"initialize_eth_for_dstforgas finish, "
              f"weth:{token} amount in sodiamond:{SoDiamond[-1].address} "
              f"is {token.balanceOf(SoDiamond[-1].address) / 10 ** decimal}.")
    else:
        account.transfer(SoDiamond[-1].address, weth_amount)
        print(f"initialize_eth_for_dstforgas finish, "
              f"eth amount in sodiamond:{SoDiamond[-1].address} "
              f"is {web3.eth.get_balance(SoDiamond[-1].address) / 10 ** decimal}.")


def reset_so_fee():
    account = get_account()
    so_fee = int(1e-3 * 1e18)
    LibSoFeeV01[-1].setFee(so_fee, {"from": account})
    print("Cur soFee is", LibSoFeeV01[-1].soFee() / 1e18)


def reset_so_gas():
    account = get_account()
    gas = int(30000)
    LibSoFeeV01[-1].setTransferForGas(gas, {"from": account})
    print("Cur gas is", LibSoFeeV01[-1].getTransferForGas())
