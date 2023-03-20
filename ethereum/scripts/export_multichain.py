import json
import os
import requests

from brownie import config

MULTICHAIN_URL = "https://bridgeapi.multichain.org/v4/tokenlistv4/"

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
multi_chain_path = os.path.join(root_path, "export/MultiChainPath.json")


def write_file(file: str, data):
    print("save to:", file)
    with open(file, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def read_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return []


def get_all_tokens_info(chainId):
    url = MULTICHAIN_URL + chainId

    print(f"\n  {url}\n")

    response = requests.get(url)

    return json.loads(response.text)


def get_multichain_bridge_tokens():
    select_chains = {
        "1": "mainnet",
        "10": "optimism-main",
        "56": "bsc-main",
        "137": "polygon-main",
        "42161": "arbitrum-main",
        "43114": "avax-main",
    }

    select_tokens = ["ETH", "OETH", "WETH", "WETH.e", "USDC", "USDC.e"]

    select_routers = {
        "1": "0x1633D66Ca91cE4D81F63Ea047B7B19Beb92dF7f3",
        "10": "0x1633D66Ca91cE4D81F63Ea047B7B19Beb92dF7f3",
        "56": "0x400b971099e0ebfda2c03a3063739cb5398734a6",
        "137": "0x1633D66Ca91cE4D81F63Ea047B7B19Beb92dF7f3",
        "42161": "0x1633D66Ca91cE4D81F63Ea047B7B19Beb92dF7f3",
        "43114": "0x1633D66Ca91cE4D81F63Ea047B7B19Beb92dF7f3",
    }

    chain_path = {}
    for chain, net in select_chains.items():
        all_tokens_info = get_all_tokens_info(chain)
        bridge_token = {}
        for token_info in all_tokens_info.values():
            if token_info["symbol"] not in select_tokens:
                continue

            # print(token_info["chainId"], token_info["symbol"])

            bridge_token[token_info["symbol"]] = {}
            bridge_token[token_info["symbol"]]["ChainPath"] = []
            is_valid = False
            for dest, tokens in token_info["destChains"].items():
                if dest not in select_chains.keys():
                    continue

                for token in tokens.values():
                    if (
                        token["type"] == "FAST_ROUTER_V7"
                        and token["router"].lower() == select_routers[chain].lower()
                    ):
                        bridge_token[token_info["symbol"]]["AnyAddress"] = token[
                            "fromanytoken"
                        ]["address"]
                        bridge_token[token_info["symbol"]]["AnyDecimal"] = token[
                            "fromanytoken"
                        ]["decimals"]
                        bridge_token[token_info["symbol"]][
                            "UnderlyingAddress"
                        ] = token_info["address"]
                        bridge_token[token_info["symbol"]][
                            "UnderlyingDecimal"
                        ] = token_info["decimals"]

                        any_to = {
                            "ChainId": dest,
                            "AnyAddress": token["anytoken"]["address"],
                            "AnyDecimal": token["anytoken"]["decimals"],
                            "UnderlyingAddress": token["underlying"]["address"],
                            "UnderlyingDecimal": token["underlying"]["decimals"],
                        }

                        bridge_token[token_info["symbol"]]["ChainPath"].append(any_to)

                        is_valid = True

                        fee = []
                        if token["MinimumSwapFee"] == token["MaximumSwapFee"]:
                            fee.append(token["MaximumSwapFee"])
                        else:
                            fee.append(token["SwapFeeRatePerMillion"] + "%")

                        print(
                            "src:",
                            chain,
                            "dst:",
                            dest,
                            token_info["symbol"],
                            "Min:",
                            token["MinimumSwap"],
                            "Max:",
                            token["BigValueThreshold"],
                            "Fee: ",
                            fee,
                        )

            if not is_valid:
                del bridge_token[token_info["symbol"]]

        check_main_multichain_config(net, chain, select_routers[chain], bridge_token)

        chain_path[select_chains[chain]] = {
            "ChainId": chain,
            "FAST_ROUTER_V7": select_routers[chain],
            "SupportToken": bridge_token,
        }

        # print(json.dumps(chain_path))
    write_file(multi_chain_path, chain_path)


def get_multichain_info(mainnet):
    return config["networks"][mainnet]["bridges"]["multichain"]


def check_main_multichain_config(net, chainId, router, bridgeToken):
    multichain_info = get_multichain_info(net)

    print(multichain_info)

    assert multichain_info["chainid"] == int(chainId)
    assert multichain_info["fast_router"] == router

    for name, info in multichain_info["token"].items():
        assert info["anytoken"] == bridgeToken[name]["AnyAddress"], bridgeToken[name][
            "AnyAddress"
        ]
        assert info["address"] == bridgeToken[name]["UnderlyingAddress"], bridgeToken[
            name
        ]["UnderlyingAddress"]
        assert info["decimal"] == bridgeToken[name]["UnderlyingDecimal"], bridgeToken[
            name
        ]["UnderlyingDecimal"]


def main():
    get_multichain_bridge_tokens()
