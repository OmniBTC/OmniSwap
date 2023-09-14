import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from brownie import network

from scripts.serde_aptos import parse_vaa_to_wormhole_payload
from scripts.serde_struct import omniswap_aptos_path, decode_hex_to_ascii, hex_str_to_vector_u8
import aptos_brownie

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

while True:
    try:
        package = aptos_brownie.AptosPackage(str(omniswap_aptos_path), network="aptos-mainnet")
        break
    except:
        pass
WORMHOLE_CHAINID_TO_NET = {
    package.config["networks"][net]["wormhole"]["chainid"]: net
    for net in package.config["networks"]
    if "wormhole" in package.config["networks"][net]
       and "chainid" in package.config["networks"][net]["wormhole"]
    if ("main" in package.network and "main" in net)
       or ("main" not in package.network and "main" not in net)
}


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
            return result
        else:
            return []
    except Exception as _e:
        return []


def process_vaa(
        dstSoDiamond: str,
        vaa_str: str,
        emitterChainId: str,
        sequence: str,
        local_logger,
        inner_interval: int = None,
        over_interval: int = None,
        is_admin: bool = False
) -> bool:
    try:
        # Use bsc-test to decode, too slow may need to change bsc-mainnet
        vaa_str = vaa_str if "0x" in vaa_str else "0x" + vaa_str
        vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(
            package, network.show_active(),
            vaa_str)
        dst_max_gas = wormhole_data[1]
        dst_max_gas_price = wormhole_data[0] / 1e10
        if "main" in package.network:
            assert dst_max_gas_price > 0, "dst_max_gas_price is 0"
    except Exception as e:
        local_logger.error(f'Parse signed vaa for emitterChainId:{emitterChainId}, '
                           f'sequence:{sequence} error: {e}')
        return False
    if inner_interval is not None and time.time() > int(vaa_data[1]) + inner_interval:
        local_logger.warning(
            f'For emitterChainId:{emitterChainId}, sequence:{sequence} '
            f'need in {int(inner_interval / 60)}min')
        return False

    if over_interval is not None and time.time() <= int(vaa_data[1]) + over_interval:
        local_logger.warning(
            f'For emitterChainId:{emitterChainId}, sequence:{sequence} '
            f'need out {int(over_interval / 60)}min')
        return False

    if transfer_data[4] != dstSoDiamond:
        local_logger.warning(
            f'For emitterChainId:{emitterChainId}, sequence:{sequence} dstSoDiamond: {dstSoDiamond} '
            f'not match: {transfer_data[4]}')
        return False

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
        local_logger.info(f'Execute emitterChainId:{emitterChainId}, sequence:{sequence}...')
        if not is_admin:
            try:
                result = package["so_diamond::complete_so_swap_by_account"](
                    hex_str_to_vector_u8(vaa_str),
                    ty_args=ty_args,
                    gas_unit_price=dst_max_gas_price
                )
            except Exception as e:
                if time.time() > vaa_data[1] + 60 * 60:
                    local_logger.error(f'Complete so swap for emitterChainId:{emitterChainId}, '
                                       f'sequence:{sequence}, start compensate for error: {e}')
                    result = package["wormhole_facet::complete_so_swap_by_relayer"](
                        hex_str_to_vector_u8(vaa_str),
                        ty_args=ty_args,
                        gas_unit_price=dst_max_gas_price
                    )
                else:
                    raise e
        else:
            receiver = wormhole_data[2][1]
            local_logger.info(f"Compensate to:{receiver}")
            result = package["wormhole_facet::complete_so_swap_by_admin"](
                hex_str_to_vector_u8(vaa_str),
                str(receiver),
                ty_args=ty_args,
                gas_unit_price=dst_max_gas_price
            )
        if "response" in result and "gas_used" in result["response"]:
            record_gas(
                int(dst_max_gas),
                int(dst_max_gas_price),
                int(result["response"]["gas_used"]),
                int(result["gas_unit_price"]),
                src_net=WORMHOLE_CHAINID_TO_NET[vaa_data["emitterChainId"]]
                if int(vaa_data["emitterChainId"]) in WORMHOLE_CHAINID_TO_NET else 0,
                dst_net=package.network,
                payload_len=int(len(vaa_str) / 2 - 1),
                swap_len=len(wormhole_data[3]),
                sequence=sequence,
                dst_txid=result["hash"]
            )
    except Exception as e:
        local_logger.error(f'Complete so swap for emitterChainId:{emitterChainId}, '
                           f'sequence:{sequence} error: {e}')
        return False
    local_logger.info(f'Process emitterChainId:{emitterChainId}, sequence:{sequence} success!')
    return True


def process_v1(
        dstWormholeChainId: int = 22,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[v1|{package.network}]")
    local_logger.info("Starting process v1...")
    has_process = {}
    if "test" in package.network or "test" == "goerli":
        url = "http://wormhole-testnet.sherpax.io"
    else:
        url = "http://wormhole-vaa.chainx.org"
    while True:
        result = get_signed_vaa_by_to(dstWormholeChainId, url=url)
        result = [d for d in result if (int(d["emitterChainId"]), int(d["sequence"])) not in has_process]
        local_logger.info(f"Get signed vaa by to length: {len(result)}")
        for d in result[::-1]:
            has_process[(int(d["emitterChainId"]), int(d["sequence"]))] = True
            process_vaa(
                dstSoDiamond,
                d["hexString"],
                d["emitterChainId"],
                d["sequence"],
                local_logger,
                inner_interval=10 * 60
            )
        time.sleep(60)


def process_v2(
        dstWormholeChainId: int = 22,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[v2|{package.network}]")
    local_logger.info("Starting process v2...")
    if "test" in package.network or "test" == "goerli":
        url = "http://wormhole-testnet.sherpax.io"
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    else:
        url = "http://wormhole-vaa.chainx.org"
        pending_url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    while True:
        pending_data = get_pending_data(url=pending_url)
        local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        for d in pending_data:
            try:
                vaa = get_signed_vaa(int(d["sequence"]), int(d["srcWormholeChainId"]), url=url)
                if vaa is None:
                    continue
                if vaa.get("toChain", -1) is not None and int(vaa.get("toChain", -1)) != dstWormholeChainId:
                    continue
                vaa = vaa["hexString"]
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            process_vaa(
                dstSoDiamond,
                vaa,
                d["srcWormholeChainId"],
                d["sequence"],
                local_logger,
                over_interval=10 * 60,
            )
        time.sleep(3 * 60)


def compensate(
        sequences: list,
        dstWormholeChainId: int = 22,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[v2|{package.network}]")
    local_logger.info("Starting process v2...")
    if "test" in package.network or "test" == "goerli":
        url = "http://wormhole-testnet.sherpax.io"
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    else:
        url = "http://wormhole-vaa.chainx.org"
        pending_url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    while True:
        pending_data = get_pending_data(url=pending_url)
        local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        for d in pending_data:
            try:
                vaa = get_signed_vaa(int(d["sequence"]), int(d["srcWormholeChainId"]), url=url)
                if vaa is None:
                    continue
                if int(vaa.get("toChain", -1)) != dstWormholeChainId:
                    continue
                if int(d["sequence"]) not in sequences:
                    continue
                vaa = vaa["hexString"]
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            process_vaa(
                dstSoDiamond,
                vaa,
                d["srcWormholeChainId"],
                d["sequence"],
                local_logger,
                over_interval=10 * 60,
                is_admin=True
            )
        time.sleep(3 * 60)


def record_gas(
        sender_gas: int,
        sender_gas_price: int,
        actual_gas: int,
        actual_gas_price: int,
        src_net: str,
        dst_net: str,
        payload_len=0,
        swap_len=0,
        file_path=Path(__file__).parent.parent.parent.parent.joinpath("gas"),
        sequence=None,
        dst_txid=None
):
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if not file_path.exists():
        file_path.mkdir()
    interval = 7 * 24 * 60 * 60
    cur_timestamp = int(time.time())
    uid = int(cur_timestamp / interval) * interval
    period1 = str(datetime.fromtimestamp(uid))[:13]
    period2 = str(datetime.fromtimestamp(uid + interval))[:13]
    file_name = file_path.joinpath(f"{dst_net}_{period1}_{period2}_v1.csv")
    data = {
        "record_time": str(datetime.fromtimestamp(cur_timestamp))[:19],
        "src_net": src_net,
        "dst_net": dst_net,
        "sender_gas": sender_gas,
        "sender_gas_price": sender_gas_price,
        "sender_value": sender_gas * sender_gas_price,
        "actual_gas": actual_gas,
        "actual_gas_price": actual_gas_price,
        "actual_value": actual_gas * actual_gas_price,
        "payload_len": payload_len,
        "swap_len": swap_len,
        "sequence": sequence,
        "dst_txid": dst_txid
    }
    columns = sorted(list(data.keys()))
    data = pd.DataFrame([data])
    data = data[columns]
    if file_name.exists():
        data.to_csv(str(file_name), index=False, header=False, mode='a')
    else:
        data.to_csv(str(file_name), index=False, header=True, mode='w')


def main():
    print(f'SoDiamond:{package.network_config["SoDiamond"]}')
    t1 = threading.Thread(target=process_v1, args=(22, package.network_config["SoDiamond"]))
    t2 = threading.Thread(target=process_v2, args=(22, package.network_config["SoDiamond"]))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


def single_process():
    process_v2(22, package.network_config["SoDiamond"])
