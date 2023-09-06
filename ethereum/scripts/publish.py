# @Time    : 2022/7/22 14:41
# @Author  : WeiDai
# @FileName: publish.py
import os

from brownie import project, network

from helpful_scripts import change_network

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def main(net: str = None):
    if net is None:
        if network.is_connected():
            net = network.show_active()
        else:
            net = "mainnet"

    p = project.load(root_path, name=net)
    p.load_config()
    change_network(net)
    deployed_contract = [
        "CCTPFacet",
        # "LibCorrectSwapV1",
        # "GenericSwapFacet",
        # "SerdeFacet",
        # "SoDiamond",
        # "DiamondCutFacet",
        # "DiamondLoupeFacet",
        # "DexManagerFacet",
        # "WithdrawFacet",
        # "OwnershipFacet",
    ]
    for c in deployed_contract:
        print(f"network:{net} publish source: {c}")
        try:
            p[c].publish_source(p[c][-1])
        except Exception as e:
            print("error:", e)


if __name__ == "__main__":
    main("optimism-main")
