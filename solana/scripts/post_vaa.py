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
    vaa = "0100000000010027098711a5996a1ef0def2e6f54ada772086114b05307afef65c76713c7e7f29213a25cf23f98ce44bb7f8a7a726627c9d108858366e72f8bb8f6d064fa57cde01653b901e0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013d40f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea700013eb54bfb6f363a4b14879f4189fecd37bf35acfc86572f9879f620736ecf3228000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc01010301196020b0dc57c0801d4c2ed2b7035795eda424c42c9c887c28b680ec3223ea390bbc022038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea701014030386238336535396664303734393166356233666166313864363336643134616630623661663465613836366232376235633531383463333236613231626638403362343432636233393132313537663133613933336430313334323832643033326235666665636430316132646266316237373930363038646630303265613740313061373233303262336665643334366437373234306331363563363463376161666135303132616461363131616164366464643134383239633962643032640016576869726c706f6f6c2c343038343934383031383338"
    post_vaa(vaa)
