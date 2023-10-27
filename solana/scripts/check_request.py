import asyncio
from omniswap.accounts.cross_request import CrossRequest
from helper import deriveCrossRequestKey
from config import get_client, get_config


async def omniswap_estimate_relayer_fee(
    network="devnet",
):
    client = get_client(network)
    await client.is_connected()

    config = get_config(network)

    omniswap_program_id = config["program"]["SoDiamond"]

    start = 0
    while True:
        req_key = deriveCrossRequestKey(omniswap_program_id, sequence=start)

        req = await CrossRequest.fetch(client, req_key)
        if req is None:
            print(f"request={req_key}, None")
        else:
            print(f"request={req_key}, Some")

        start += 1


asyncio.run(omniswap_estimate_relayer_fee())
