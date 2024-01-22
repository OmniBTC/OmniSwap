from scripts.serde_aptos import get_serde_facet
from scripts.serde_struct import omniswap_aptos_path, hex_str_to_vector_u8
import aptos_brownie


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
    net = "aptos-mainnet"
    print(f"Current aptos network:{net}")
    # deploy
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=net
    )
    package.publish_package()

    # set relayer
    relayer = "0x3b52fa49ef6577001619c56ba56c5c51d493fba0671dc15a7f41a99103e0e299"
    package["wormhole_facet::set_relayer"](relayer)

    # initialize
    # # fee
    try:
        # Maybe has initialized
        # use dst chain id init
        # ETH
        ratio_decimal = 1e8
        package["so_fee_wormhole::initialize"](2)
        package["so_fee_wormhole::set_price_ratio"](2, int(1400 / 7 * ratio_decimal))
        package["so_fee_wormhole::initialize"](4)
        package["so_fee_wormhole::set_price_ratio"](4, int(300 / 7 * ratio_decimal))
        package["so_fee_wormhole::initialize"](5)
        package["so_fee_wormhole::set_price_ratio"](5, int(1 / 7 * ratio_decimal))
        package["so_fee_wormhole::initialize"](6)
        package["so_fee_wormhole::set_price_ratio"](6, int(20 / 7 * ratio_decimal))
        package["so_fee_wormhole::initialize"](21)
        package["so_fee_wormhole::set_price_ratio"](21, int(0.1 / 7 * ratio_decimal))
    except:
        pass
    # # wormhole
    try:
        # Maybe has initialized
        package["wormhole_facet::init_wormhole"](
            package.network_config["wormhole"]["chainid"])

        package["wormhole_facet::init_so_transfer_event"]()
    except:
        pass

    # set so fee
    so_fee_decimal = 1e8
    package["wormhole_facet::set_so_fees"](int(1e-3 * so_fee_decimal))

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
            package.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes
        )

    # setup_mock(package.network)


if __name__ == "__main__":
    main()
