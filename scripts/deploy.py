from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_contracts(account):
    deploy_facets = [DiamondCutFacet, DiamondLoupeFacet, DexManagerFacet, StargateFacet,
                     WithdrawFacet, OwnershipFacet, GenericSwapFacet
                     ]
    for facet in deploy_facets:
        print(f"deploy {facet._name}.sol...")
        facet.deploy({'from': account})

    print("deploy SoDiamond.sol...")
    SoDiamond.deploy(account, DiamondCutFacet[-1], {'from': account})

    print("deploy end!")
