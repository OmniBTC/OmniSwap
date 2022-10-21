from scripts.serde_aptos import get_serde_facet
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
        package["so_fee_wormhole::set_price_ratio"](4, 1)
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
    reserve_decimal = 1e8
    package["wormhole_facet::set_wormhole_reserve"](
        int(package.network_config["wormhole"]["actual_reserve"] * reserve_decimal),
        int(package.network_config["wormhole"]["estimate_reserve"] * reserve_decimal)
    )

    serde = get_serde_facet(package, "bsc-test")

    # set gas
    for net in package.network_config["wormhole"]["gas"]:
        if net == package.network:
            continue
        base_gas = hex_str_to_vector_u8(str(serde.normalizeU256(
            package.network_config["wormhole"]["gas"][net]["base_gas"])))
        gas_per_bytes = hex_str_to_vector_u8(str(serde.normalizeU256(
            package.network_config["wormhole"]["gas"][net]["per_byte_gas"])))
        print(f"Set wormhole gas for:{net}")
        package["wormhole_facet::set_wormhole_gas"](
            package.network_config["wormhole"]["chainid"],
            base_gas,
            gas_per_bytes
        )

    setup_mock(package.network)
