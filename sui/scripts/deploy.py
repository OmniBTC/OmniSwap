from sui_brownie import SuiPackage, sui_brownie

from scripts import sui_project
from scripts.struct import omniswap_sui_path

from pathlib import Path


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
            ".move/https___github_com_OmniBTC_wormhole_git_d26d9407fb6a4f17db29e1028202bb1c9f76cf8b/sui/wormhole")),
    )

    wormhole_package.program_publish_package(gas_budget=500000000)


def load_wormhole():
    return SuiPackage(
        package_id=sui_project.Wormhole[-1],
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
            ".move/https___github_com_OmniBTC_wormhole_git_d26d9407fb6a4f17db29e1028202bb1c9f76cf8b/sui/token_bridge")),
    )

    token_bridge_package.program_publish_package(gas_budget=500000000,
                                                 replace_address=dict(token_bridge="0x0", wormhole=None))


def load_token_bridge():
    return SuiPackage(
        package_id=sui_project.TokenBridge[-1],
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

    # deploy
    omniswap_package = SuiPackage(package_path=omniswap_sui_path, package_id=sui_project.OmniSwap[-1])
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
