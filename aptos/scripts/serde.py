from brownie import Contract

from scripts.struct import change_network, omniswap_ethereum_project
from scripts.utils import aptos_brownie


def get_serde_facet(
        package: aptos_brownie.AptosPackage,
        net: str):
    change_network(net)
    contract_name = "SerdeFacet"
    return Contract.from_abi(
        contract_name,
        package.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


def get_wormhole_facet(
        package: aptos_brownie.AptosPackage,
        net: str):
    change_network(net)
    contract_name = "WormholeFacet"
    return Contract.from_abi(
        contract_name,
        package.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


def get_token_bridge(
        package: aptos_brownie.AptosPackage,
        net: str):
    change_network(net)
    contract_name = "TokenBridge"
    return Contract.from_abi(
        contract_name,
        package.config["networks"][net]["wormhole"]["token_bridge"],
        omniswap_ethereum_project.interface.IWormholeBridge
    )


def get_wormhole(
        package: aptos_brownie.AptosPackage,
        net: str):
    change_network(net)
    contract_name = "Wormhole"
    return Contract.from_abi(
        contract_name,
        package.config["networks"][net]["wormhole"]["wormhole"],
        omniswap_ethereum_project.interface.IWormhole
    )
