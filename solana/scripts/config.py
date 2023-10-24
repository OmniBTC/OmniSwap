import os

from dotenv import load_dotenv
from functools import cache

import yaml

from pathlib import Path
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

load_dotenv()

@cache
def get_config(network: str = "devnet"):
    with Path(__file__).parent.parent.joinpath("config.yaml").open() as fp:
        config = yaml.safe_load(fp)
        return config[network]


@cache
def get_payer(silent=False):
    bytes_string =  os.environ.get('TEST_OWNER')
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    owner = Keypair.from_bytes(bytes(raw_key))

    if not silent:
        print(f"owner={owner.pubkey()}")

    return owner

@cache
def get_proxy():
    bytes_string =  os.environ.get('TEST_REDEEM_PROXY')
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    proxy = Keypair.from_bytes(bytes(raw_key))

    print(f"proxy={proxy.pubkey()}")

    return proxy

@cache
def get_price_manager():
    bytes_string =  os.environ.get('TEST_PRICE_MANAGER')
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    manager = Keypair.from_bytes(bytes(raw_key))

    print(f"price_manager={manager.pubkey()}")

    return manager


def get_client(network: str = "devnet"):
    rpc_url = get_config(network)["rpc_url"]
    return AsyncClient(rpc_url)


if __name__ == '__main__':
    get_payer().pubkey()