from brownie import (
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    StargateFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    LibSoFeeStargateV1,
    LibSoFeeWormholeV1,
    LibCorrectSwapV1,
    WormholeFacet,
    SerdeFacet,
    network,
    LibSoFeeCelerV1,
    CelerFacet,
    MultiChainFacet,
    LibSoFeeMultiChainV1,
)
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_contracts(account):
    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("1 gwei")
    deploy_facets = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        StargateFacet,
        CelerFacet,
        MultiChainFacet,
        WormholeFacet,
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

    print("deploy LibSoFeeStargateV1.sol...")
    transfer_for_gas = 30000
    LibSoFeeStargateV1.deploy(int(so_fee * 1e18), transfer_for_gas, {"from": account})

    ray = 1e27

    print("deploy LibSoFeeCelerV1.sol...")
    LibSoFeeCelerV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibSoFeeMultiChainV1.sol...")
    LibSoFeeMultiChainV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibSoFeeWormholeV1.sol...")

    LibSoFeeWormholeV1.deploy(int(so_fee * ray), {"from": account})

    print("deploy LibCorrectSwapV1...")
    LibCorrectSwapV1.deploy({"from": account})

    print("deploy end!")
