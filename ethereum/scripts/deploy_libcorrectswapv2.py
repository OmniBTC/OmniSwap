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
    Contract,
    SoDiamond,
    DexManagerFacet,
    CorrectLynexFactory
)

from scripts.helpful_scripts import get_account


def deploy_correct_swaps(account=get_account()):
    print("deploy LibCorrectSwapV2...")
    _lib = LibCorrectSwapV2.deploy({"from": account})

    factorys = [
        CorrectUniswapV2Factory,
        CorrectUniswapV3Factory,
        # CorrectLynexFactory
        # CorrectSyncswapFactory,
        # CorrectMuteswapFactory,
        # CorrectQuickswapV3Factory,
        # CorrectAerodromeFactory,
        # CorrectBalancerV2Factory,
        # CorrectCurveFactory,
        # CorrectWombatFactory,
        # CorrectTraderJoeFactory,
        # CorrectGMXV1Factory,
        # CorrectPearlFiFactory,
        # CorrectIZiSwapFactory,
        # CorrectCamelotFactory,
        # CorrectKyberswapFactory,
        # CorrectOneInchFactory,
        # CorrectOpenOceanFactory,
    ]

    for k, factory in enumerate(factorys):
        print(f"deploy {k}/{len(factorys)} {factory._name}.sol...")
        factory.deploy(LibCorrectSwapV2[-1].address, {"from": account})

    print("addCorrectSwap...")
    proxy_dex = Contract.from_abi(
        "DexManagerFacet", SoDiamond[-1].address, DexManagerFacet.abi
    )
    proxy_dex.addCorrectSwap(LibCorrectSwapV2[-1].address, {"from": account})


def main():
    deploy_correct_swaps()
