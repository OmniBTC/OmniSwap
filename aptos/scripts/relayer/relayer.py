import json
import logging
import time

import requests

from scripts.serde import parse_vaa_to_wormhole_payload
from scripts.struct import padding_to_bytes, omniswap_aptos_path, decode_hex_to_ascii, hex_str_to_vector_u8
from scripts.utils import aptos_brownie

FORMAT = '%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")


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
            str(sequence),
            src_wormhole_id,
            padding_to_bytes(src_emitter_address, padding="left"),
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
    package = aptos_brownie.AptosPackage(str(omniswap_aptos_path))
    has_process = {}
    while True:
        pending_data = get_pending_data()
        for d in pending_data:
            if (int(d["srcWormholeChainId"]), int(d["sequence"])) in has_process:
                continue
            has_process[(int(d["srcWormholeChainId"]), int(d["sequence"]))] = True
            try:
                vaa = get_signed_vaa(package, int(d["srcWormholeChainId"]), int(d["sequence"]))["hexString"]
            except Exception as e:
                logger.error(f"Get signed vaa error: {e}")
                continue
            try:
                # Use bsc-test to decode, too slow may need to change bsc-mainnet
                vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(package, "bsc-test", vaa)
            except Exception as e:
                logger.error(f"Parse signed vaa error: {e}")
                continue
            try:
                final_asset_id = decode_hex_to_ascii(wormhole_data[2][5])
                if len(wormhole_data[3]) == 0:
                    ty_args = [final_asset_id, final_asset_id, final_asset_id, final_asset_id]
                elif len(wormhole_data[3]) == 1:
                    s1 = decode_hex_to_ascii(wormhole_data[3][0][2])
                    s2 = final_asset_id
                    ty_args = [s1, s2, s2, s2]
                elif len(wormhole_data[3]) == 2:
                    s1 = decode_hex_to_ascii(wormhole_data[3][0][2])
                    s2 = decode_hex_to_ascii(wormhole_data[3][1][2])
                    s3 = final_asset_id
                    ty_args = [s1, s2, s3, s3]
                elif len(wormhole_data[3]) == 3:
                    s1 = decode_hex_to_ascii(wormhole_data[3][0][2])
                    s2 = decode_hex_to_ascii(wormhole_data[3][1][2])
                    s3 = decode_hex_to_ascii(wormhole_data[3][2][2])
                    s4 = final_asset_id
                    ty_args = [s1, s2, s3, s4]
                else:
                    logger.error(f"Dst swap too much")
                    raise OverflowError
                package["so_diamond::complete_so_swap"](hex_str_to_vector_u8(vaa), ty_args=ty_args)
            except Exception as e:
                logger.error(f"Decode hex error: {e}")
                continue

        time.sleep(60)
