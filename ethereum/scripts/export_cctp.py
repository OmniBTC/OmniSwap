import time
import json
import os
from pathlib import Path

from brownie import config, project

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
cctp_bridge_token_file = os.path.join(root_path, "export/CCTPChainPath.json")


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


def export_cctp_info():
    support_networks = ['arbitrum-main', 'avax-main', "optimism-main", "mainnet", "base-main"]

    cctp_bridge_token_info = {}
    for network in support_networks:
        cctp_info = config['networks'][network]['bridges']['cctp']
        chain_id = config['networks'][network]['chainid']
        domain_id = cctp_info['domain_id']
        support_tokens = [
            {
                'TokenName': "USDC",
                'Address': config['networks'][network]["token"]["usdc"]["address"],
                'Decimal': config['networks'][network]["token"]["usdc"]["decimal"],
                'ChainPath': []
            }
        ]

        network_info = {
            'ChainId': chain_id,
            'DomainId': domain_id,
            'SupportTokens': support_tokens
        }

        cctp_bridge_token_info[network] = network_info

    write_file(cctp_bridge_token_file, cctp_bridge_token_info)


def export_chain_path():
    cctp_bridge_token_info = read_json(cctp_bridge_token_file)

    tokens_path = {}
    for network in cctp_bridge_token_info:
        network_info = cctp_bridge_token_info[network]
        domain_id = network_info['DomainId']
        support_tokens = network_info['SupportTokens']
        for token in support_tokens:
            token_name = token['TokenName']
            token_address = token['Address']
            decimal = token['Decimal']
            if token_name not in tokens_path.keys():
                tokens_path[token_name] = []
            tokens_path[token_name].append({
                'Address': token_address,
                'DomainId': domain_id,
                'Decimal': decimal,
            })

    for network in cctp_bridge_token_info:
        network_info = cctp_bridge_token_info[network]

        support_tokens = network_info['SupportTokens']
        for token in support_tokens:
            chain_path = [
                token_path
                for token_path in tokens_path[token['TokenName']]
                if token_path['Address'] != token['Address']
            ]
            token['ChainPath'] = chain_path

    write_file(cctp_bridge_token_file, cctp_bridge_token_info)


def main():
    project_path = Path(__file__).parent.parent
    p = project.load(project_path)
    p.load_config()
    export_cctp_info()
    time.sleep(1)
    export_chain_path()


if __name__ == '__main__':
    main()
