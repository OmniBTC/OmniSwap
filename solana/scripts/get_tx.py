import asyncio

from solders.signature import Signature
from config import get_client


async def get_tx():
    client = get_client()
    await client.is_connected()

    tx_id = "4SHthfTuTaa2CuDFY2KFC9NZTQ4By5WNfR7rxN5QTJc1jL499FE2iuakwuXYkPRRwaFqj8862YcWm1W5GrjZWB5m"
    resp = await client.get_transaction(Signature.from_string(tx_id))
    print(resp.value.to_json())

    await client.close()


asyncio.run(get_tx())
