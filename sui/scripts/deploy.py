import functools
from pathlib import Path

import yaml
from sui_brownie import SuiPackage, sui_brownie, SuiObject

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


def setup_wormhole(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    wormhole_package = sui_brownie.SuiPackage(
        package_path=Path.home().joinpath(Path(
            ".move/https___github_com_OmniBTC_wormhole_git_f88f836e5fdb80ee8804b061d749620480ae2615/sui/wormhole")),
    )

    wormhole_package.program_publish_package(gas_budget=500000000)


@functools.lru_cache()
def load_wormhole(is_from_config):
    if is_from_config:
        return SuiPackage(
            sui_project.network_config['packages']['Wormhole'],
            package_name="Wormhole",
        )
    else:
        return SuiPackage(
            sui_project.Wormhole[-1],
            package_name="Wormhole",
        )


def init_wormhole(net: str = "sui-testnet"):
    """
    public entry fun complete(
        deployer: DeployerCap,
        upgrade_cap: UpgradeCap,
        governance_chain: u16,
        governance_contract: vector<u8>,
        initial_guardians: vector<vector<u8>>,
        guardian_set_epochs_to_live: u32,
        message_fee: u64,
        ctx: &mut TxContext
    )
    :return:
    """
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    wormhole = load_wormhole(is_from_config=False)
    upgrade_cap = get_upgrade_cap_by_package_id(wormhole.package_id)

    wormhole.setup.complete(
        wormhole.setup.DeployerCap[-1],
        upgrade_cap,
        0,
        list(bytes.fromhex("deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")),
        [
            list(bytes.fromhex("1337133713371337133713371337133713371337")),
            list(bytes.fromhex("c0dec0dec0dec0dec0dec0dec0dec0dec0dec0de")),
            list(bytes.fromhex("ba5edba5edba5edba5edba5edba5edba5edba5ed"))
        ],
        0,
        0
    )


def setup_token_bridge(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    token_bridge_package = sui_brownie.SuiPackage(
        package_path=Path.home().joinpath(Path(
            ".move/https___github_com_OmniBTC_wormhole_git_f88f836e5fdb80ee8804b061d749620480ae2615/sui/token_bridge")),
    )

    token_bridge_package.program_publish_package(gas_budget=500000000,
                                                 replace_address=dict(token_bridge="0x0", wormhole=None))


@functools.lru_cache()
def load_token_bridge(is_from_config):
    if is_from_config:
        return SuiPackage(
            sui_project.network_config['packages']['TokenBridge'],
            package_name="TokenBridge",
        )
    else:
        return SuiPackage(
            sui_project.TokenBridge[-1],
            package_name="TokenBridge",
        )


def init_token_bridge(net: str = "sui-testnet"):
    """
    public entry fun complete(
        worm_state: &WormholeState,
        deployer: DeployerCap,
        upgrade_cap: UpgradeCap,
        ctx: &mut TxContext
    )
    Returns:

    """
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    token_bridge = load_token_bridge(is_from_config=False)
    wormhole = load_wormhole(is_from_config=False)

    token_bridge.setup.complete(
        wormhole.state.State[-1],
        token_bridge.setup.DeployerCap[-1],
        get_upgrade_cap_by_package_id(token_bridge.package_id)
    )


def treasury_cap(coin_type):
    return f"0x2::coin::TreasuryCap<{coin_type}>"


def coin_metadata(coin_type):
    return f"0x2::coin::CoinMetadata<{coin_type}>"


def usdt(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["USDT"]
    else:
        return f"{sui_project.TestCoins[-1]}::usdt::USDT"


def usdc(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["USDC"]
    else:
        return f"{sui_project.TestCoins[-1]}::usdc::USDC"


def btc(is_from_config):
    if is_from_config:
        return sui_project.network_config["tokens"]["btc::BTC"]
    else:
        return f"{sui_project.TestCoins[-1]}::btc::BTC"


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

    wormhole = SuiPackage(
        package_id=sui_project.Wormhole[-1],
        package_name="Wormhole",
    )
    token_bridge = SuiPackage(
        package_id=sui_project.TokenBridge[-1],
        package_name="TokenBridge",
    )
    test_coins = SuiPackage(
        package_id=sui_project.TestCoins[-1],
        package_name="TestCoins",
    )
    omniswap = SuiPackage(
        package_id=sui_project.OmniSwap[-1],
        package_name="OmniSwap",
    )
    objects = {
        "WormholeState": wormhole.state.State[-1],
        "TokenBridgeState": token_bridge.state.State[-1],
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
            "address": "0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
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
        }
    }

    if "tokens" not in config["networks"]["sui-testnet"]:
        config["networks"]["sui-testnet"]["tokens"] = {}

    for token in tokens:
        config["networks"]["sui-testnet"]["tokens"][token] = tokens[token]

    # write config to config file
    with open(path, "w") as f:
        yaml.safe_dump(config, f)


def load_omniswap():
    if "packages" in sui_project.network_config and 'OmniSwap' in sui_project.network_config['packages']:
        package_id = sui_project.network_config['packages']['OmniSwap']
    else:
        package_id = sui_project.OmniSwap[-1]
    return SuiPackage(
        package_id,
        package_name="OmniSwap",
    )


def load_wormhole_state(is_from_config):
    if is_from_config:
        return sui_project.network_config["objects"]["WormholeState"]
    else:
        token_bridge = load_token_bridge(is_from_config)
        return token_bridge.state.State[-1]


def load_token_bridge_state(is_from_config):
    if is_from_config:
        return sui_project.network_config["objects"]["WormholeState"]
    else:
        wormhole = load_wormhole(is_from_config)
        return wormhole.state.State[-1]


def attest_token(coin_type, is_from_config):
    token_bridge = load_token_bridge(is_from_config)

    result = sui_project.pay_sui([0])
    zero_coin = result['objectChanges'][-1]['objectId']
    metadata = sui_project[SuiObject.from_type(coin_metadata(coin_type))][-1]
    token_bridge.token_bridge.attest_token(
        load_token_bridge_state(is_from_config),
        load_wormhole_state(is_from_config),
        zero_coin,
        metadata,
        0,
        clock(),
        type_arguments=[coin_type]
    )


# for testnet
def register_wormhole_token(is_from_config):
    attest_token(usdt(is_from_config), is_from_config)
    attest_token(usdc(is_from_config), is_from_config)
    attest_token(btc(is_from_config), is_from_config)


def main():
    net = "sui-testnet"
    print(f"Current sui network:{net}")

    # for testnet
    # setup_wormhole(net)
    # init_wormhole()
    # setup_token_bridge(net)
    # init_token_bridge()
    # register_wormhole_token(is_from_config=False)

    wormhole = load_wormhole(is_from_config=True)
    token_bridge = load_token_bridge(is_from_config=True)
    wormhole_state = load_wormhole_state(is_from_config=True)

    # deploy
    omniswap_package = SuiPackage(package_path=omniswap_sui_path)
    omniswap_package.publish_package(gas_budget=5000000000, replace_address=dict(
        wormhole=wormhole.package_id,
        token_bridge=token_bridge.package_id,
    ))

    facet_manager = omniswap_package.wormhole_facet.WormholeFacetManager[-1]

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
