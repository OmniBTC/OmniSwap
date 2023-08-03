from brownie import (
    DiamondCutFacet,
    SoDiamond,
    DiamondLoupeFacet,
    DexManagerFacet,
    WithdrawFacet,
    OwnershipFacet,
    GenericSwapFacet,
    LibCorrectSwapV1,
    SerdeFacet,
    network,
    ConnextFacet,
    LibSoFeeConnextV1,
)
import json
import os
from pathlib import Path
from brownie import config
from scripts.helpful_scripts import change_network

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
connext_bridge_token_file = os.path.join(root_path, "export/ConnextChainPath.json")


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


def export_connext_info():
    deployed_contract = read_json(str(Path(__file__).parent.parent.joinpath("export/mainnet/ContractDeployed.json")))
    support_networks = ['arbitrum-main', 'optimism-main', 'polygon-main', 'bsc-main']

    connext_bridge_token_info = {}
    for network in support_networks:
        connext_info = config['networks'][network]['bridges']['connext']
        connext = connext_info['connext']
        chain_id = connext_info['chainid']
        domain_id = connext_info['domain_id']
        tokens = connext_info['token']
        support_tokens = []
        for token in tokens:
            if 'next' in token:
                continue
            token_info = tokens[token]
            token_address = token_info['address']
            decimal = token_info['decimal']
            token_info = {
                'TokenName': str(token).upper(),
                'Address': token_address,
                'Decimal': decimal,
                'ChainPath': []
            }
            support_tokens.append(token_info)

        network_info = {
            'SoDiamond': deployed_contract[network]["SoDiamond"],

            'ChainId': chain_id,
            'DomainId': domain_id,
            'Connext': connext,
            'SupportTokens': support_tokens
        }

        connext_bridge_token_info[network] = network_info

    write_file(connext_bridge_token_file, connext_bridge_token_info)


def export_chain_path():
    connext_bridge_token_info = read_json(connext_bridge_token_file)

    tokens_path = {}
    for network in connext_bridge_token_info:
        network_info = connext_bridge_token_info[network]
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

    for network in connext_bridge_token_info:
        network_info = connext_bridge_token_info[network]

        support_tokens = network_info['SupportTokens']
        for token in support_tokens:
            chain_path = [
                token_path
                for token_path in tokens_path[token['TokenName']]
                if token_path['Address'] != token['Address']
            ]
            token['ChainPath'] = chain_path

    write_file(connext_bridge_token_file, connext_bridge_token_info)


def export_deploy_contract(nets=None):
    if nets is None:
        nets = ["arbitrum-main", "optimism-main", "polygon-main", "bsc-main"]

    deploy_contract = [
        DiamondCutFacet,
        DiamondLoupeFacet,
        DexManagerFacet,
        ConnextFacet,
        WithdrawFacet,
        OwnershipFacet,
        GenericSwapFacet,
        SerdeFacet,
        SoDiamond,
        LibSoFeeConnextV1,
        LibCorrectSwapV1
    ]

    data = {}
    for net in nets:
        data[net] = {}
        change_network(net)
        for c in deploy_contract:
            data[net][c._name] = c[-1].address

    write_file(str(Path(__file__).parent.parent.joinpath("export/mainnet/ContractDeployed.json")), data)


def main():
    export_connext_info()
    export_chain_path()


if __name__ == '__main__':
    export_chain_path()
