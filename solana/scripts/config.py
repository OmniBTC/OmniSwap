import json
from functools import cache

import yaml

from pathlib import Path
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient


@cache
def get_config(network: str = "devnet"):
    with Path(__file__).parent.parent.joinpath("config.yaml").open() as fp:
        config = yaml.safe_load(fp)
        return config[network]


def get_payer():
    default_path = Path.home().joinpath(".config/solana/id.json")
    with open(default_path, "r") as file:
        raw_key = json.load(file)

    payer = Keypair.from_bytes(bytes(raw_key))

    print(f"payer={payer.pubkey()}")

    return payer


def get_client(network: str = "devnet"):
    rpc_url = get_config(network)["rpc_url"]
    return AsyncClient(rpc_url)
