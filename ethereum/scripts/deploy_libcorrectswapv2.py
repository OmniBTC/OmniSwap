from brownie import (
    LibCorrectSwapV2,
    CorrectUniswapV2Factory,
    CorrectUniswapV3Factory,
    CorrectSyncswapFactory,
    CorrectMuteswapFactory,
    CorrectQuickswapV3Factory,
    CorrectAerodromeFactory,
    CorrectBalancerV2Factory,
    CorrectCurveFactory,
    CorrectWombatFactory,
    CorrectTraderJoeFactory,
    CorrectGMXV1Factory,
    CorrectPearlFiFactory,
    CorrectIZiSwapFactory,
    CorrectCamelotFactory,
    CorrectKyberswapFactory,
    CorrectOneInchFactory
)

from ethereum.scripts.helpful_scripts import get_account


def deploy_lib_correct_swap_v2(account):
    print("deploy LibCorrectSwapV2...")
    LibCorrectSwapV2.deploy({"from": account})


def deploy_correct_swaps(account):
    account = get_account()
    print("deploy CorrectUniswapV2Factory...")
    CorrectUniswapV2Factory.deploy({"from": account})
    print("deploy CorrectUniswapV3Factory...")
    CorrectUniswapV3Factory.deploy({"from": account})
    print("deploy CorrectSyncswapFactory...")
    CorrectSyncswapFactory.deploy({"from": account})
    print("deploy CorrectMuteswapFactory...")
    CorrectMuteswapFactory.deploy({"from": account})
    print("deploy CorrectQuickswapV3Factory...")
    CorrectQuickswapV3Factory.deploy({"from": account})
    print("deploy CorrectAerodromeFactory...")
    CorrectAerodromeFactory.deploy({"from": account})
    print("deploy CorrectBalancerV2Factory...")
    CorrectBalancerV2Factory.deploy({"from": account})
    print("deploy CorrectCurveFactory...")
    CorrectCurveFactory.deploy({"from": account})
    print("deploy CorrectWombatFactory...")
    CorrectWombatFactory.deploy({"from": account})
    print("deploy CorrectTraderJoeFactory...")
    CorrectTraderJoeFactory.deploy({"from": account})
    print("deploy CorrectGMXV1Factory...")
    CorrectGMXV1Factory.deploy({"from": account})
    print("deploy CorrectPearlFiFactory...")
    CorrectPearlFiFactory.deploy({"from": account})
    print("deploy CorrectIZiSwapFactory...")
    CorrectIZiSwapFactory.deploy({"from": account})
    print("deploy CorrectCamelotFactory...")
    CorrectCamelotFactory.deploy({"from": account})
    print("deploy CorrectKyberswapFactory...")
    CorrectKyberswapFactory.deploy({"from": account})
    print("deploy CorrectOneInchFactory...")
    CorrectOneInchFactory.deploy({"from": account})


def main():
    account = get_account()
    deploy_lib_correct_swap_v2(account)
    deploy_correct_swaps(account)
