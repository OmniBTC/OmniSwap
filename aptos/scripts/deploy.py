from scripts.struct import omniswap_aptos_path
from scripts.utils import aptos_brownie


def setup_mock(net: str = "aptos-testnet"):
    if net not in ["aptos-testnet", "aptos-devnet"]:
        return
    package_mock = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=net,
        package_path=omniswap_aptos_path.joinpath("mocks")
    )
    package_mock.publish_package()
    try:
        # Maybe has initialized
        package_mock["setup::initialize"]()
    except:
        pass


def main():
    net = "aptos-testnet"
    # deploy
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=net
    )
    package.publish_package()

    # initialize
    # # fee
    try:
        # Maybe has initialized
        package["so_fee_wormhole_v1::initialize"]()
    except:
        pass
    # # wormhole
    try:
        # Maybe has initialized
        package["wormhole_facet::init_wormhole"](package.network_config["wormhole"]["chainid"])
    except:
        pass

    setup_mock(net)
