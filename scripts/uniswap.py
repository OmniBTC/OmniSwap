# @Time    : 2022/6/15 19:57
# @Author  : WeiDai
# @FileName: uniswap.py
import time

from brownie import network, interface, Contract

from scripts.helpful_scripts import get_account, get_token_address, get_swap_info


def create_pair_and_add_liquidity():
    account = get_account()

    # usdc
    token1_address = "0x742DfA5Aa70a8212857966D491D67B09Ce7D6ec7"
    # weth
    token2_address = get_token_address("weth")
    token1_amount = int(30000 * 1e6)
    token2_amount = int(0.4 * 1e18)

    router_address = get_swap_info()["IUniswapV2Router02"]["router"]
    router = Contract.from_abi("Router", router_address, interface.IUniswapV2Router02.abi)
    factory_address = router.factory()
    factory = Contract.from_abi("Factory", factory_address, interface.IUniswapV2Factory.abi)
    try:
        factory.createPair(token1_address, token2_address, {"from": account})
    except:
        pass
    # approve
    usdc = Contract.from_abi("IERC20", token1_address, interface.IERC20.abi)
    usdc.approve(router_address, token1_amount, {"from": account})
    router.addLiquidityETH(token1_address, token1_amount, 0, 0, account, int(time.time() + 3000),
                           {"from": account, "value": token2_amount})
