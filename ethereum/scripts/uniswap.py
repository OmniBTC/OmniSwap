# @Time    : 2022/6/15 19:57
# @Author  : WeiDai
# @FileName: uniswap.py
import contextlib
import time

from brownie import interface, Contract, MockToken
from brownie.network import priority_fee
from scripts.helpful_scripts import get_account, get_token_address, get_swap_info


# todo: batch add liquidity


def create_pair_and_add_liquidity():
    account = get_account()
    # usdc
    token1_address = get_token_address("wusdt")
    # weth
    token2_address = get_token_address("aave")

    token1_amount = int(100000 * 1e18)
    token2_amount = int(5000 * 1e18)

    router_address = get_swap_info()["IUniswapV2Router02AVAX"]["router"]
    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02AVAX.abi)
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi)
    with contextlib.suppress(Exception):
        factory.createPair(token1_address, token2_address, {"from": account})
    # approve
    usdc = Contract.from_abi("IERC20", token1_address, interface.IERC20.abi)
    usdc.approve(router_address, token1_amount, {"from": account})

    wbnb = Contract.from_abi("IERC20", token2_address, interface.IERC20.abi)
    wbnb.approve(router_address, token2_amount, {"from": account})
    router.addLiquidity(token1_address, token2_address, token1_amount, token2_amount, 0, 0, account, int(time.time() + 3000),
                        {"from": account})
