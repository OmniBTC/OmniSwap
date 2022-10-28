from scripts.struct import omniswap_aptos_path
from scripts.utils import aptos_brownie


def main(net="aptos-testnet"):
    aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=net
    )
