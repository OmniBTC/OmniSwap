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
    vaa = "010000000001009325759e66abc55a528f22af788b85a87183ba09e4242a65713a97ea41babc17084c9f5f87d9476ecbeccd0cc8a69dae95b59a1e40a25f97d643355c96f681140065432fa10000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013fb0f0300000000000000000000000000000000000000000000000000000000000186a03b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea700013636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102fe042061b9be0ccc363e71e20e6502a6c3e90739297d780868c10b01dce9b26082081b2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f193820000000000000000000000000000000000000000000000000000000000000000001012028dd308f27ddd70a066fdf47bb26e28987a41b4fa5d25c0196fcfef028a8b102203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea720069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f00000000001000f576869726c706f6f6c2c3932333431"
    post_vaa(vaa)
