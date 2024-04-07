# @Time    : 2022/7/22 14:41
# @Author  : WeiDai
# @FileName: publish.py
import functools
import os

from brownie import project, network
from sui_brownie.parallelism import ProcessExecutor

from helpful_scripts import change_network

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def worker(net: str = None):
    if net is None:
        if network.is_connected():
            net = network.show_active()
        else:
            net = "mainnet"

    p = project.load(root_path, name=net)
    p.load_config()
    change_network(net)
    deployed_contract = [
        "DiamondCutFacet",
        "SoDiamond",
        "DiamondLoupeFacet",
        "DexManagerFacet",
        "WithdrawFacet",
        "OwnershipFacet",
        "GenericSwapFacet",
        "LibCorrectSwapV1",
        "SerdeFacet",
        "ConnextFacet",
        "LibSoFeeConnextV1",
    ]
    for c in deployed_contract:
        print(f"network:{net} publish source: {c}")
        try:
            p[c].publish_source(p[c][-1])
        except Exception as e:
            print("error:", e)


def main():
    nets = ["avax-main", "base-main", "optimism-main", "arbitrum-main", "bsc-main", "mainnet", "polygon-main"]
    pt = ProcessExecutor(executor=len(nets))
    pt.run([functools.partial(worker, net) for net in nets])


if __name__ == "__main__":
    main("bsc-main")
