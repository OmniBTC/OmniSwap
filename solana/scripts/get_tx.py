import asyncio

from solders.signature import Signature
from config import get_client


async def get_tx():
    client = get_client()
    await client.is_connected()

    tx_id = "48HeHgLW3K5wwMSkpezSgesb2LceHvF8ruYdzwWawzJ7JmBEhXEmq9Bt53tjKGaodKGbsCJzAUsRxgBrFozPjxw5"
    resp = await client.get_transaction(
        Signature.from_string(tx_id), max_supported_transaction_version=0
    )
    print(resp.value.to_json())

    await client.close()


asyncio.run(get_tx())
