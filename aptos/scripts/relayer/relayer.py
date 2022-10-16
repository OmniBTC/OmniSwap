import json

import requests

from scripts.struct import padding_to_bytes
from scripts.utils import aptos_brownie


def get_wormhole_info(package: aptos_brownie.AptosPackage) -> dict:
    """Get token bridge info"""
    info = {}
    for net, c in package.config["networks"].items():
        try:
            info[c["wormhole"]["chainid"]] = c["wormhole"]["token_bridge"]
        except:
            pass
    return info


def get_signed_vaa(
        package: aptos_brownie.AptosPackage,
        src_wormhole_id: int,
        sequence: int,
        src_emitter_address: str = None
):
    """
    Get signed vaa
    :param package:
    :param src_wormhole_id:
    :param sequence:
    :param src_emitter_address:
    :return: dict
        {'_id': '634a804c25eccbc77a0dbcbb',
        'emitterAddress': '0x000000000000000000000000f890982f9310df57d00f659cf4fd87e65aded8d7',
        'emitterChainId': 2,
        'sequence': '2337',
        'consistencyLevel': 1,
        'guardianSetIndex': 0,
        'hash': '0xf94bf64a709ab9aaf70a8ef02676a875648b3ebd7c5940ace790baef36030ca4',
        'hexString': '010000000001006...',
        'nonce': 2224160768,
        'payload': '0x01000000000000000000000000000000000000000000',
        'signatures': [['0x696d2300a3798196634db775dca14d6e861997f077b0bbb950e01107d8b94026',
        '0x4d6812a66cf1cca41657c7cba1d83b4c1485776cde0d9e9be24d3a69ab96fcdb', 27, 0]],
        'timestamp': 1665809748,
        'version': 1}
    """
    url = "http://localhost:5066"
    if src_emitter_address is None:
        token_bridge_info = get_wormhole_info(package)
        src_emitter_address = token_bridge_info[src_wormhole_id]
    data = {
        "method": "GetSignedVAA",
        "params": [
            src_wormhole_id,
            padding_to_bytes(src_emitter_address, padding="left"),
            str(sequence)
        ]
    }
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()


def get_pending_data() -> list:
    """
    Get data for pending relayer
    :return: list
        [{'chainName': 'bsc-test',
        'extrinsicHash': '0x63942108e3e0b4ca70ba331acc1c7419ffc43ebcc10e75abe4b0c05a4ce2e2d5',
        'srcWormholeChainId': 0,
        'dstWormholeChainId': 0,
        'sequence': 2110, '
        blockTimestamp': 0}]
    """
    url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    try:
        response = requests.get(url)
        return response.json()["record"]
    except:
        return []


def main():
    package = aptos_brownie.AptosPackage(".")
    while True:
        pending_data = get_pending_data()
        for d in pending_data:
            try:
                vaa = get_signed_vaa(package, int(d["srcWormholeChainId"]), int(d["sequence"]))
            except:
                continue
            # todo! fix
            package["wormhole_facet::complete_so_swap"]()


if __name__ == "__main__":
    print(get_signed_vaa(aptos_brownie.AptosPackage("../../"), 2, 2337, "0xf890982f9310df57d00f659cf4fd87e65aded8d7"))
    print(get_pending_data())
