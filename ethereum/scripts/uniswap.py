# @Time    : 2022/6/15 19:57
# @Author  : WeiDai
# @FileName: uniswap.py
import time

from brownie import interface, Contract

from scripts.helpful_scripts import get_account, get_token_address, get_swap_info


def create_pair_and_add_liquidity():
    account = get_account()

    # usdc
    token1_address = "0x4A0D1092E9df255cf95D72834Ea9255132782318"
    # usdt
    token2_address = "0x8337e5eF98af25012e1B39CD996772143f6c5fDf"

    token1_amount = int(100000 * 1e6)
    token2_amount = int(100000 * 1e18)

    router_address = get_swap_info()["IUniswapV2Router02AVAX"]["router"]
    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02.abi)
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi)
    try:
        factory.createPair(token1_address, token2_address, {"from": account})
    except:
        pass
    # approve
    usdc = Contract.from_abi("IERC20", token1_address, interface.IERC20.abi)
    usdc.approve(router_address, token1_amount, {"from": account})

    usdt = Contract.from_abi("IERC20", token2_address, interface.IERC20.abi)
    usdt.approve(router_address, token2_amount, {"from": account})

    router.addLiquidity(token1_address, token2_address, token1_amount, token2_amount, 0, 0, account, int(time.time() + 3000),
                        {"from": account})
