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
    vaa = "01000000000100fc6948db1b1f99a2a8fde8468a2cb04d33bee763091aaa4dd5460ff2ae61532760a411675c450ffb002e8460050cc6da7b7b3f68938c419fb60dd89b78c05faa01653f15750000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013d50f030000000000000000000000000000000000000000000000000000000005f5e1000000000000000000000000008ce306d8a34c99b23d3054072ba7fc013684e8a100043eb54bfb6f363a4b14879f4189fecd37bf35acfc86572f9879f620736ecf3228000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac203248c6dc21ad3943b7084b2e39d59697c001754a1d7a8978d793257c47d19c332038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
    post_vaa(vaa)
