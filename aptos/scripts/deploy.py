from scripts.serde import get_serde_facet
from scripts.struct import omniswap_aptos_path, hex_str_to_vector_u8
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
        # use dst chain id init
        package["so_fee_wormhole::initialize"](4)
    except:
        pass
    # # wormhole
    try:
        # Maybe has initialized
        package["wormhole_facet::init_wormhole"](
            package.network_config["wormhole"]["chainid"])
    except:
        pass

    # set reserve
    package["wormhole_facet::set_wormhole_reserve"](
        package.network_config["wormhole"]["actual_reserve"],
        package.network_config["wormhole"]["estimate_reserve"]
    )

    serde = get_serde_facet(package, "bsc-test")

    # set gas
    for net in package.config["networks"]:
        if net == package.network:
            continue
        if (("test" in net and "test" in package.network)
                or ("main" in net and "main" in package.network)):
            base_gas = hex_str_to_vector_u8(str(serde.normalizeU256(
                package.network_config["wormhole"]["base_gas"])))
            gas_per_bytes = hex_str_to_vector_u8(str(serde.normalizeU256(
                package.network_config["wormhole"]["gas_per_bytes"])))

            package["wormhole_facet::set_wormhole_gas"](
                package.network_config["wormhole"]["chainid"],
                base_gas,
                gas_per_bytes
            )

    setup_mock(package.network)
