import json
import os
import urllib
import requests

from brownie import Contract, config, interface

from scripts.helpful_scripts import get_celer_message_bus, change_network

CELER_GATEWAY = "https://cbridge-prod2.celer.app/v2/"

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
tmp_celer_bridge_token = os.path.join(root_path, "export/TmpCelerBridgeToken.json")
celer_chain_path = os.path.join(root_path, "export/CelerChainPath.json")


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


def check_bridge_token(
        src_chain_id: str,
        dst_chain_id: str,
        symbol: str,
        src_decimal: int,
        dst_decimal: int
):
    fixed_amount = 10 ** src_decimal
    pegged_amount = 10 ** dst_decimal

    if symbol != "WETH":
        fixed_amount = 500 * fixed_amount
        pegged_amount = 500 * pegged_amount

    params = {
        "src_chain_id": src_chain_id,
        "dst_chain_id": dst_chain_id,
        "token_symbol": symbol,
        "usr_addr": 0x0,
        "slippage_tolerance": 10000,  # 1%
        "amt": fixed_amount,
        "is_pegged": "false",
    }

    url = CELER_GATEWAY + "estimateAmt" + "?" + urllib.parse.urlencode(params)

    print(f"\n  {url}\n")

    response = requests.get(url)
    data = json.loads(response.text)

    try:
        estimated_amount = int(data["estimated_receive_amt"])
    except:
        estimated_amount = pegged_amount

    # print("estimated_amount: ", estimated_amount)

    return estimated_amount != pegged_amount


def simple_check_bridge_tokens():
    chain_tokens = {
        # Ethereum
        "1": {
            "USDC": 6,
            "USDT": 6,
            "WETH": 18
        },
        # Optimism
        "10": {
            "USDC": 6,
            "USDT": 6,
            "WETH": 18
        },
        # BSC
        "56": {
            "USDC": 18,
            "USDT": 18,
            "WETH": 18
        },
        # Polygon
        "137": {
            "USDC": 6,
            "USDT": 6,
            "WETH": 18
        },
        # Arbitrum
        "42161": {
            "USDC": 6,
            "USDT": 6,
            "WETH": 18
        },
        # Avalanche
        "43114": {
            "USDC": 6,
            "USDT": 6,
            "WETH": 18
        }
    }

    for chain1, tokens1 in chain_tokens.items():
        for chain2, tokens2 in chain_tokens.items():
            if chain1 == chain2:
                continue
            for token, decimal in tokens1.items():
                if check_bridge_token(chain1, chain2, token, decimal, tokens2[token]):
                    print(chain1, "===>>===", chain2, ":", token, decimal, tokens2[token])
                else:
                    print(chain1, "===/////===", chain2, ":", token, decimal, tokens2[token])


def check_celer_bridge_tokens(bridge_tokens):
    for chain1, tokens1 in bridge_tokens.items():
        for chain2, tokens2 in bridge_tokens.items():
            if chain1 == chain2:
                continue
            for token in tokens1:
                decimal1 = tokens1[token]["decimal"]
                decimal2 = tokens2[token]["decimal"]

                if check_bridge_token(chain1, chain2, token, decimal1, decimal2):
                    print(chain1, "===>>===", chain2, ":", token, decimal1, decimal2)
                else:
                    print(chain1, "===/////===", chain2, ":", token, decimal1, decimal2)


def get_celer_bridge_tokens():
    select_chains = [
        "1",  # Ethereum
        "10",  # Optimism
        "56",  # BSC
        "137",  # Polygon
        "42161",  # Arbitrum
        "43114",  # Avalanche
    ]

    select_tokens = ["USDC", "USDT", "WETH"]

    url = CELER_GATEWAY + "getTransferConfigs"
    response = requests.get(url)
    config = json.loads(response.text)

    bridge_tokens = {}
    for (chain, tokens) in config["chain_token"].items():
        if chain not in select_chains:
            continue

        filter_tokens = {}
        for token in tokens["token"]:
            if token["token"]["symbol"] in select_tokens:
                del token["token"]["xfer_disabled"]
                filter_tokens[token["token"]["symbol"]] = {
                    "decimal": int(token["token"]["decimal"]),
                    "address": token["token"]["address"]
                }

        bridge_tokens[chain] = filter_tokens

    # print(json.dumps(bridge_tokens))

    check_celer_bridge_tokens(bridge_tokens)

    write_file(tmp_celer_bridge_token, bridge_tokens)

    return bridge_tokens


def export_main_celer_chain_path():
    bridge_tokens = read_json(tmp_celer_bridge_token)
    # bridge_tokens = get_celer_bridge_tokens()

    celer_contracts = {
        "1": {
            "cBridge": "0x5427FEFA711Eff984124bFBB1AB6fbf5E3DA1820",
            "MessageBus": "0x4066d196a423b2b3b8b054f4f40efb47a74e200c"
        },
        "10": {
            "cBridge": "0x9D39Fc627A6d9d9F8C831c16995b209548cc3401",
            "MessageBus": "0x0D71D18126E03646eb09FEc929e2ae87b7CAE69d"
        },
        "56": {
            "cBridge": "0xdd90E5E87A2081Dcf0391920868eBc2FFB81a1aF",
            "MessageBus": "0x95714818fdd7a5454f73da9c777b3ee6ebaeea6b"
        },
        "137": {
            "cBridge": "0x88DCDC47D2f83a99CF0000FDF667A468bB958a78",
            "MessageBus": "0xaFDb9C40C7144022811F034EE07Ce2E110093fe6"
        },
        "42161": {
            "cBridge": "0x1619DE6B6B20eD217a58d00f37B9d47C7663feca",
            "MessageBus": "0x3ad9d0648cdaa2426331e894e980d0a5ed16257f"
        },
        "43114": {
            "cBridge": "0xef3c714c9425a8F3697A9C969Dc1af30ba82e5d4",
            "MessageBus": "0x5a926eeeafc4d217add17e9641e8ce23cd01ad57"
        }
    }

    chain_names = {
        "1": "mainnet",
        "10": "optimism-main",
        "56": "bsc-main",
        "137": "polygon-main",
        "42161": "arbitrum-main",
        "43114": "avax-main"
    }

    chain_paths = {}
    for chain1, tokens1 in bridge_tokens.items():
        token_paths = {}
        for token, decimal in tokens1.items():
            paths = []
            for chain2, tokens2 in bridge_tokens.items():
                if chain1 == chain2:
                    continue

                # print(chain1, token, "===>>===", chain2, tokens2[token]["address"], tokens2[token]["decimal"])

                paths.append({
                    "CelerChainId": int(chain2),
                    "Address": tokens2[token]["address"],
                    "Decimal": tokens2[token]["decimal"]
                })
            token_paths[token] = {
                "Address": tokens1[token]["address"],
                "Decimal": tokens1[token]["decimal"],
                "ChainPath": paths
            }

        chain_paths[chain_names[chain1]] = {
            "CelerChainId": chain1,
            "Bridge": celer_contracts[chain1]["cBridge"],
            "MessageBus": celer_contracts[chain1]["MessageBus"],
            "SupportToken": token_paths
        }

    # print(json.dumps(chain_paths))

    write_file(celer_chain_path, chain_paths)


def get_celer_support_token(net):
    if "bridges" in config["networks"][net].keys():
        tokens = {}
        for token in config["networks"][net]["bridges"]["celer"]["token"]:
            if token in ["usdt", "usdc", "weth"]:
                tokens[token.upper()] = {
                    "ChainPath": [],
                    "Address": config["networks"][net]["bridges"]["celer"]["token"][
                        token
                    ]["address"],
                    "Decimal": config["networks"][net]["bridges"]["celer"]["token"][token][
                        "decimal"
                    ],
                }

        return tokens


def check_celer_contracts(net, net_config):
    message_bus_address = get_celer_message_bus()
    message_bus = Contract.from_abi(
        "ICelerMessageBus", message_bus_address, interface.ICelerMessageBus.abi
    )
    bridge_address = message_bus.liquidityBridge()
    bridge = Contract.from_abi(
        "ICelerBridge", bridge_address, interface.ICelerBridge.abi
    )

    assert message_bus_address == net_config["MessageBus"]
    assert bridge_address == net_config["Bridge"]

    support_tokens = get_celer_support_token(net)

    # check max_send and min_send
    for token, info in support_tokens.items():
        token_address = info["Address"]
        decimal = info["Decimal"]
        assert token_address == net_config["SupportToken"][token]["Address"]
        assert decimal == net_config["SupportToken"][token]["Decimal"]

        min_send = bridge.minSend(token_address)
        max_send = bridge.maxSend(token_address)

        print(net, ":", token, "min=", min_send / 10 ** decimal, "max=", max_send / 10 ** decimal)


def check_main_celer_config():
    # USDC min= 20.0 max= 3500000.0
    # USDT min= 20.0 max= 3500000.0
    # WETH min= 0.015 max= 950.0

    networks = [
        "mainnet",
        "bsc-main",
        "avax-main",
        "polygon-main",
        "arbitrum-main",
        "optimism-main",
    ]

    chain_path = read_json(celer_chain_path)

    for net in networks:
        print(f"[check_main_celer_config] current net: {net}")

        try:
            change_network(net)
        except:
            continue

        check_celer_contracts(net, chain_path[net])


def main():
    check_main_celer_config()
