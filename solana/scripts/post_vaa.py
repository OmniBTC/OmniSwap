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
    vaa = "0100000000010071554763c9a4d515b370984c6d5b7a16732b20b633784da7e79c96b21c593cd53e6415fb2a5ed0bd33341745fbf24ff27135ee6c24af6e3f63c86e3656c412a4006540bf760000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013de0f0300000000000000000000000000000000000000000000000000000000000027103b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea700013eb54bfb6f363a4b14879f4189fecd37bf35acfc86572f9879f620736ecf3228000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac2064668548b29fe67f3c5bed09c8ad2a4e000000006540bf2903d96ed62447e821204418d22de631f119689cf4811cab850d339d474804c250b19ea16f0ebe26ef7f203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
    post_vaa(vaa)
