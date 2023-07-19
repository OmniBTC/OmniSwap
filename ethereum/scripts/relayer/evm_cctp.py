from __future__ import annotations

import logging
import multiprocessing
import time
from datetime import datetime
from multiprocessing import Process, set_start_method
from pathlib import Path
from typing import Dict, List

import ccxt
import pandas as pd
import requests
from brownie import project, network, config, chain, web3, Contract
import threading

from brownie.network.transaction import TransactionReceipt
from retrying import retry

from scripts.helpful_scripts import get_account, change_network, get_cctp_message_transmitter
from scripts.serde import get_cctp_facet

FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

SUPPORTED_EVM = [
    {
        "destinationDomain": 1,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "avax-main",
    },
    {
        "destinationDomain": 3,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "arbitrum-main",
    }
]

# SUPPORTED_EVM = [
#     {"destinationDomain": 1,
#      "dstSoDiamond": "0xFeEE07da1B3513BdfD5440562e962dfAac19566F",
#      "dstNet": "avax-test"
#      },
#     {"destinationDomain": 3,
#      "dstSoDiamond": "0xBb032459B39547908eDB8E690c030Dc4F31DA673",
#      "dstNet": "arbitrum-test"
#      },
# ]

SHARE_STORAGE = {
    v["destinationDomain"]: multiprocessing.Queue()
    for v in SUPPORTED_EVM
}

DOMAIN_TO_NET = {
    v["destinationDomain"]: v["dstNet"]
    for v in SUPPORTED_EVM
}


@retry
def get_token_price():
    kucoin = ccxt.kucoin()
    result = {}
    for v in SUPPORTED_EVM:
        if v["dstNet"] in ["mainnet", "goerli"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("ETH/USDT")['close'])
        elif v["dstNet"] in ["bsc-main", "bsc-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("BNB/USDT")['close'])
        elif v["dstNet"] in ["polygon-main", "polygon-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("MATIC/USDT")['close'])
        elif v["dstNet"] in ["avax-main", "avax-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("AVAX/USDT")['close'])
    return result


class CCTPMessage:
    def __init__(
            self,
            msgVersion=None,
            msgSourceDomain=None,
            msgDestinationDomain=None,
            msgNonce=None,
            msgSender=None,
            msgRecipient=None,
            msgDestinationCaller=None,
            msgRawBody=None,
    ):
        self.msgVersion = msgVersion
        self.msgSourceDomain = msgSourceDomain,
        self.msgDestinationDomain = msgDestinationDomain,
        self.msgNonce = msgNonce,
        self.msgSender = msgSender,
        self.msgRecipient = msgRecipient,
        self.msgDestinationCaller = msgDestinationCaller,
        self.msgRawBody = msgRawBody,
        self.message = None
        self.msgHash = None
        self.attestation = None

    def to_dict(self):
        result = {}
        for attr in self.__dir__():
            if attr.startswith("__"):
                continue
            result[attr] = getattr(self, attr)
        return result

    @staticmethod
    def from_dict(data) -> CCTPMessage:
        result = CCTPMessage()
        for attr in data:
            setattr(result, attr, data[attr])
        return result


class CCTPFacetMessage:
    def __init__(self):
        self.token_message: CCTPMessage = None
        self.payload_message: CCTPMessage = None
        self.src_txid: str = None
        self.transactionId: str = None
        self.fee: int = None

    def to_dict(self):
        return {
            "token_message": self.token_message.to_dict(),
            "payload_message": self.payload_message.to_dict(),
            "src_txid": self.src_txid,
            "transactionId": self.transactionId,
            "fee": self.fee
        }

    @staticmethod
    def from_dict(data) -> CCTPFacetMessage:
        result = CCTPFacetMessage()
        result.token_message = CCTPMessage.from_dict(data["token_message"])
        result.payload_message = CCTPMessage.from_dict(data["payload_message"])
        result.src_txid = data["src_txid"]
        result.transactionId = data["transactionId"]
        result.fee = data["fee"]
        return result


@retry
def get_cctp_attestation(msg_hash):
    net = network.show_active()
    if 'test' in net:
        url = "https://iris-api-sandbox.circle.com/v1/attestations/"
    else:
        url = "https://iris-api.circle.com/v1/attestations/"

    url += msg_hash
    result = requests.get(url)
    if result.status_code == 200:
        return result.json()['attestation']
    else:
        raise ValueError(f"Get cctp attestation failed: {result.json()['status']}")


def get_facet_message(tx_hash) -> CCTPFacetMessage:
    p = project.get_loaded_projects()[-1]
    cctp_facet = get_cctp_facet()
    Contract.from_abi("MessageTransmitter",
                      get_cctp_message_transmitter(),
                      getattr(p.interface, "IMessageTransmitter").abi
                      )
    events = dict(chain.get_transaction(tx_hash).events)
    messages = []
    for event in events.get("MessageSent", []):
        message = event["message"].hex()
        msg_hash = web3.keccak(hexstr=message)
        cctp_message = CCTPMessage(*cctp_facet.decodeCCTPMessage(message))
        cctp_message.message = message
        cctp_message.msgHash = msg_hash.hex()
        cctp_message.attestation = get_cctp_attestation(cctp_message.msgHash)
    result = CCTPFacetMessage()
    result.src_txid = tx_hash
    if len(messages) > 0:
        result.token_message = messages[0]
    if len(messages) > 1:
        result.payload_message = messages[1]
    relay_event = events.get("RelayEvent", {})
    if len(relay_event) > 0:
        result.transactionId = relay_event["transactionId"].hex()
        result.fee = relay_event["fee"]
    return result


def get_pending_data(url: str = None, src_chain_id: int = None) -> list:
    """
    Get data for pending relayer
    :return: list
        [{'chainName': 'bsc-test',
        'extrinsicHash': '0x63942108e3e0b4ca70ba331acc1c7419ffc43ebcc10e75abe4b0c05a4ce2e2d5',
        'srcChainId': 0,
        "blockTimestamp": 1689644481
        }]
    """
    if url is None:
        url = "https://crossswap.coming.chat/v1/getUnSendTransferFromCCTP"
    try:
        response = requests.get(url)
        result = response.json()["record"]
        if isinstance(result, list):
            result = [v for v in result if v["srcChainId"] == src_chain_id]
            result.sort(key=lambda x: x["blockTimestamp"])
            return result
        else:
            return []
    except:
        return []


def process_v1(
        _destinationDomain: int,
        _dstSoDiamond: str,
        share_storage_v1: Dict[int, multiprocessing.Queue],
):
    """
    Used to get the message and send it to the corresponding consumer
    """
    local_logger = logger.getChild(f"[v1|{network.show_active()}]")
    local_logger.info("Starting process v1...")
    src_chain_id = chain.id

    while True:
        result = get_pending_data(src_chain_id=src_chain_id)
        local_logger.info(f"Get pending data len:{len(result)}")

        for v in result:
            data = get_facet_message(v["extrinsicHash"])
            if data.token_message is None:
                local_logger.warning(f"Get token message is None from {v['extrinsicHash']}")
                continue
            if data.token_message.attestation is None:
                local_logger.warning(f"Get token message attestation fail from {v['extrinsicHash']}")
                continue

            if data.payload_message is None:
                local_logger.warning(f"Get payload message is None from {v['extrinsicHash']}")
                continue
            if data.payload_message.attestation is None:
                local_logger.warning(f"Get payload message attestation fail from {v['extrinsicHash']}")
                continue

            share_storage_v1[data.token_message.msgDestinationDomain].put(data.to_dict())

        time.sleep(3)


def format_hex(data):
    if "0x" != data[:2]:
        data = f"0x{data}"
    data = data.lower()
    return data


def process_v2(
        destinationDomain: int,
        dstSoDiamond: str,
        share_storage_v1: Dict[int, multiprocessing.Queue],
):
    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}, acc:{get_account().address}")
    cctp_facet = get_cctp_facet()
    account = get_account()
    price_info = get_token_price()
    last_price_update = time.time()
    while True:
        local_logger.info("Get item from queue")
        try:
            data = share_storage_v1[destinationDomain].get(timeout=10)
            data = CCTPFacetMessage.from_dict(data)
        except Exception as e:
            local_logger.warning(f"Get item fail:{e}, wait...")
            continue
        if format_hex(data.payload_message.msgRecipient) != format_hex(dstSoDiamond):
            local_logger.warning(f"Payload message recipient {data.payload_message.msgRecipient} not "
                                 f"equal dstSoDiamond {dstSoDiamond}")
            continue
        if time.time() - last_price_update >= 0:
            price_info = get_token_price()
            last_price_update = time.time()

        src_domain = data.token_message.msgSourceDomain
        dst_domain = data.token_message.msgDestinationDomain
        src_fee = data.fee
        src_price = price_info[src_domain]
        dst_price = price_info[dst_domain]
        dst_fee = src_fee * src_price / dst_price
        gas_price = web3.eth.gas_price
        gas_limit = dst_fee / gas_price
        result: TransactionReceipt = cctp_facet.receiveCCTPMessage(
            format_hex(data.token_message.message),
            format_hex(data.token_message.attestation),
            format_hex(data.payload_message.message),
            format_hex(data.payload_message.attestation),
            {"from": account,
             "gas_limit": gas_limit
             }
        )
        record_gas(
            result.gas_used,
            result.gas_price,
            src_net=DOMAIN_TO_NET[src_domain],
            dst_net=DOMAIN_TO_NET[dst_domain],
            src_txid=data.src_txid,
            dst_txid=result.txid,
        )
        local_logger.info(
            f"Process src txid:{data.src_txid}, dst txid: {result.txid}"
            f" success!"
        )


class Session(Process):
    def __init__(
            self,
            destinationDomain: int,
            dstSoDiamond: str,
            dstNet: str,
            project_path: str,
            group=None,
            name=None,
            daemon=None,
    ):
        self.destinationDomain = destinationDomain
        self.dstSoDiamond = dstSoDiamond
        self.dstNet = dstNet
        self.project_path = project_path
        super().__init__(
            group=group, target=self.worker, name=name, args=(SHARE_STORAGE,), daemon=daemon
        )
        self.start()

    def worker(self,
               share_storage_v1: Dict[int, multiprocessing.Queue],
               ):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        try:
            change_network(self.dstNet)
        except:
            logger.error(f"Connect {self.dstNet} fail")
            return
        t1 = threading.Thread(
            target=process_v1, args=(self.destinationDomain, self.dstSoDiamond, share_storage_v1)
        )
        t2 = threading.Thread(
            target=process_v2, args=(self.destinationDomain, self.dstSoDiamond, share_storage_v1)
        )
        t1.start()
        t2.start()
        while True:
            if not t1.is_alive():
                if not network.is_connected():
                    change_network(self.dstNet)
                t1.start()
            if not t2.is_alive():
                if not network.is_connected():
                    change_network(self.dstNet)
                t2.start()
            time.sleep(10 * 60 * 60)


def record_gas(
        gas: int,
        gas_price: int,
        src_net: str,
        dst_net: str,
        src_txid=None,
        dst_txid=None,
        file_path=Path(__file__).parent.joinpath("gas"),
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
    file_name = file_path.joinpath(f"cctp_{dst_net}_{period1}_{period2}.csv")
    data = {
        "record_time": str(datetime.fromtimestamp(cur_timestamp))[:19],
        "src_net": src_net,
        "dst_net": dst_net,
        "gas": gas,
        "gas_price": gas_price,
        "sender_value": gas * gas_price,
        "src_txid": src_txid,
        "dst_txid": dst_txid,
    }
    columns = sorted(list(data.keys()))
    data = pd.DataFrame([data])
    data = data[columns]
    if file_name.exists():
        data.to_csv(str(file_name), index=False, header=False, mode="a")
    else:
        data.to_csv(str(file_name), index=False, header=True, mode="w")


def main():
    set_start_method("spawn")
    project_path = Path(__file__).parent.parent.parent
    logger.info(f"Loading project...")
    for d in SUPPORTED_EVM:
        Session(
            destinationDomain=d["destinationDomain"],
            dstSoDiamond=d["dstSoDiamond"],
            dstNet=d["dstNet"],
            name=d["dstNet"],
            project_path=str(project_path),
        )
