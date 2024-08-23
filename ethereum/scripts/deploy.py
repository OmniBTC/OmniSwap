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
    BoolFacet,
    LibSoFeeBoolV1,
    network,
    CCTPFacet,
    LibSoFeeCCTPV1,
    StargateFacet,
    LibSoFeeStargateV2,
    WormholeFacet,
    CoreBridgeFacet,
    LibSoFeeWormholeV1,
    Multicall3,
    BulkTransfer,
    config,
    Contract,
)
from brownie.network import priority_fee, max_fee, gas_price, gas_limit

from scripts.helpful_scripts import get_account, get_stargate_router


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_multicall(account=get_account()):
    Multicall3.deploy({"from": account})


def deploy_bulk(account=get_account("deploy_key")):
    BulkTransfer.deploy({"from": account})


def deploy_contracts(account):
    print(f"account:{account.address}")
    if network.show_active() in ["rinkeby", "goerli"]:
        priority_fee("1 gwei")
    if "arbitrum-test" in network.show_active():
        priority_fee("1 gwei")
        max_fee("1.25 gwei")
    if "core" in network.show_active():
        # need to use the old fee calculation model
        priority_fee(None)
        max_fee(None)
        gas_price("30 gwei")
    deploy_facets = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        CoreBridgeFacet,
        # StargateFacet,
        # CCTPFacet,
        # CelerFacet,
        # MultiChainFacet,
        # WormholeFacet,
        # BoolFacet,
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

    # so_fee = 0
    # transfer_for_gas = 40000
    # basic_beneficiary = config["networks"][network.show_active()]["basic_beneficiary"]
    # basic_fee = int(0.0002 * 1e18)
    # if network.show_active() == "bsc-main":
    #     basic_fee *= 8
    # elif network.show_active() == "avax-main":
    #     basic_fee *= 183
    # elif network.show_active() == "polygon-main":
    #     basic_fee *= 3000
    # elif network.show_active() == "metis-main":
    #     basic_fee *= 25
    # elif network.show_active() == "mantle-main":
    #     basic_fee *= 4500
    # print(f"deploy LibSoFeeStargateV2.sol so_fee:{so_fee}, basic_fee:{basic_fee} "
    #       f"basic_beneficiary:{basic_beneficiary}...")
    # LibSoFeeStargateV2.deploy(int(so_fee * 1e18), transfer_for_gas,
    #                           basic_fee, basic_beneficiary,
    #                           {"from": account})

    # ray = 1e27

    # print("deploy LibSoFeeCelerV1.sol...")
    # LibSoFeeCelerV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("deploy LibSoFeeMultiChainV1.sol...")
    # LibSoFeeMultiChainV1.deploy(int(so_fee * ray), {"from": account})

    # print("deploy LibSoFeeWormholeV1.sol...")
    #
    # LibSoFeeWormholeV1.deploy(int(so_fee * ray), {"from": account})
    #
    # print("deploy LibSoFeeBoolV1.sol...")

    # LibSoFeeBoolV1.deploy(int(so_fee * ray), {"from": account})

    # print("deploy LibSoFeeCCTPV1.sol...")
    # LibSoFeeCCTPV1.deploy(int(so_fee * ray), {"from": account})

    # print("deploy LibCorrectSwapV1...")
    # LibCorrectSwapV1.deploy({"from": account})
    #
    print("deploy end!")
