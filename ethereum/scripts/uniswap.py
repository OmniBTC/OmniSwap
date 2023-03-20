# @Time    : 2022/6/15 19:57
# @Author  : WeiDai
# @FileName: uniswap.py
import contextlib
import os
import time

from brownie import interface, Contract, network, ERC20
from brownie.network import priority_fee
from scripts.helpful_scripts import (
    get_account,
    get_token_address,
    get_swap_info,
    read_json,
)
from scripts.wormhole import get_stable_coin_address

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omni_swap_file = os.path.join(root_path, "export/OmniSwapInfo.json")


def batch_add_liquidity():
    current_net = network.show_active()
    if current_net in ["goerli"]:
        priority_fee("2 gwei")
    omni_swap_infos = read_json(omni_swap_file)
    (_, stable_coin_address) = get_stable_coin_address(current_net)

    support_tokens = omni_swap_infos[current_net]["WormholeSupportToken"]
    for token in support_tokens:
        if token["TokenName"] in ["USDT", "USDC"] and token["NativeToken"] == False:
            for chain_path in token["ChainPath"]:
                wrapped_token_address = chain_path["SrcTokenAddress"]
                create_pair_and_add_liquidity(
                    stable_coin_address, wrapped_token_address
                )


def create_pair_and_add_liquidity(token1_address, token2_address):
    account = get_account()
    # # usdc
    # token1_address = get_token_address("test")
    # # weth
    # token2_address = get_token_address("aave")

    router_address = get_swap_info()["IUniswapV2Router02"]["router"]
    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02.abi
    )
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi
    )
    with contextlib.suppress(Exception):
        factory.createPair(token1_address, token2_address, {"from": account})
    # approve
    token1 = Contract.from_abi("ERC20", token1_address, ERC20.abi)
    token1_amount = int(10000 * 10 ** token1.decimals())
    token1.approve(router_address, token1_amount, {"from": account})

    token2 = Contract.from_abi("ERC20", token2_address, ERC20.abi)
    token2_amount = int(10000 * 10 ** token2.decimals())
    token2.approve(router_address, token2_amount, {"from": account})
    router.addLiquidity(
        token1_address,
        token2_address,
        token1_amount,
        token2_amount,
        0,
        0,
        account,
        int(time.time() + 3000),
        {"from": account},
    )


def create_pair_and_add_liquidity_for_celer():
    if network.show_active() not in ["goerli"]:
        print("Only support avax-test")
        return

    account = get_account()
    token1_address = "0xCbE56b00d173A26a5978cE90Db2E33622fD95A28"  # celer-usdc
    token2_address = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"  # weth

    router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02.abi
    )
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi
    )
    with contextlib.suppress(Exception):
        factory.createPair(token1_address, token2_address, {"from": account})
    # approve
    token1 = Contract.from_abi("ERC20", token1_address, ERC20.abi)
    token1_amount = int(100 * 10 ** token1.decimals())
    token1.approve(router_address, token1_amount, {"from": account})

    token2 = Contract.from_abi("ERC20", token2_address, ERC20.abi)
    token2_amount = int(0.1 * 10 ** token2.decimals())
    token2.approve(router_address, token2_amount, {"from": account})

    router.addLiquidity(
        token1_address,
        token2_address,
        token1_amount,
        token2_amount,
        0,
        0,
        account,
        int(time.time() + 3000),
        {"from": account},
    )


def create_pair_and_add_liquidity_for_multichain():
    if network.show_active() not in ["bsc-test"]:
        print("Only support bsc-test")
        return

    account = get_account()

    token1_address = "0x75A2df47F2c30cc90B27f3c83C86e42B01466410"  # Y1
    token2_address = "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd"  # wbnb
    router_address = "0xD99D1c33F9fC3444f8101754aBC46c52416550D1"

    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02.abi
    )
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi
    )
    with contextlib.suppress(Exception):
        factory.createPair(token1_address, token2_address, {"from": account})
    # approve
    token1 = Contract.from_abi("ERC20", token1_address, ERC20.abi)
    token1_amount = int(1000 * 10 ** token1.decimals())
    token1.approve(router_address, token1_amount, {"from": account})

    token2 = Contract.from_abi("ERC20", token2_address, ERC20.abi)
    token2_amount = int(0.01 * 10 ** token2.decimals())
    token2.approve(router_address, token2_amount, {"from": account})

    router.addLiquidityETH(
        token1_address,
        token1_amount,
        0,
        0,
        account,
        int(time.time() + 3000),
        {"from": account, "value": token2_amount},
    )
