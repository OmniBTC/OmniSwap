import json
import os
from pathlib import Path
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

# solana-devnet
ANCHOR_PROVIDER_URL = os.environ.get("ANCHOR_PROVIDER_URL")
wormhole_devnet = "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5"
token_bridge_devnet = "DZnkkTmCiFWfYTfT41X3Rd1kDgozqzxWaHqsw6W4x2oe"
lookup_table_devnet = Pubkey.from_string("ESxWFjHVo2oes1eAQiwkAUHNTTUT9Xm5zsSrE7QStYX8")
lookup_table_addresses_devnet = [
    # token_bridge_config
    Pubkey.from_string("8PFZNjn19BBYVHNp4H31bEW7eAmu78Yf2RKV8EeA461K"),
    # token_bridge_authority_signer
    Pubkey.from_string("3VFdJkFuzrcwCwdxhKRETGxrDtUVAipNmYcLvRBDcQeH"),
    # token_bridge_custody_signer
    Pubkey.from_string("H9pUTqZoRyFdaedRezhykA1aTMq7vbqRHYVhpHZK2QbC"),
    # token_bridge_mint_authority
    Pubkey.from_string("rRsXLHe7sBHdyKU3KY3wbcgWvoT1Ntqudf6e9PKusgb"),
    # wormhole_bridge
    Pubkey.from_string("6bi4JGDoRwUs9TYBuvoA7dUVyikTJDrJsJU1ew6KVLiu"),
    # token_bridge_emitter
    Pubkey.from_string("4yttKWzRoNYS2HekxDfcZYmfQqnVWpKiJ8eydYRuFRgs"),
    # wormhole_fee_collector
    Pubkey.from_string("7s3a1ycs16d6SNDumaRtjcoyMaTDZPavzgsmS3uUZYWX"),
    # token_bridge_sequence
    Pubkey.from_string("9QzqZZvhxoHzXbNY9y2hyAUfJUzDwyDb7fbDs9RXwH3"),
    # Rent
    Pubkey.from_string("SysvarRent111111111111111111111111111111111"),
    # Clock
    Pubkey.from_string("SysvarC1ock11111111111111111111111111111111"),
    # ComputeBudget
    Pubkey.from_string("ComputeBudget111111111111111111111111111111"),
    # System
    Pubkey.from_string("11111111111111111111111111111111"),
    # whirlpool_program
    Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"),
    # test_usdc_pool
    Pubkey.from_string("b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV"),
    # test token
    Pubkey.from_string("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"),
    # usdc token
    Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"),
    # test_usdc_pool vault_a
    Pubkey.from_string("3dycP3pym3q6DgUpZRviaavaScwrrCuC6QyLhiLfSXge"),
    # test_usdc_pool vault_b
    Pubkey.from_string("969UqMJSqvgxmNuAWZx91PAnLJU825qJRAAcEVQMWASg"),
    # omniswap sender config
    Pubkey.from_string("GR7xDWrbWcEYsnz1e5WDfy3iXvPw5tmWjeV8MY1sVHCp"),
    # omniswap fee config
    Pubkey.from_string("EcZK7hAyxzjeCL1zM9FKWeWcdziF4pFHiUCJ5r2886TP"),
    # omniswap bsc(4) price manage
    Pubkey.from_string("EofptCXfgVxRk1vxBLNP1Zk6SSPBiPdkYWVPgTLzbzGR"),
    # omniswap bsc(4) foreign_contract
    Pubkey.from_string("FV2SB6pUGWABHxmnoVUxxdTVctzY7puAQon38sJ8oNm"),
]


def get_payer():
    default_path = Path.home().joinpath(".config/solana/id.json")
    with open(default_path, "r") as file:
        raw_key = json.load(file)

    payer = Keypair.from_bytes(bytes(raw_key))

    print(f"payer={payer.pubkey()}")

    return payer


def get_client(rpc_url=ANCHOR_PROVIDER_URL):
    assert rpc_url != "", "invalid env ANCHOR_PROVIDER_URL"
    return AsyncClient(rpc_url)
