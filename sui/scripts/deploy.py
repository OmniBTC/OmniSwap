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
        sui_project[SuiObject.from_type(treasury_cap(usdt()))][-1],
        type_arguments=[usdt()]
    )
    test_coins.faucet.add_supply(
        faucet,
        sui_project[SuiObject.from_type(treasury_cap(usdc()))][-1],
        type_arguments=[usdc()]
    )
    test_coins.faucet.add_supply(
        faucet,
        sui_project[SuiObject.from_type(treasury_cap(btc()))][-1],
        type_arguments=[btc()]
    )


def load_test_coins():
    return SuiPackage(
        package_id=sui_project.TestCoins[-1],
        package_name="TestCoins",
    )


# for testnet and devnet
def setup_omniswap_mock(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    omniswap_mock = SuiPackage(
        package_path=omniswap_sui_path.joinpath("mocks")
    )
    omniswap_mock.publish_package(replace_address=dict(omniswap_mock="0x0", test_coins=None))


def load_omniswap_mock():
    return SuiPackage(
        package_id=sui_project.OmniSwapMock[-1],
        package_name="OmniSwapMock",
    )


def setup_wormhole(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    wormhole_package = sui_brownie.SuiPackage(
        package_path=Path.home().joinpath(Path(
            ".move/https___github_com_OmniBTC_wormhole_git_f88f836e5fdb80ee8804b061d749620480ae2615/sui/wormhole")),
    )

    wormhole_package.program_publish_package(gas_budget=500000000)


def load_wormhole():
    if "packages" in sui_project.network_config and 'Wormhole' in sui_project.network_config['packages']:
        package_id = sui_project.network_config['packages']['Wormhole']
    else:
        package_id = sui_project.Wormhole[-1]
    return SuiPackage(
        package_id,
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
    wormhole = load_wormhole()
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


def load_token_bridge():
    if 'packages' in sui_project.network_config and 'TokenBridge' in sui_project.network_config['packages']:
        package_id = sui_project.network_config['packages']['TokenBridge']
    else:
        package_id = sui_project.TokenBridge[-1]
    return SuiPackage(
        package_id,
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
    token_bridge = load_token_bridge()
    wormhole = load_wormhole()

    token_bridge.setup.complete(
        wormhole.state.State[-1],
        token_bridge.setup.DeployerCap[-1],
        get_upgrade_cap_by_package_id(token_bridge.package_id)
    )


def init_mock(net: str = "sui-testnet"):
    if net not in ["sui-testnet", "sui-devnet"]:
        return
    omniswap_mock = load_omniswap_mock()
    test_coins = load_test_coins()
    omniswap_mock.setup.setup_pool(test_coins.faucet.Faucet[-1])


def pool(x_type, y_type):
    return f"{sui_project.OmniSwapMock[-1]}::pool::Pool<{sui_project.OmniSwapMock[-1]}::setup::OmniSwapMock, {x_type}, {y_type}>"


def treasury_cap(coin_type):
    return f"0x2::coin::TreasuryCap<{coin_type}>"


def coin_metadata(coin_type):
    return f"0x2::coin::CoinMetadata<{coin_type}>"


def usdt():
    return f"{sui_project.TestCoins[-1]}::usdt::USDT"


def usdc():
    return f"{sui_project.TestCoins[-1]}::usdc::USDC"


def btc():
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
        "OmniSwapMock": sui_project.OmniSwapMock[-1],
        "Wormhole": sui_project.Wormhole[-1],
        "TokenBridge": sui_project.TokenBridge[-1],
        "TestCoins": sui_project.TestCoins[-1],
    }

    if "packages" not in config["networks"]["sui-testnet"]:
        config["networks"]["sui-testnet"]["packages"] = {}

    for package_name in packages:
        config["networks"]["sui-testnet"]["packages"][package_name] = packages[package_name]

    wormhole = load_wormhole()
    token_bridge = load_token_bridge()
    test_coins = load_test_coins()
    omniswap = load_omniswap()
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
        "Pool<OmniSwapMock, USDT, USDC>": sui_project[SuiObject.from_type(pool(usdt(), usdc()))][-1],
        "Pool<OmniSwapMock, BTC, USDT>": sui_project[SuiObject.from_type(pool(btc(), usdt()))][-1],
        "Pool<OmniSwapMock, USDC, BTC>": sui_project[SuiObject.from_type(pool(usdc(), btc()))][-1]
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
            "address": str(usdt().replace("0x", "")),
            "decimal": 6
        },
        "USDC": {
            "name": "USDC",
            "address": str(usdc().replace("0x", "")),
            "decimal": 6
        },
        "BTC": {
            "name": "BTC",
            "address": str(btc().replace("0x", "")),
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


def attest_token(coin_type):
    token_bridge = load_token_bridge()
    wormhole = load_wormhole()

    result = sui_project.pay_sui([0])
    zero_coin = result['objectChanges'][-1]['objectId']
    metadata = sui_project[SuiObject.from_type(coin_metadata(coin_type))][-1]
    token_bridge.token_bridge.attest_token(
        token_bridge.state.State[-1],
        wormhole.state.State[-1],
        zero_coin,
        metadata,
        0,
        clock(),
        type_arguments=[coin_type]
    )


# for testnet
def register_wormhole_token():
    attest_token(usdt())
    attest_token(usdc())
    attest_token(btc())


def main():
    net = "sui-testnet"
    print(f"Current sui network:{net}")

    # for testnet
    setup_test_coins(net)
    setup_omniswap_mock(net)
    setup_wormhole(net)
    init_wormhole()
    setup_token_bridge(net)
    init_token_bridge()
    init_mock(net)
    register_wormhole_token()

    # deploy
    omniswap_package = SuiPackage(package_path=omniswap_sui_path)
    omniswap_package.publish_package(gas_budget=500000000, replace_address=dict(
        test_coins=None,
        omniswap_mock=None,
        wormhole=None,
        token_bridge=None,
    ))

    wormhole = load_wormhole()
    wormhole_state = wormhole.state.State[-1]
    facet_manager = omniswap_package.wormhole_facet.WormholeFacetManager[-1]

    print(f"FacetManager:{facet_manager}\n")

    omniswap_package.wormhole_facet.init_wormhole(
        facet_manager,
        wormhole_state,
        sui_project.network_config["wormhole"]["chainid"]
    )

    wormhole_fee = omniswap_package.wormhole_facet.WormholeFee[-1]
    storage = omniswap_package.wormhole_facet.Storage[-1]
    price_manager = omniswap_package.so_fee_wormhole.PriceManager[-1]

    print(f"FacetStorage:{storage}\n"
          f"PriceManager:{price_manager}\n"
          f"WormholeFee:{wormhole_fee}")

    # set so fee
    so_fee_decimal = 1e8
    omniswap_package.wormhole_facet.set_so_fees(wormhole_fee, int(1e-3 * so_fee_decimal))

    # set reserve
    reserve_decimal = 1e8
    omniswap_package.wormhole_facet.set_wormhole_reserve(
        facet_manager,
        storage,
        int(sui_project.network_config["wormhole"]["actual_reserve"] * reserve_decimal),
        int(sui_project.network_config["wormhole"]["estimate_reserve"] * reserve_decimal)
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
            gas_per_bytes
        )


if __name__ == "__main__":
    main()
