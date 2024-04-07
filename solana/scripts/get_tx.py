import asyncio

from solders.signature import Signature
from solana_config import get_client


async def get_tx():
    client = get_client()
    await client.is_connected()

    tx_id = "4eDqgghqZL4Hn7TMMZvCBBe87PL439Ytyc3kqovA9WetJd9h8MFFAKpUPp4VKp5BKLrw6J6x43yPhfGviFRjFht8"
    resp = await client.get_transaction(
        Signature.from_string(tx_id), max_supported_transaction_version=0
    )
    print(resp.value.transaction.meta)

    await client.close()


asyncio.run(get_tx())
