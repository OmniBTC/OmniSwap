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
    vaa = "01000000000100e4f557d2040650a16efc8c2dd8e3eeb0ec74b6bc4607c55f5e23c8dd456d249c3c40ffaaf4a3bfdb9b14063832ee7ae1c185b433bc2e3ac1bd689bddd3a2897c006538f9940000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013c30f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001dc3779efc394bf8f4ddc09c41bad9f8aae8345431d4b17a20b99c9ac209c2a80000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102ffe020167284e775396258bb597c0c5395ee9954608dc054ee0278107a415baca1ad8a2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea701012008b83e59fd07491f5b3faf18d636d14af0b6af4ea866b27b5c5184c326a21bf8203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea72010a72302b3fed346d77240c165c64c7aafa5012ada611aad6ddd14829c9bd02d0016576869726c706f6f6c2c343235353137303131303839"
    post_vaa(vaa)
