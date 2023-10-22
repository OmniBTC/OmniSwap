import json
from pathlib import Path
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

# solana-devnet
rpc_url_devnet = "https://api.devnet.solana.com"
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
]


def get_payer():
    default_path = Path.home().joinpath(".config/solana/id.json")
    with open(default_path, "r") as file:
        raw_key = json.load(file)

    payer = Keypair.from_bytes(bytes(raw_key))

    print(f"payer={payer.pubkey()}")

    return payer


def get_client(rpc_url=rpc_url_devnet):
    return AsyncClient(rpc_url)
