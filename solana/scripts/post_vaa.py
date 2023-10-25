import json
import os
import subprocess
from pathlib import Path

from solders.pubkey import Pubkey
from config import get_config


def post_vaa(vaa: str, network="devnet"):
    config = get_config(network)

    js_file_name = "postvaa.js"
    js_file_path = Path(__file__).parent.joinpath("test_dex").joinpath(js_file_name)

    new_env = {
        "ANCHOR_PROVIDER_URL": config["rpc_url"],
        "ANCHOR_WALLET": os.environ.get("TEST_OWNER"),
    }

    wormhole_program = config["program"]["Wormhole"]

    result = subprocess.run(
        ["node", str(js_file_path), wormhole_program, vaa],
        env={**os.environ, **new_env},
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout)


if __name__ == "__main__":
    vaa = "01000000000100b0ebb8232182198b50246f7ba2d2bbcfe2ccb029757bc5261ccc35e4190590d209d9d58ee6a0594e117743baead5bbcfa4bb82f8b13fb3ced1585d12ba4c57b000653795ba0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013ac0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001dc3779efc394bf8f4ddc09c41bad9f8aae8345431d4b17a20b99c9ac209c2a80000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20493294b88e30b66848a5977de2a6a10001e8031bdd3682a07005e6674b7d69cc2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
    post_vaa(vaa)
