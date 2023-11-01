import json
import os
import subprocess
from pathlib import Path

from solders.pubkey import Pubkey
from solana_config import get_config


def get_whirlpool_quote_config(
    whirlpool_address: str, token_mint_in: str, ui_amount_in: str, network="devnet"
):
    config = get_config(network)

    js_file_name = "get_whirlpool_quote_config.js"
    js_file_path = Path(__file__).parent.joinpath("test_dex").joinpath(js_file_name)

    new_env = {
        "ANCHOR_PROVIDER_URL": config["rpc_url"],
        "ANCHOR_WALLET": os.environ.get("TEST_OWNER"),
    }

    result = subprocess.run(
        ["node", str(js_file_path), whirlpool_address, token_mint_in, ui_amount_in],
        env={**os.environ, **new_env},
        capture_output=True,
        text=True,
        check=True,
    )

    print(result.stdout)

    try:
        config = json.loads(result.stdout)

        return {
            "whirlpool_program": Pubkey.from_string(config["whirlpool_program"]),
            "whirlpool": Pubkey.from_string(config["whirlpool"]),
            "token_mint_a": Pubkey.from_string(config["token_mint_a"]),
            "token_mint_b": Pubkey.from_string(config["token_mint_b"]),
            "token_owner_account_a": Pubkey.from_string(
                config["token_owner_account_a"]
            ),
            "token_owner_account_b": Pubkey.from_string(
                config["token_owner_account_b"]
            ),
            "token_vault_a": Pubkey.from_string(config["token_vault_a"]),
            "token_vault_b": Pubkey.from_string(config["token_vault_b"]),
            "tick_array_0": Pubkey.from_string(config["tick_array_0"]),
            "tick_array_1": Pubkey.from_string(config["tick_array_1"]),
            "tick_array_2": Pubkey.from_string(config["tick_array_2"]),
            "oracle": Pubkey.from_string(config["oracle"]),
            "is_a_to_b": config["is_a_to_b"],
            "amount_in": int(config["amount_in"]),
            "estimated_amount_out": int(config["estimated_amount_out"]),
            "min_amount_out": int(config["min_amount_out"]),
        }
    except json.JSONDecodeError as e:
        print("parse quote config fail", e)


if __name__ == "__main__":
    get_whirlpool_quote_config(
        "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV",
        "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS",
        "1",
    )
