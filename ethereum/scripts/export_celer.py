import json
import os
import urllib
import requests

from brownie import Contract, config, interface

from scripts.helpful_scripts import (
    get_celer_message_bus,
    change_network,
    get_celer_oracles,
)

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
    dst_decimal: int,
):
    fixed_amount = 10**src_decimal
    pegged_amount = 10**dst_decimal

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
        "1": {"USDC": 6, "USDT": 6, "WETH": 18},
        # Optimism
        "10": {"USDC": 6, "USDT": 6, "WETH": 18},
        # BSC
        "56": {"USDC": 18, "USDT": 18, "WETH": 18},
        # Polygon
        "137": {"USDC": 6, "USDT": 6, "WETH": 18},
        # Zksync-era
        "324": {"USDC": 6, "WETH": 18},
        # Polygon-zkevm
        "1101": {"WETH": 18},
        # Arbitrum
        "42161": {"USDC": 6, "USDT": 6, "WETH": 18},
        # Avalanche
        "43114": {"USDC": 6, "USDT": 6, "WETH": 18},
    }

    for chain1, tokens1 in chain_tokens.items():
        for chain2, tokens2 in chain_tokens.items():
            if chain1 == chain2:
                continue
            for token, decimal in tokens1.items():
                try:
                    if check_bridge_token(
                        chain1, chain2, token, decimal, tokens2[token]
                    ):
                        print(
                            chain1,
                            "===>>===",
                            chain2,
                            ":",
                            token,
                            decimal,
                            tokens2[token],
                        )
                    else:
                        print(
                            chain1,
                            "===/////===",
                            chain2,
                            ":",
                            token,
                            decimal,
                            tokens2[token],
                        )
                except KeyError:
                    continue


def check_celer_bridge_tokens(bridge_tokens):
    for chain1, tokens1 in bridge_tokens.items():
        for chain2, tokens2 in bridge_tokens.items():
            if chain1 == chain2:
                continue
            for token in tokens1:
                try:
                    decimal1 = tokens1[token]["decimal"]
                except KeyError:
                    continue

                try:
                    decimal2 = tokens2[token]["decimal"]
                except KeyError:
                    continue

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
        "324",  # Zksync-era
        "1101",  # Polygon-zkevm
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
                    "address": token["token"]["address"],
                }

        bridge_tokens[chain] = filter_tokens

    # print(json.dumps(bridge_tokens))

    check_celer_bridge_tokens(bridge_tokens)

    write_file(tmp_celer_bridge_token, bridge_tokens)

    return bridge_tokens


def export_main_celer_chain_path():
    # bridge_tokens = read_json(tmp_celer_bridge_token)
    bridge_tokens = get_celer_bridge_tokens()

    celer_contracts = {
        "1": {
            "cBridge": "0x5427FEFA711Eff984124bFBB1AB6fbf5E3DA1820",
            "MessageBus": "0x4066d196a423b2b3b8b054f4f40efb47a74e200c",
        },
        "10": {
            "cBridge": "0x9D39Fc627A6d9d9F8C831c16995b209548cc3401",
            "MessageBus": "0x0D71D18126E03646eb09FEc929e2ae87b7CAE69d",
        },
        "56": {
            "cBridge": "0xdd90E5E87A2081Dcf0391920868eBc2FFB81a1aF",
            "MessageBus": "0x95714818fdd7a5454f73da9c777b3ee6ebaeea6b",
        },
        "137": {
            "cBridge": "0x88DCDC47D2f83a99CF0000FDF667A468bB958a78",
            "MessageBus": "0xaFDb9C40C7144022811F034EE07Ce2E110093fe6",
        },
        "324": {
            "cBridge": "0x54069e96C4247b37C2fbd9559CA99f08CD1CD66c",
            "MessageBus": "0x9a98a376D30f2c9A0A7332715c15D940dE3da0e2",
        },
        "1101": {
            "cBridge": "0xD46F8E428A06789B5884df54E029e738277388D1",
            "MessageBus": "0x9Bb46D5100d2Db4608112026951c9C965b233f4D",
        },
        "42161": {
            "cBridge": "0x1619DE6B6B20eD217a58d00f37B9d47C7663feca",
            "MessageBus": "0x3ad9d0648cdaa2426331e894e980d0a5ed16257f",
        },
        "43114": {
            "cBridge": "0xef3c714c9425a8F3697A9C969Dc1af30ba82e5d4",
            "MessageBus": "0x5a926eeeafc4d217add17e9641e8ce23cd01ad57",
        },
    }

    chain_names = {
        "1": "mainnet",
        "10": "optimism-main",
        "324": "zksync2-main",
        "56": "bsc-main",
        "137": "polygon-main",
        "1101": "zkevm-main",
        "42161": "arbitrum-main",
        "43114": "avax-main",
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

                try:
                    paths.append(
                        {
                            "CelerChainId": int(chain2),
                            "Address": tokens2[token]["address"],
                            "Decimal": tokens2[token]["decimal"],
                        }
                    )
                except KeyError:
                    continue

            token_paths[token] = {
                "Address": tokens1[token]["address"],
                "Decimal": tokens1[token]["decimal"],
                "ChainPath": paths,
            }

        chain_paths[chain_names[chain1]] = {
            "CelerChainId": chain1,
            "Bridge": celer_contracts[chain1]["cBridge"],
            "MessageBus": celer_contracts[chain1]["MessageBus"],
            "SupportToken": token_paths,
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
                    "Decimal": config["networks"][net]["bridges"]["celer"]["token"][
                        token
                    ]["decimal"],
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

        print(
            net,
            ":",
            token,
            "min=",
            min_send / 10**decimal,
            "max=",
            max_send / 10**decimal,
        )


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
        "zksync2-main",
        "zkevm-main",
    ]

    chain_path = read_json(celer_chain_path)

    for net in networks:
        print(f"[check_main_celer_config] current net: {net}")

        try:
            change_network(net)
        except:
            continue

        check_celer_contracts(net, chain_path[net])


def get_price(contract):
    price_feed = Contract.from_abi(
        "IAggregatorV3Interface", contract, interface.IAggregatorV3Interface.abi
    )

    decimals = price_feed.decimals()
    print(price_feed.description(), "decimas:", decimals)

    (
        _round_id,
        price,
        _started,
        _updated,
        _answeredInRound,
    ) = price_feed.latestRoundData()

    print("price:", float(price / 10**decimals))
    print("=====================================")


def check_main_oracles():
    main_chain_oracles = {
        "mainnet": {
            "ETHUSD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
            "AVAXUSD": "0xFF3EEb22B5E3dE6e705b44749C2559d704923FD7",
            "BNBUSD": "0x14e613AC84a31f709eadbdF89C6CC390fDc9540A",
            "MATICUSD": "0x7bAC85A8a13A4BcD8abb3eB7d6b4d632c5a57676",
        },
        "optimism-main": {
            "ETHUSD": "0x13e3Ee699D1909E989722E753853AE30b17e08c5",
            "AVAXUSD": "0x5087Dc69Fd3907a016BD42B38022F7f024140727",
            "BNBUSD": "0xD38579f7cBD14c22cF1997575eA8eF7bfe62ca2c",
            "MATICUSD": "0x0ded608AFc23724f614B76955bbd9dFe7dDdc828",
        },
        "bsc-main": {
            "ETHUSD": "0x9ef1B8c0E4F7dc8bF5719Ea496883DC6401d5b2e",
            "AVAXUSD": "0x5974855ce31EE8E1fff2e76591CbF83D7110F151",
            "BNBUSD": "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE",
            "MATICUSD": "0x7CA57b0cA6367191c94C8914d7Df09A57655905f",
        },
        "polygon-main": {
            "ETHUSD": "0xF9680D99D6C9589e2a93a78A04A279e509205945",
            "AVAXUSD": "0xe01eA2fbd8D76ee323FbEd03eB9a8625EC981A10",
            "BNBUSD": "0x82a6c4AF830caa6c97bb504425f6A66165C2c26e",
            "MATICUSD": "0xAB594600376Ec9fD91F8e885dADF0CE036862dE0",
        },
        "arbitrum-main": {
            "ETHUSD": "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612",
            "AVAXUSD": "0x8bf61728eeDCE2F32c456454d87B5d6eD6150208",
            "BNBUSD": "0x6970460aabF80C5BE983C6b74e5D06dEDCA95D4A",
            "MATICUSD": "0x52099D4523531f678Dfc568a7B1e5038aadcE1d6",
        },
        "avax-main": {
            "ETHUSD": "0x976B3D034E162d8bD72D6b9C989d545b839003b0",
            "AVAXUSD": "0x0A77230d17318075983913bC2145DB16C7366156",
            # "BNBUSD": "",
            "MATICUSD": "0x1db18D41E4AD2403d9f52b5624031a2D9932Fd73",
        },
    }

    for net, oracles in main_chain_oracles.items():
        print(f"[check_oracles] current net: {net}")

        change_network(net)
        # from config
        chain_oracles = get_celer_oracles()

        for oracle in chain_oracles.values():
            assert oracle["address"] == oracles[oracle["pair"]]
            get_price(oracle["address"])


def check_main_online_oracles():
    chain_oracles = {
        "arbitrum-main": {
            "address": "0x937AfcA1bb914405D37D55130184ac900ce5961f",
            "dst_chain": [1, 10, 56, 137, 43114],
        },
        "avax-main": {
            "address": "0x7e482c0DA0481414311097cF058f0E64B20c9D6C",
            "dst_chain": [1, 10, 56, 137, 42161],
        },
        "bsc-main": {
            "address": "0xD7eC4E3DaC58e537Eb24fef4c3F7B011aeA50f30",
            "dst_chain": [1, 10, 137, 42161, 43114],
        },
        "mainnet": {
            "address": "0xf5110f6211a9202c257602CdFb055B161163a99d",
            "dst_chain": [10, 56, 137, 42161, 43114],
        },
        "optimism-main": {
            "address": "0x19370bE0D726A88d3e6861301418f3daAe3d798E",
            "dst_chain": [1, 56, 137, 42161, 43114],
        },
        "polygon-main": {
            "address": "0xb7e02565426d47174fF4231D490Ff6B827306377",
            "dst_chain": [1, 10, 56, 42161, 43114],
        },
    }

    for net, oracle in chain_oracles.items():
        print(f"[check_main_online_oracles] current net: {net}")
        change_network(net)

        abi_str = '[{"inputs":[{"internalType":"uint256","name":"_soFee","type":"uint256"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"ReentrancyError","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint64","name":"chainId","type":"uint64"},{"components":[{"internalType":"address","name":"router","type":"address"},{"internalType":"bool","name":"flag","type":"bool"}],"indexed":false,"internalType":"struct LibSoFeeCelerV1.ChainlinkConfig[]","name":"chainlink","type":"tuple[]"},{"indexed":false,"internalType":"uint256","name":"interval","type":"uint256"}],"name":"UpdatePriceConfig","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint64","name":"chainId","type":"uint64"},{"indexed":false,"internalType":"uint256","name":"interval","type":"uint256"}],"name":"UpdatePriceInterval","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"sender","type":"address"},{"indexed":false,"internalType":"uint256","name":"currentRatio","type":"uint256"}],"name":"UpdatePriceRatio","type":"event"},{"inputs":[],"name":"RAY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_amountIn","type":"uint256"}],"name":"getFees","outputs":[{"internalType":"uint256","name":"s","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"}],"name":"getPriceRatio","outputs":[{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"},{"components":[{"components":[{"internalType":"address","name":"router","type":"address"},{"internalType":"bool","name":"flag","type":"bool"}],"internalType":"struct LibSoFeeCelerV1.ChainlinkConfig[]","name":"chainlink","type":"tuple[]"},{"internalType":"uint256","name":"interval","type":"uint256"}],"internalType":"struct LibSoFeeCelerV1.PriceConfig","name":"_config","type":"tuple"}],"name":"getPriceRatioByChainlink","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_amountIn","type":"uint256"}],"name":"getRestoredAmount","outputs":[{"internalType":"uint256","name":"r","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTransferForGas","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getVersion","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint64","name":"","type":"uint64"}],"name":"priceConfig","outputs":[{"internalType":"uint256","name":"interval","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint64","name":"","type":"uint64"}],"name":"priceData","outputs":[{"internalType":"uint256","name":"currentPriceRatio","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_soFee","type":"uint256"}],"name":"setFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"},{"components":[{"internalType":"address","name":"router","type":"address"},{"internalType":"bool","name":"flag","type":"bool"}],"internalType":"struct LibSoFeeCelerV1.ChainlinkConfig[]","name":"_chainlink","type":"tuple[]"},{"internalType":"uint256","name":"_interval","type":"uint256"}],"name":"setPriceConfig","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"},{"internalType":"uint256","name":"_interval","type":"uint256"}],"name":"setPriceInterval","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"},{"internalType":"uint256","name":"_ratio","type":"uint256"}],"name":"setPriceRatio","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"soFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint64","name":"_chainId","type":"uint64"}],"name":"updatePriceRatio","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]'

        print(oracle["address"])
        contract = Contract.from_abi(
            "LibSoFeeCelerV1", oracle["address"], json.loads(abi_str)
        )

        for dst_chain in oracle["dst_chain"]:
            print("dst chain:", dst_chain)
            print(contract.getPriceRatio(dst_chain))


def main():
    check_main_celer_config()
    # check_main_oracles()
    # check_main_online_oracles()
