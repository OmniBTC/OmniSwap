import os
import subprocess
from pathlib import Path

from solana_config import get_config


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
    vaa = "0100000000010019c9469347188ba1dd54550b822d9fdf72c5f5c342fcc09511fb6e4bc00a37392ccee23355eda90b3d5c6ee03929061f958c8fbd9a4670b98e57fabf30fc0fb50065411f340000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013e80f0300000000000000000000000000000000000000000000000000000000000f4240069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f0000000000100013636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20e2deb5206cd68c25b4edc31a2ba648a6ca5e14e76ce496bba217de48c246cde12038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938200000000000000000000000000000000000000000000000000000000000000000"
    post_vaa(vaa)
