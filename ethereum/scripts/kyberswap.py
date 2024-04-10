from brownie import config
import requests


NET_NAME = {
    "optimism-main": "optimism",
    "arbitrum-main": "arbitrum",
}


def get_kyber_swap_router(net):
    return config["networks"][net]["swap"]["IMetaAggregationRouterV2"]["router"]


def get_kyber_routes(chain, token_in, token_out, amount_in):
    base_url = f"https://aggregator-api.kyberswap.com/{chain}/api/v1/routes"

    resp = requests.get(
        base_url,
        params={
            "tokenIn": token_in,
            "tokenOut": token_out,
            "amountIn": amount_in,
            "saveGas": False,
            "gasInclude": True,
        },
    )
    return resp.json()


def build_kyber_swap_route(chain, route_summary, sender, reciver, slippage=100):
    """Build a kyber swap route

    Args:
        chain (_type_): chain name (e.g. "optimism")
        route_summary (_type_): routeSummary in result from get_kyber_routes
        sender (_type_): sodiamond address
        reciver (_type_): sodiamond address
        slippage (int, optional): [0, 20000] 10 means 0.1%. Defaults to 100.
    """
    base_url = f"https://aggregator-api.kyberswap.com/{chain}/api/v1/route/build"

    result = requests.post(
        base_url,
        json={
            "routeSummary": route_summary,
            "sender": sender,
            "recipient": reciver,
            "slippageTolerance": slippage,
        },
    )

    return result.json()


def kyber_calldata(net, sender, receiver, send_token, recv_token, amount_in):
    chain_name = NET_NAME[net]
    result = get_kyber_routes(chain_name, send_token, recv_token, amount_in)

    route_summary = result["data"]["routeSummary"]
    route_data = build_kyber_swap_route(
        chain_name,
        route_summary,
        sender,
        receiver,
    )
    calldata = route_data["data"]["data"]
    router_address = route_data["data"]["routerAddress"]

    return router_address, calldata
