import json
import logging

import requests

import aptos_brownie


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
        sequence: int,
        src_wormhole_id: int = None,
        url: str = None
):
    """
    Get signed vaa
    :param src_wormhole_id:
    :param sequence:
    :param url:
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
    if url is None:
        url = "http://wormhole-testnet.sherpax.io"
    if src_wormhole_id is None:
        data = {
            "method": "GetSignedVAA",
            "params": [
                str(sequence),
            ]
        }
    else:
        data = {
            "method": "GetSignedVAA",
            "params": [
                str(sequence),
                src_wormhole_id,
            ]
        }
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()


def get_signed_vaa_by_to(
        to_chain: int,
        to: str = None,
        count: int = None,
        url: str = None,
):
    """
    Get signed vaa
    :param to_chain:
    :param to:
    :param count:
    :param url:
    :return: dict
        [{'_id': '634a804c25eccbc77a0dbcbb',
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
        'version': 1}]
    """
    if url is None:
        url = "http://wormhole-testnet.sherpax.io"
    if count is None:
        count = 10
    if to is None:
        data = {
            "method": "GetSignedVAAByTo",
            "params": [
                to_chain
            ]
        }
    else:
        data = {
            "method": "GetSignedVAAByTo",
            "params": [
                to_chain,
                str(to),
                count
            ]
        }
    try:
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        return response.json()
    except:
        return []


def get_pending_data(url: str = None) -> list:
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
    if url is None:
        # url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
        url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    try:
        response = requests.get(url)
        result = response.json()["record"]
        if isinstance(result, list):
            result.sort(key=lambda x: x["sequence"])
            return result
        else:
            return []
    except:
        return []
