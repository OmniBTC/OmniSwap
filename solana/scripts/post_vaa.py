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
    vaa = "010000000001005825c18b9f9bb0f5f416bb83b05e6117211354689043d485685042417c20e88306926661e55b4cf0a77f905b5d175fb27e8f864b6bcea93484a856a53765e3cb00653f74be0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013dc0f030000000000000000000000000000000000000000000000000000000005f5e1000000000000000000000000008ce306d8a34c99b23d3054072ba7fc013684e8a100043eb54bfb6f363a4b14879f4189fecd37bf35acfc86572f9879f620736ecf3228000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102ff582009979eb9d52522d2e1e96a08ee97334084440d7ba19342a85752093c4e1adede2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7010120940539d0ba099c4a169fef0a64d5b7834385c949018d69608b682f221cac7c33200e5623c833433c5191bc501ad65ffad64a42ceafd1abe4c7d70549f2602eb1432010a72302b3fed346d77240c165c64c7aafa5012ada611aad6ddd14829c9bd02d0014576869726c706f6f6c2c35333731333734363137"
    post_vaa(vaa)
