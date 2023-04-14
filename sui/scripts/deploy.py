from sui_brownie import SuiProject, SuiPackage

from scripts.struct import omniswap_sui_path


def setup_test_coins(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    test_coins = SuiPackage(
        package_path=omniswap_sui_path.joinpath("test_coins")
    )
    test_coins.publish_package()
    print(f"Faucet:{test_coins.faucet.Faucet[-1]}")


def load_test_coins(package_id):
    return SuiPackage(
        package_id=package_id,
        package_name="TestCoins",
    )


def main():
    net = "sui-mainnet"
    print(f"Current aptos network:{net}")
    # deploy
    sui_project = SuiProject(omniswap_sui_path, network=net)
    sui_package = SuiPackage(package_path=omniswap_sui_path)
    sui_package.publish_package()

    wormhole_state = sui_project.network_config
    wormhole_fee = sui_package.wormhole_facet.WormholeFee[-1]
    facet_manager = sui_package.wormhole_facet.WormholeFacetManager[-1]
    storage = sui_package.wormhole_facet.Storage[-1]
    price_manager = sui_package.so_fee_wormhole.PriceManager[-1]

    print(f"WormholeFee:{wormhole_fee}\n"
          f"WormholeFee:{facet_manager}\n"
          f"WormholeFee:{storage}\n"
          f"WormholeFee:{price_manager}\n")

    sui_package.wormhole_facet.init_wormhole(
        facet_manager,
        wormhole_state,
        sui_project.network_config["wormhole"]["chainid"]
    )

    # set so fee
    so_fee_decimal = 1e8
    sui_package.wormhole_facet.set_so_fees(int(1e-3 * so_fee_decimal))

    # set reserve
    reserve_decimal = 1e8
    sui_package.wormhole_facet.set_wormhole_reserve(
        facet_manager,
        storage,
        int(sui_project.network_config["wormhole"]["actual_reserve"] * reserve_decimal),
        int(sui_project.network_config["wormhole"]["estimate_reserve"] * reserve_decimal)
    )

    # set gas
    for net in sui_project.network_config["wormhole"]["gas"]:
        if net == sui_package.network:
            continue
        base_gas = int(sui_project.network_config["wormhole"]["gas"][net]["base_gas"])
        gas_per_bytes = int(sui_project.network_config["wormhole"]["gas"][net]["per_byte_gas"])
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        sui_package.wormhole_facet.set_wormhole_gas(
            storage,
            facet_manager,
            sui_project.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes
        )

    setup_test_coins(net)
