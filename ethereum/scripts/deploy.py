from brownie import (
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    LibCorrectSwapV1,
    SerdeFacet,
    network,
    CCTPFacet,
    LibSoFeeCCTPV1,
)
from brownie.network import priority_fee, max_fee

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_contracts(account):
    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("1 gwei")
    if "arbitrum-test" in network.show_active():
        priority_fee("1 gwei")
        max_fee("1.25 gwei")
    deploy_facets = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        CCTPFacet,
        # StargateFacet,
        # CelerFacet,
        # MultiChainFacet,
        # WormholeFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        SerdeFacet,
    ]
    for facet in deploy_facets:
        print(f"deploy {facet._name}.sol...")
        facet.deploy({"from": account})

    print("deploy SoDiamond.sol...")
    SoDiamond.deploy(account, DiamondCutFacet[-1], {"from": account})

    so_fee = 1e-3

    # print("deploy LibSoFeeStargateV1.sol...")
    # transfer_for_gas = 30000
    # LibSoFeeStargateV1.deploy(int(so_fee * 1e18), transfer_for_gas, {"from": account})

    ray = 1e27

    # print("deploy LibSoFeeCelerV1.sol...")
    # LibSoFeeCelerV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("deploy LibSoFeeMultiChainV1.sol...")
    # LibSoFeeMultiChainV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("deploy LibSoFeeWormholeV1.sol...")
    #
    # LibSoFeeWormholeV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibSoFeeCCTPV1.sol...")
    LibSoFeeCCTPV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibCorrectSwapV1...")
    LibCorrectSwapV1.deploy({"from": account})

    print("deploy end!")
