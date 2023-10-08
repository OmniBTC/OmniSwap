import json
from pathlib import Path
from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

# solana-devnet
rpc_url_devnet = (
    "https://solana-devnet.g.alchemy.com/v2/VaTALh1zwDTmrzIkcN_zPJG4QCym--nR"
)
wormhole_devnet = "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5"
token_bridge_devnet = "DZnkkTmCiFWfYTfT41X3Rd1kDgozqzxWaHqsw6W4x2oe"


def get_payer():
    default_path = Path.home().joinpath(".config/solana/id.json")
    with open(default_path, "r") as file:
        raw_key = json.load(file)

    payer = Keypair.from_bytes(bytes(raw_key))

    print(f"payer={payer.pubkey()}")

    return payer


def get_client(rpc_url=rpc_url_devnet):
    return AsyncClient(rpc_url)
