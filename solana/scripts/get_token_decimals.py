import asyncio

from solders.pubkey import Pubkey

from solana_config import get_client


async def get_token_decimals(token_mint):
    client = get_client()

    token_mint_key = Pubkey.from_string(token_mint)

    resp = await client.get_account_info_json_parsed(token_mint_key)

    print(resp.value.data.parsed["info"]["decimals"])

    pass


asyncio.run(get_token_decimals("xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"))
