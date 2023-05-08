from pprint import pprint

from sui_brownie import SuiPackage

from scripts import sui_project
from scripts.deploy import clock, attest_token


def global_config():
    return sui_project.network_config['objects']['GlobalConfig']


def btc():
    return sui_project.network_config['tokens']['Cetus-BTC']['address']


def btc_supply():
    return sui_project.network_config['objects']['BTCSupply']


def eth():
    return sui_project.network_config['tokens']['Cetus-ETH']['address']


def eth_supply():
    return sui_project.network_config['objects']['ETHSupply']


def usdc():
    return sui_project.network_config['tokens']['Cetus-USDC']['address']


def usdc_supply():
    return sui_project.network_config['objects']['USDCSupply']


def usdt():
    return sui_project.network_config['tokens']['Cetus-USDT']['address']


def usdt_supply():
    return sui_project.network_config['objects']['USDTSupply']


def usdc_eth_pool():
    return sui_project.network_config['pools']['Cetus-USDC-ETH']['pool_id']


def usdt_usdc_pool():
    return sui_project.network_config['pools']['Cetus-USDT-USDC']['pool_id']


def load_cetus_faucet():
    return SuiPackage(
        sui_project.network_config['packages']['CetusFaucet'],
        package_name="CetusFaucet",
    )


def load_cetus():
    return SuiPackage(
        sui_project.network_config['packages']['CetusClmm'],
        package_name="CetusClmm",
    )


def load_cetus_scripts():
    return SuiPackage(
        sui_project.network_config['packages']['CetusScripts'],
        package_name="CetusScripts",
    )


def claim_from_cetus_faucet(token):
    faucet = load_cetus_faucet()
    if "BTC" in token:
        faucet.btc.faucet(btc_supply())
    elif "ETH" in token:
        faucet.eth.faucet(eth_supply())
    elif "USDC" in token:
        faucet.usdc.faucet(usdc_supply())
    elif "USDT" in token:
        faucet.usdt.faucet(usdt_supply())
    else:
        raise Exception("Invalid token")


def get_coins(coin_type):
    result = sui_project.client.suix_getCoins(sui_project.account.account_address, coin_type, None, None)
    return [c["coinObjectId"] for c in result["data"]]


def register_cetus_tokens():
    attest_token(usdt())
    attest_token(usdc())
    attest_token(btc())
    attest_token(eth())


def get_amount_out():
    cetus_scripts = load_cetus_scripts()

    result = cetus_scripts.fetcher_script.calculate_swap_result.inspect(
        usdt_usdc_pool(),
        True,
        True,
        int(1 * 1e6),
        type_arguments=[usdt(), usdc()]
    )

    pprint(result)


def get_amount_in():
    cetus = load_cetus()

    result = cetus.pool.calculate_swap_result.inspect(
        usdt_usdc_pool(),
        True,
        False,
        int(1 * 1e6),
        type_arguments=[usdt(), usdc()]
    )

    pprint(result)


def add_liquidity():
    cetus_scripts = load_cetus_scripts()

    cetus_scripts.pool_script.open_position_with_liquidity_with_all(
        global_config(),
        usdt_usdc_pool(),
        4294967244,
        52,
        get_coins(usdt()),
        get_coins(usdc()),
        int(1 * 1e6),
        int(1 * 1e6),
        True,
        clock(),
        type_arguments=[usdt(), usdc()]
    )


if __name__ == "__main__":
    get_amount_out()
    # register_cetus_tokens()
