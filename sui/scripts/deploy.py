import functools
from pathlib import Path

import yaml
from sui_brownie import SuiPackage, SuiObject, Argument, U16

from scripts import sui_project
from scripts.struct_sui import omniswap_sui_path


def get_upgrade_cap_info(upgrade_cap_ids: tuple):
    result = sui_project.client.sui_multiGetObjects(
        upgrade_cap_ids,
        {
            "showType": True,
            "showOwner": True,
            "showPreviousTransaction": False,
            "showDisplay": False,
            "showContent": True,
            "showBcs": False,
            "showStorageRebate": False
        }
    )
    return {v["data"]["content"]["fields"]["package"]: v["data"] for v in result if "error" not in v}


def get_upgrade_cap_by_package_id(package_id: str):
    upgrade_cap_ids = tuple(list(sui_project["0x2::package::UpgradeCap"]))
    info = get_upgrade_cap_info(upgrade_cap_ids)
    if package_id in info:
        return info[package_id]["objectId"]


# for testnet and devnet
def setup_test_coins(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    test_coins = SuiPackage(
        package_path=omniswap_sui_path.joinpath("test_coins")
    )
    test_coins.publish_package()

    faucet = test_coins.faucet.Faucet[-1]
    test_coins.faucet.add_supply(
        faucet,
        sui_project[SuiObject.from_type(treasury_cap(usdt(is_from_config=False)))][-1],
        type_arguments=[usdt(is_from_config=False)]
    )
    test_coins.faucet.add_supply(
        faucet,
        sui_project[SuiObject.from_type(treasury_cap(usdc(is_from_config=False)))][-1],
        type_arguments=[usdc(is_from_config=False)]
    )
    test_coins.faucet.add_supply(
        faucet,
        sui_project[SuiObject.from_type(treasury_cap(btc(is_from_config=False)))][-1],
        type_arguments=[btc(is_from_config=False)]
    )


def load_test_coins(is_from_config):
    if is_from_config:
        return SuiPackage(
            package_id=sui_project.network_config["packages"]["TestCoins"],
            package_name="TestCoins",
        )
    else:
        return SuiPackage(
            package_id=sui_project.TestCoins[-1],
            package_name="TestCoins",
        )


@functools.lru_cache()
def load_integer_mate():
    return SuiPackage(
        sui_project.network_config['packages']['IntegerMate']["latest"],
        package_name="IntegerMate",
    )


@functools.lru_cache()
def load_move_stl():
    return SuiPackage(
        sui_project.network_config['packages']['MoveSTL']["latest"],
        package_name="MoveSTL",
    )


@functools.lru_cache()
def load_cetus_clmm():
    return SuiPackage(
        sui_project.network_config['packages']['CetusClmm']["latest"],
        package_name="CetusClmm",
    )


@functools.lru_cache()
def load_wormhole():
    return SuiPackage(
        sui_project.network_config['packages']['Wormhole']['latest'],
        package_name="Wormhole",
    )


@functools.lru_cache()
def load_token_bridge():
    return SuiPackage(
        sui_project.network_config['packages']['TokenBridge']['latest'],
        package_name="TokenBridge",
    )


def treasury_cap(coin_type):
    return f"0x2::coin::TreasuryCap<{coin_type}>"


def coin_metadata(coin_type):
    return f"0x2::coin::CoinMetadata<{coin_type}>"


def usdt(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["USDT"]['address']
    else:
        return f"{sui_project.TestCoins[-1]}::usdt::USDT"


def usdc(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["USDC"]['address']
    else:
        return f"{sui_project.TestCoins[-1]}::usdc::USDC"


def btc(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["BTC"]['address']
    else:
        return f"{sui_project.TestCoins[-1]}::btc::BTC"


def cetus_btc():
    return sui_project.network_config["tokens"]["Cetus-BTC"]['address']


def cetus_eth():
    return sui_project.network_config["tokens"]["Cetus-ETH"]['address']


def cetus_usdc():
    return sui_project.network_config["tokens"]["Cetus-USDC"]['address']


def cetus_usdt():
    return sui_project.network_config["tokens"]["Cetus-USDT"]['address']


def clock():
    return "0x0000000000000000000000000000000000000000000000000000000000000006"


def export_testnet():
    # load brownie config file
    path = Path(__file__).parent.parent.joinpath("brownie-config.yaml")
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    packages = {
        "OmniSwap": sui_project.OmniSwap[-1],
        "Wormhole": sui_project.Wormhole[-1],
        "TokenBridge": sui_project.TokenBridge[-1],
        "TestCoins": sui_project.TestCoins[-1],
        "DeepBook": "0x000000000000000000000000000000000000000000000000000000000000dee9"
    }

    if "packages" not in config["networks"]["sui-testnet"]:
        config["networks"]["sui-testnet"]["packages"] = {}

    for package_name in packages:
        config["networks"]["sui-testnet"]["packages"][package_name] = packages[package_name]

    test_coins = SuiPackage(
        package_id=sui_project.TestCoins[-1],
        package_name="TestCoins",
    )
    omniswap = SuiPackage(
        package_id=sui_project.OmniSwap[-1],
        package_name="OmniSwap",
    )
    objects = {
        "WormholeState": load_wormhole_state(),
        "TokenBridgeState": load_token_bridge_state(),
        "Clock": "0x0000000000000000000000000000000000000000000000000000000000000006",
        "FacetStorage": omniswap.wormhole_facet.Storage[-1],
        "PriceManager": omniswap.so_fee_wormhole.PriceManager[-1],
        "WormholeFee": omniswap.wormhole_facet.WormholeFee[-1],
        "FacetManager": omniswap.wormhole_facet.WormholeFacetManager[-1],
        # for testnet
        "Faucet": test_coins.faucet.Faucet[-1],
        "UpgradeCap": get_upgrade_cap_by_package_id(omniswap.package_id)
    }

    if "objects" not in config["networks"]["sui-testnet"]:
        config["networks"]["sui-testnet"]["objects"] = {}

    for obj in objects:
        config["networks"]["sui-testnet"]["objects"][obj] = objects[obj]

    tokens = {
        "SUI": {
            "name": "SUI",
            "address": "0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
            "decimal": 9
        },
        "USDT": {
            "name": "USDT",
            "address": usdt(is_from_config=False),
            "decimal": 6
        },
        "USDC": {
            "name": "USDC",
            "address": usdc(is_from_config=False),
            "decimal": 6
        },
        "BTC": {
            "name": "BTC",
            "address": btc(is_from_config=False),
            "decimal": 8
        },
        "Cetus-BTC": {
            "name": "Cetus-BTC",
            "address": cetus_btc(),
            "decimal": 8
        },
        "Cetus-ETH": {
            "name": "Cetus-ETH",
            "address": cetus_eth(),
            "decimal": 8
        },
        "Cetus-USDC": {
            "name": "Cetus-USDC",
            "address": cetus_usdc(),
            "decimal": 6
        },
        "Cetus-USDT": {
            "name": "Cetus-USDT",
            "address": cetus_usdt(),
            "decimal": 6
        }
    }

    if "tokens" not in config["networks"]["sui-testnet"]:
        config["networks"]["sui-testnet"]["tokens"] = {}

    for token in tokens:
        config["networks"]["sui-testnet"]["tokens"][token] = tokens[token]

    # write config to config file
    with open(path, "w") as f:
        yaml.safe_dump(config, f)


def load_omniswap(is_from_config):
    if is_from_config:
        return SuiPackage(
            package_id=sui_project.network_config['packages']['OmniSwap'],
            package_name="OmniSwap",
        )
    else:
        return SuiPackage(
            package_id=sui_project.OmniSwap[-1],
            package_name="OmniSwap",
        )


def load_wormhole_state():
    return sui_project.network_config["objects"]["WormholeState"]


def load_test_coin_faucet(is_from_config):
    if is_from_config:
        return sui_project.network_config["objects"]["Faucet"]
    else:
        test_coins = load_test_coins(is_from_config=True)
        return test_coins.faucet.Faucet[-1]


def load_token_bridge_state():
    return sui_project.network_config["objects"]["TokenBridgeState"]


def get_coin_metadata(coin_type):
    return sui_project.client.suix_getCoinMetadata(coin_type)['id']


def attest_token(coin_type):
    token_bridge = load_token_bridge()
    wormhole = load_wormhole()

    result = sui_project.pay_sui([0])
    zero_coin = result['objectChanges'][-1]['objectId']
    metadata = get_coin_metadata(coin_type)

    sui_project.batch_transaction(
        actual_params=[
            load_token_bridge_state(),
            metadata,
            0,
            load_wormhole_state(),
            zero_coin,
            clock()
        ],
        transactions=[
            [
                token_bridge.attest_token.attest_token,
                [
                    Argument("Input", U16(0)),
                    Argument("Input", U16(1)),
                    Argument("Input", U16(2)),
                ],
                [coin_type]
            ],
            [
                wormhole.publish_message.publish_message,
                [
                    Argument("Input", U16(3)),
                    Argument("Input", U16(4)),
                    Argument("Result", U16(0)),
                    Argument("Input", U16(5)),
                ],
                []
            ]
        ]
    )


# for testnet
def register_wormhole_token(is_from_config):
    attest_token(usdt(is_from_config))
    attest_token(usdc(is_from_config))
    attest_token(btc(is_from_config))


def main():
    net = sui_project.network
    print(f"Current sui network:{net}")

    # for testnet
    # register_wormhole_token(is_from_config=False)

    wormhole = load_wormhole()
    token_bridge = load_token_bridge()
    wormhole_state = load_wormhole_state()
    cetus_clmm = load_cetus_clmm()
    move_stl = load_move_stl()
    integer_mate = load_integer_mate()

    # deploy
    omniswap_package = SuiPackage(package_path=omniswap_sui_path)
    omniswap_package.publish_package(
        gas_budget=500000000,
        skip_dependency_verification=True,
        replace_address=dict(
            wormhole=sui_project.network_config['packages']['Wormhole']['origin'],
            token_bridge=sui_project.network_config['packages']['TokenBridge']['origin'],
            cetus_clmm=cetus_clmm.package_id,
            move_stl=move_stl.package_id,
            integer_mate=integer_mate.package_id,
        ),
        replace_publish_at=dict(
            wormhole=wormhole.package_id,
            token_bridge=token_bridge.package_id,
        )
    )

    facet_manager = omniswap_package.wormhole_facet.WormholeFacetManager[-1]

    omniswap_package.wormhole_facet.set_relayer(facet_manager, sui_project.network_config["Relayer"])

    print(f"FacetManager:{facet_manager}\n")

    omniswap_package.wormhole_facet.init_wormhole(
        facet_manager,
        wormhole_state,
        sui_project.network_config["wormhole"]["chainid"],
        gas_budget=1000000000
    )

    wormhole_fee = omniswap_package.wormhole_facet.WormholeFee[-1]
    storage = omniswap_package.wormhole_facet.Storage[-1]
    price_manager = omniswap_package.so_fee_wormhole.PriceManager[-1]

    print(f"FacetStorage:{storage}\n"
          f"PriceManager:{price_manager}\n"
          f"WormholeFee:{wormhole_fee}")

    # set so fee
    so_fee_decimal = 1e8
    omniswap_package.wormhole_facet.set_so_fees(wormhole_fee, int(1e-3 * so_fee_decimal),
                                                gas_budget=1000000000)

    # set reserve
    reserve_decimal = 1e8
    omniswap_package.wormhole_facet.set_wormhole_reserve(
        facet_manager,
        storage,
        int(sui_project.network_config["wormhole"]["actual_reserve"] * reserve_decimal),
        int(sui_project.network_config["wormhole"]["estimate_reserve"] * reserve_decimal),
        gas_budget=1000000000
    )

    # set gas
    for net in sui_project.network_config["wormhole"]["gas"]:
        if net == sui_project.network:
            continue
        base_gas = int(sui_project.network_config["wormhole"]["gas"][net]["base_gas"])
        gas_per_bytes = int(sui_project.network_config["wormhole"]["gas"][net]["per_byte_gas"])
        print(f"Set wormhole gas for:{net}, bas_gas:{base_gas}, gas_per_bytes:{gas_per_bytes}")
        omniswap_package.wormhole_facet.set_wormhole_gas(
            storage,
            facet_manager,
            sui_project.network_config["wormhole"]["gas"][net]["dst_chainid"],
            base_gas,
            gas_per_bytes,
            gas_budget=1000000000
        )


if __name__ == "__main__":
    main()
    # export_testnet()
