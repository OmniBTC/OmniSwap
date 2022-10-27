import json
import logging
import threading
import time

import requests
from brownie import network

from scripts.serde_aptos import parse_vaa_to_wormhole_payload
from scripts.struct import omniswap_aptos_path, decode_hex_to_ascii, hex_str_to_vector_u8
from scripts.utils import aptos_brownie

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

package = aptos_brownie.AptosPackage(str(omniswap_aptos_path), network="aptos-testnet")


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
        return response.json()["record"]
    except Exception as _e:
        return []


def process_v1(
        dstWormholeChainId: int = 22,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[{package.network}]")
    local_logger.info("Starting process v1...")
    has_process = {}
    while True:
        if "test" in package.network or "test" == "goerli":
            url = "http://wormhole-testnet.sherpax.io"
        else:
            url = "http://wormhole-vaa.chainx.org"
        result = get_signed_vaa_by_to(dstWormholeChainId, url=url)
        result = [d for d in result if (int(d["emitterChainId"]), int(d["sequence"])) not in has_process]
        local_logger.info(f"Get signed vaa by to length: {len(result)}")
        for d in result[::-1]:
            has_process[(int(d["emitterChainId"]), int(d["sequence"]))] = True
            try:
                # Use bsc-test to decode, too slow may need to change bsc-mainnet
                d["hexString"] = "0x" + d["hexString"]
                vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(package, network.show_active(),
                                                                                       d["hexString"])
            except Exception as e:
                local_logger.error(f'Parse signed vaa for emitterChainId:{d["emitterChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            interval = 3 * 60 * 60
            if time.time() > int(vaa_data[1]) + interval:
                local_logger.warning(
                    f'For emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} '
                    f'beyond {int(interval / 60)}min')
                continue
            if transfer_data[4] != dstSoDiamond:
                local_logger.warning(
                    f'For emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} dstSoDiamond: {dstSoDiamond} '
                    f'not match: {transfer_data[4]}')
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
                package["so_diamond::complete_so_swap"](hex_str_to_vector_u8(d["hexString"]), ty_args=ty_args)
            except Exception as e:
                local_logger.error(f'Complete so swap for emitterChainId:{d["emitterChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            logger.info(f'Process emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} success!')
        time.sleep(60)


def process_v2(
        _dstWormholeChainId: int = 22,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[{package.network}]")
    local_logger.info("Starting process v2...")
    has_process = {}
    while True:
        pending_data = get_pending_data()
        pending_data = [d for d in pending_data if
                        (int(d["srcWormholeChainId"]), int(d["sequence"])) not in has_process]
        local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        for d in pending_data:
            has_process[(int(d["srcWormholeChainId"]), int(d["sequence"]))] = True
            try:
                if "test" in package.network or "test" == "goerli":
                    url = "http://wormhole-testnet.sherpax.io"
                else:
                    url = "http://wormhole-vaa.chainx.org"
                vaa = get_signed_vaa(int(d["sequence"]), int(d["srcWormholeChainId"]), url=url)
                if vaa is None:
                    continue
                vaa = vaa["hexString"]
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            try:
                # Use bsc-test to decode, too slow may need to change bsc-mainnet
                vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(package, network.show_active(),
                                                                                       vaa)
            except Exception as e:
                local_logger.error(f'Parse signed vaa for emitterChainId:{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            interval = 3 * 60 * 60
            if time.time() > int(vaa_data[1]) + interval:
                local_logger.warning(
                    f'For emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} '
                    f'beyond {int(interval / 60)}min')
                continue
            if transfer_data[4] != dstSoDiamond:
                local_logger.warning(
                    f'For emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} '
                    f'dstSoDiamond: {dstSoDiamond} '
                    f'not match: {transfer_data[4]}')
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
                local_logger.error(f'Complete so swap for emitterChainId:{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            logger.info(f'Process emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} success!')
        time.sleep(60)


def main():
    print(f'SoDiamond:{package.network_config["SoDiamond"]}')
    t1 = threading.Thread(target=process_v1, args=(22, package.network_config["SoDiamond"]))
    # t2 = threading.Thread(target=process_v2, args=(22, package.network_config["SoDiamond"]))
    t1.start()
    # t2.start()
    t1.join()
    # t2.join()


def single_process():
    process_v1(22, package.network_config["SoDiamond"])
