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
    CorrectOneInchFactory,
    CorrectOpenOceanFactory,
)

from scripts.helpful_scripts import get_account


def deploy_correct_swaps(account):
    print("deploy LibCorrectSwapV2...")
    lib = LibCorrectSwapV2.deploy({"from": account})

    print("deploy CorrectUniswapV2Factory...")
    CorrectUniswapV2Factory.deploy(lib.address, {"from": account})

    print("deploy CorrectUniswapV3Factory...")
    CorrectUniswapV3Factory.deploy(lib.address, {"from": account})

    print("deploy CorrectSyncswapFactory...")
    CorrectSyncswapFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectMuteswapFactory...")
    CorrectMuteswapFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectQuickswapV3Factory...")
    CorrectQuickswapV3Factory.deploy(lib.address, {"from": account})

    print("deploy CorrectAerodromeFactory...")
    CorrectAerodromeFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectBalancerV2Factory...")
    CorrectBalancerV2Factory.deploy(lib.address, {"from": account})

    print("deploy CorrectCurveFactory...")
    CorrectCurveFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectWombatFactory...")
    CorrectWombatFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectTraderJoeFactory...")
    CorrectTraderJoeFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectGMXV1Factory...")
    CorrectGMXV1Factory.deploy(lib.address, {"from": account})

    print("deploy CorrectPearlFiFactory...")
    CorrectPearlFiFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectIZiSwapFactory...")
    CorrectIZiSwapFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectCamelotFactory...")
    CorrectCamelotFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectKyberswapFactory...")
    CorrectKyberswapFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectOneInchFactory...")
    CorrectOneInchFactory.deploy(lib.address, {"from": account})

    print("deploy CorrectOpenOceanFactory...")
    CorrectOpenOceanFactory.deploy(lib.address, {"from": account})


def main():
    account = get_account()
    deploy_correct_swaps(account)
