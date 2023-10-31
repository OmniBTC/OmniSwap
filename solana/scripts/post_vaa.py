import os
import subprocess
from pathlib import Path

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
    vaa = "010000000001003f7809d06a070453f15f2e85d87dfc7b011aff765e2bc280dbd84e6ff72f1e04384b78e9fafacfcc1d7f5da8d15d1d0daa6f59924a1dd1cf0584b2d5ee103e9d01654118ec0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013e70f0300000000000000000000000000000000000000000000000000000000000f4240069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f0000000000100013636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac202a56b8e105c974ddc99eee2a293d857487b04cbed2c7ac05a475e03d68783ca12038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938200000000000000000000000000000000000000000000000000000000000000000"
    post_vaa(vaa)
