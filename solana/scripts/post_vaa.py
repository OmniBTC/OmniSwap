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
    vaa = "0100000000010003245911bd48438a4d075bad3f5d7d4a326a918828ce5d85e9673d4966de23bf16af52994a0ec2ad255fee37ab5f6b21d6791da28b26b7b10e2b8c4e05a1e800016538b6cb0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013bb0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001dc3779efc394bf8f4ddc09c41bad9f8aae8345431d4b17a20b99c9ac209c2a80000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102ffe0208960d459b2828ed88b88667e931586b991d63b8cb00eebb6aa61514e96311cae2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70101200e03685f8e909053e458121c66f5a76aedc7706aa11c82f8aa952a8f2b7879a9203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea72010a72302b3fed346d77240c165c64c7aafa5012ada611aad6ddd14829c9bd02d0016576869726c706f6f6c2c343330363138363230353236"
    post_vaa(vaa)
