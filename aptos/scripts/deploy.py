from scripts.utils import aptos_brownie


def main():
    # deploy
    package = aptos_brownie.AptosPackage(
        project_path=".",
        network="aptos-testnet"
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
