import json
import os
from pathlib import Path

from brownie import config, project

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
bool_bridge_token_file = os.path.join(root_path, "export/BoolChainPath.json")


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


def export_bool_info():
    support_networks = ['arbitrum-main', 'optimism-main', 'polygon-main', "bsc-main", "zksync2-main", "avax-main",
                        "base-main", "bevm-main"
                        ]

    bool_bridge_token_info = {}
    for network in support_networks:
        bool_info = config['networks'][network]['bridges']['bool']
        pools = bool_info['pools']
        bool_router = bool_info["router"]
        bool_factory = bool_info["factory"]
        chain_id = bool_info["chainid"]

        support_tokens = []
        for token in pools:
            pool_id = pools[token]['pool_id']
            decimal = pools[token]['decimals']
            pool_address = pools[token]['pool_address']
            token_address = pools[token]['token_address']
            token_info = {
                'TokenName': str(token).upper(),
                'Address': token_address,
                'Decimal': decimal,
                'PoolId': pool_id,
                'PoolAddress': pool_address,
                'ChainPath': []
            }
            support_tokens.append(token_info)

        network_info = {
            'ChainId': chain_id,
            'BoolRouter': bool_router,
            'BoolFactory': bool_factory,
            'SupportTokens': support_tokens
        }

        bool_bridge_token_info[network] = network_info
    print(bool_bridge_token_info)
    write_file(bool_bridge_token_file, bool_bridge_token_info)


def export_chain_path():
    bool_bridge_token_info = read_json(bool_bridge_token_file)

    tokens_path = {}
    for network in bool_bridge_token_info:
        network_info = bool_bridge_token_info[network]
        support_tokens = network_info['SupportTokens']
        chain_id = network_info['ChainId']
        for token in support_tokens:
            token_name = token['TokenName']
            token_address = token['Address']
            decimal = token['Decimal']
            pool_id = token['PoolId']
            if token_name not in tokens_path.keys():
                tokens_path[token_name] = []
            tokens_path[token_name].append({
                'Address': token_address,
                'ChainId': chain_id,
                'PoolId': pool_id,
                'Decimal': decimal,
            })

    for network in bool_bridge_token_info:
        network_info = bool_bridge_token_info[network]
        cur_chain_id = network_info["ChainId"]

        support_tokens = network_info['SupportTokens']
        for token in support_tokens:
            chain_path = [
                token_path
                for token_path in tokens_path[token['TokenName']]
                if cur_chain_id != token_path['ChainId']
            ]
            token['ChainPath'] = chain_path

    write_file(bool_bridge_token_file, bool_bridge_token_info)


def main():
    project_path = Path(__file__).parent.parent
    p = project.load(project_path)
    p.load_config()
    export_bool_info()
    export_chain_path()


if __name__ == '__main__':
    main()
