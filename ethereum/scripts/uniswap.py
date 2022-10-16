# @Time    : 2022/6/15 19:57
# @Author  : WeiDai
# @FileName: uniswap.py
import contextlib
import os
import time

from brownie import interface, Contract, network, ERC20
from brownie.network import priority_fee
from scripts.helpful_scripts import get_account, get_token_address, get_swap_info, read_json
from scripts.wormhole import get_stable_coin_address

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
omni_swap_file = os.path.join(root_path, "export/OmniSwapInfo.json")


def batch_add_liquidity():
    current_net = network.show_active()
    if current_net in ["goerli"]:
        priority_fee("1 gwei")
    omni_swap_infos = read_json(omni_swap_file)
    (_, stable_coin_address) = get_stable_coin_address(current_net)

    support_tokens = omni_swap_infos[current_net]["WormholeSupportToken"]
    for token in support_tokens:
        if token["TokenName"] in ["USDT", "USDC"] and token["NativeToken"] == False:
            for chain_path in token["ChainPath"]:
                wrapped_token_address = chain_path["SrcTokenAddress"]
                create_pair_and_add_liquidity(
                    stable_coin_address, wrapped_token_address)


def create_pair_and_add_liquidity(token1_address, token2_address):
    account = get_account()
    # # usdc
    # token1_address = get_token_address("test")
    # # weth
    # token2_address = get_token_address("aave")

    router_address = get_swap_info()["IUniswapV2Router02"]["router"]
    router = Contract.from_abi(
        "Router", router_address, interface.IUniswapV2Router02.abi)
    factory_address = router.factory()
    factory = Contract.from_abi(
        "Factory", factory_address, interface.IUniswapV2Factory.abi)
    with contextlib.suppress(Exception):
        factory.createPair(token1_address, token2_address, {"from": account})
    # approve
    token1 = Contract.from_abi("ERC20", token1_address, ERC20.abi)
    token1_amount = int(10000 * 10 ** token1.decimals())
    token1.approve(router_address, token1_amount, {"from": account})

    token2 = Contract.from_abi("ERC20", token2_address, ERC20.abi)
    token2_amount = int(10000 * 10 ** token2.decimals())
    token2.approve(router_address, token2_amount, {"from": account})
    router.addLiquidity(token1_address, token2_address, token1_amount, token2_amount, 0, 0, account, int(time.time() + 3000),
                        {"from": account})
