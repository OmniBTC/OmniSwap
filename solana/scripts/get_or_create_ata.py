import os
import subprocess
from pathlib import Path

from solders.pubkey import Pubkey

from solana_config import get_config


def get_or_create_associated_token_account(
    token_mint: str, user_address: str, network="devnet"
):
    config = get_config(network)

    js_file_name = "get_or_create_ata.js"
    js_file_path = Path(__file__).parent.joinpath("test_dex").joinpath(js_file_name)

    new_env = {
        "ANCHOR_PROVIDER_URL": config["rpc_url"],
        "ANCHOR_WALLET": os.environ.get("TEST_OWNER"),
    }

    result = subprocess.run(
        ["node", str(js_file_path), token_mint, user_address],
        env={**os.environ, **new_env},
        capture_output=True,
        text=True,
        check=True,
    )

    return Pubkey.from_string(str(result.stdout).strip())


if __name__ == "__main__":
    ata = get_or_create_associated_token_account(
        "xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz",
        "4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9",
    )
    print(ata)
