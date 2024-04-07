import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv, dotenv_values
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair

load_dotenv()


@lru_cache()
def get_config(network: str = "devnet"):
    with Path(__file__).parent.parent.joinpath("config.yaml").open() as fp:
        config = yaml.safe_load(fp)
        return config[network]


@lru_cache()
def get_payer_by_env(name="OMNISWAP_KEY", env_file=None):
    if env_file is None:
        env_file = Path(__file__).parent.parent.joinpath(".env")
    env = dotenv_values(env_file)
    private_key = eval(env.get(name))
    owner = Keypair.from_bytes(bytes(private_key))
    print(f"owner={owner.pubkey()}")
    return owner


@lru_cache()
def get_payer():
    bytes_string = os.environ.get("TEST_OWNER")
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    owner = Keypair.from_bytes(bytes(raw_key))

    print(f"owner={owner.pubkey()}")

    return owner


@lru_cache()
def get_proxy():
    bytes_string = os.environ.get("TEST_REDEEM_PROXY")
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    proxy = Keypair.from_bytes(bytes(raw_key))

    print(f"proxy={proxy.pubkey()}")

    return proxy


@lru_cache()
def get_price_manager():
    bytes_string = os.environ.get("TEST_PRICE_MANAGER")
    assert bytes_string is not None, "empty solana wallet envs"

    raw_key = eval(bytes_string)

    manager = Keypair.from_bytes(bytes(raw_key))

    print(f"price_manager={manager.pubkey()}")

    return manager


def get_client(network: str = "devnet"):
    rpc_url = get_config(network)["rpc_url"]
    return AsyncClient(rpc_url)


if __name__ == "__main__":
    get_payer().pubkey()
