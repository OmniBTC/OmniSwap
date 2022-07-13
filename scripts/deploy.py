from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, LibSoFeeV01, LibCorrectSwapV1, network
from brownie.network import priority_fee

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_contracts(account):
    if network.show_active() in ["rinkeby"]:
        priority_fee("2 gwei")
    deploy_facets = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet,
                     WithdrawFacet, OwnershipFacet, GenericSwapFacet
                     ]
    for facet in deploy_facets:
        print(f"deploy {facet._name}.sol...")
        facet.deploy({'from': account})

    print("deploy SoDiamond.sol...")
    SoDiamond.deploy(account, DiamondCutFacet[-1], {'from': account})

    print("deploy LibSoFeeV01.sol...")
    so_fee = 1e-3
    transfer_for_gas = 30000
    LibSoFeeV01.deploy(int(so_fee*1e18), transfer_for_gas, {'from': account})

    print("deploy LibCorrectUniswapV2...")
    LibCorrectSwapV1.deploy({'from': account})

    print("deploy end!")
