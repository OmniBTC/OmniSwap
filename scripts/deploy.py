from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet

from scripts.helpful_scripts import get_account


def main():
    account = get_account()
    deploy_contracts(account)


def deploy_contracts(account):
    print("deploy DiamondCutFacet.sol...")
    cut = DiamondCutFacet.deploy({'from': account})

    print("deploy SoDiamond.sol...")
    so_diamond = SoDiamond.deploy(account, cut, {'from': account})

    print("deploy DiamondLoupeFacet.sol...")
    loupe = DiamondLoupeFacet.deploy({'from': account})

    print("deploy DexManagerFacet.sol...")
    dex_manager = DexManagerFacet.deploy({'from': account})

    print("deploy StargateFacet.sol...")
    stargate = StargateFacet.deploy({'from': account})

    print("deploy WithdrawFacet.sol...")
    withdraw = WithdrawFacet.deploy({'from': account})

    print("deploy OwnershipFacet.sol...")
    ownership = OwnershipFacet.deploy({'from': account})

    print("deploy GenericSwapFacet.sol...")
    swap = GenericSwapFacet.deploy({'from': account})

    print("deploy end!")
