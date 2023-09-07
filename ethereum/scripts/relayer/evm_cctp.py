from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import requests
import ccxt
import pandas as pd

from brownie import project, network, chain, web3, Contract
import threading

from brownie.network.transaction import TransactionReceipt
from retrying import retry

from scripts.helpful_scripts import get_account, change_network, get_cctp_message_transmitter, Process, \
    set_start_method, Queue, reconnect_random_rpc
from scripts.serde import get_cctp_facet

FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

SUPPORTED_EVM = [
    {
        "destinationDomain": 0,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "mainnet",
    },
    {
        "destinationDomain": 1,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "avax-main",
    },
    {
        "destinationDomain": 2,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "optimism-main",
    },
    {
        "destinationDomain": 3,
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "arbitrum-main",
    }
]

# SUPPORTED_EVM = [
#     {"destinationDomain": 1,
#      "dstSoDiamond": "0x7969921f69c612C3D93D0cea133a571ff84753D3",
#      "dstNet": "avax-test"
#      },
#     {"destinationDomain": 3,
#      "dstSoDiamond": "0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449",
#      "dstNet": "arbitrum-test"
#      },
# ]

DOMAIN_TO_NET = {
    v["destinationDomain"]: v["dstNet"]
    for v in SUPPORTED_EVM
}


@retry
def get_token_price():
    kucoin = ccxt.kucoin()
    result = {}
    for v in SUPPORTED_EVM:
        if v["dstNet"] in ["mainnet", "goerli", "arbitrum-main", "arbitrum-test", "optimism-main", "optimism-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("ETH/USDT")['close'])
        elif v["dstNet"] in ["bsc-main", "bsc-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("BNB/USDT")['close'])
        elif v["dstNet"] in ["polygon-main", "polygon-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("MATIC/USDT")['close'])
        elif v["dstNet"] in ["avax-main", "avax-test"]:
            result[v["destinationDomain"]] = float(kucoin.fetch_ticker("AVAX/USDT")['close'])
        else:
            raise ValueError(f"{v['dstNet']} not found")
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
        self.msgVersion = int(msgVersion) if msgVersion is not None else msgVersion
        self.msgSourceDomain = int(msgSourceDomain) if msgSourceDomain is not None else msgSourceDomain
        self.msgDestinationDomain = int(msgDestinationDomain) if msgDestinationDomain \
                                                                 is not None else msgDestinationDomain
        self.msgNonce = int(msgNonce) if msgNonce is not None else msgNonce
        self.msgSender = str(format_hex(msgSender.hex()[-40:])) if msgSender is not None else msgSender
        self.msgRecipient = str(format_hex(msgRecipient.hex()[-40:])) if msgRecipient is not None else msgRecipient
        self.msgDestinationCaller = str(format_hex(msgDestinationCaller.hex()[-40:])) \
            if msgDestinationCaller is not None else msgDestinationCaller
        self.msgRawBody = str(format_hex(msgRawBody.hex())) if msgRawBody is not None else msgRawBody
        self.message = None
        self.msgHash = None
        self.attestation = None

    def to_dict(self):
        result = {}
        for attr in vars(self):
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


def is_hex(data: str):
    if str(data[:2]) != "0x":
        data = "0x" + str(data)
    if len(data) % 2 != 0:
        return False
    try:
        web3.toInt(hexstr=data)
        return True
    except:
        return False


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
        attestation = result.json()['attestation']
        if not is_hex(attestation):
            logger.warning(f"Get cctp attestation: {attestation}")
            attestation = None
        return attestation
    else:
        logger.warning(f"Get cctp attestation failed: {result.json()['status']}")
        return None


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
        cctp_message.message = format_hex(message)
        cctp_message.msgHash = format_hex(msg_hash.hex())
        cctp_message.attestation = format_hex(get_cctp_attestation(cctp_message.msgHash))
        messages.append(cctp_message)
    result = CCTPFacetMessage()
    result.src_txid = tx_hash
    if len(messages) > 0:
        result.token_message = messages[0]
    if len(messages) > 1:
        result.payload_message = messages[1]
    relay_event = events.get("RelayEvent", {})
    if len(relay_event) > 0:
        result.transactionId = format_hex(str(relay_event["transactionId"].hex()))
        result.fee = relay_event["fee"]
    else:
        logger.warning("Not found relay event")
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


def clear_queue(q: Queue):
    while not q.empty():
        try:
            q.get_nowait()
        except:
            break


def process_v1(
        _destinationDomain: int,
        _dstSoDiamond: str,
        dst_storage: Dict[int, Queue],
):
    """
    Used to get the message and send it to the corresponding consumer
    """
    local_logger = logger.getChild(f"[v1|{network.show_active()}]")
    local_logger.info("Starting process v1...")
    src_chain_id = chain.id

    last_process = {}
    interval = 30

    last_update_endpoint = 0
    endpoint_interval = 300

    while True:
        result = get_pending_data(src_chain_id=src_chain_id)
        local_logger.info(f"Get pending data len:{len(result)}")
        try:
            if time.time() > last_update_endpoint + endpoint_interval:
                reconnect_random_rpc()
                last_update_endpoint = time.time()

            for v in result:
                if v["extrinsicHash"] in last_process and (time.time() - last_process[v["extrinsicHash"]]) < interval:
                    continue
                last_process[v["extrinsicHash"]] = time.time()
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

                dst_domain = data.token_message.msgDestinationDomain
                dst_net = DOMAIN_TO_NET[dst_domain]

                if dst_storage[dst_domain].qsize() > 30:
                    # Avoid mem leak
                    clear_queue(dst_storage[dst_domain])

                dst_storage[dst_domain].put(data.to_dict())
                local_logger.info(f"Put {dst_net} item for txid: {data.src_txid}")
        except:
            import traceback
            err = traceback.format_exc()
            local_logger.error(f"Get error:{err}")

        time.sleep(3)


def format_hex(data):
    data = str(data)
    if not is_hex(data):
        return None
    if "0x" != data[:2]:
        data = f"0x{data}"
    data = data.lower()
    return data


def process_v2(
        destinationDomain: int,
        dstSoDiamond: str,
        dst_storage: Dict[int, Queue],
        is_compensate
):
    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}, acc:{get_account().address}")
    cctp_facet = get_cctp_facet()
    account = get_account()
    local_logger.info("Get token price")
    price_info = get_token_price()
    last_price_update = time.time()
    while True:
        local_logger.info("Get item from queue")
        data = None
        try:
            try:
                data = dst_storage[destinationDomain].get()
            except Exception as e:
                local_logger.warning(f"Get item fail:{e}, wait...")
                continue
            data = CCTPFacetMessage.from_dict(data)
            if format_hex(data.payload_message.msgRecipient) != format_hex(dstSoDiamond):
                local_logger.warning(f"Payload message recipient {data.payload_message.msgRecipient} not "
                                     f"equal dstSoDiamond {dstSoDiamond}")
                continue
            if time.time() - last_price_update >= 0:
                local_logger.info("Get token price")
                price_info = get_token_price()
                last_price_update = time.time()

            src_domain = data.token_message.msgSourceDomain
            dst_domain = data.token_message.msgDestinationDomain
            src_fee = data.fee if data.fee is not None else 0
            src_price = price_info[src_domain]
            dst_price = price_info[dst_domain]
            dst_fee = src_fee * src_price / dst_price
            gas_price = web3.eth.gas_price
            gas_limit = int(dst_fee / gas_price)
            if data.fee is None:
                gas_limit = None
            elif gas_limit == 0:
                logger.warning(f"Gas fee:{src_fee}, gas limit is zero, refuse relay")
                continue
            else:
                logger.info(f"Gas limit is {gas_limit} for transaction")
            if not is_compensate:
                result: TransactionReceipt = cctp_facet.receiveCCTPMessage(
                    format_hex(data.token_message.message),
                    format_hex(data.token_message.attestation),
                    format_hex(data.payload_message.message),
                    format_hex(data.payload_message.attestation),
                    {"from": account,
                     "gas_limit": gas_limit
                     }
                )
            else:
                result: TransactionReceipt = cctp_facet.receiveCCTPMessageByOwner(
                    format_hex(data.token_message.message),
                    format_hex(data.token_message.attestation),
                    {"from": account
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
        except:
            import traceback
            err = traceback.format_exc()
            local_logger.error(f"Src txid:{getattr(data, '', None)}, get error:{err}")


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
            dst_storage=None,
            is_compensate=False
    ):
        self.destinationDomain = destinationDomain
        self.dstSoDiamond = dstSoDiamond
        self.dstNet = dstNet
        self.project_path = project_path
        self.is_compensate = is_compensate
        super().__init__(
            group=group, target=self.worker, name=name, args=(dst_storage,), daemon=daemon
        )
        logger.info(f"Start {self.dstNet}")
        self.start()
        time.sleep(10)

    def worker(
            self,
            dst_storage
    ):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        try:
            change_network(self.dstNet)
        except:
            logger.error(f"Connect {self.dstNet} fail")
            return
        t1 = threading.Thread(
            target=process_v1, args=(self.destinationDomain, self.dstSoDiamond, dst_storage)
        )
        t2 = threading.Thread(
            target=process_v2, args=(self.destinationDomain, self.dstSoDiamond, dst_storage, self.is_compensate)
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
    try:
        set_start_method("spawn")
        logger.info("Set start method spawn")
    except:
        logger.warning("Set start method spawn fail")
    dst_storage = {
        v["destinationDomain"]: Queue()
        for v in SUPPORTED_EVM
    }

    project_path = Path(__file__).parent.parent.parent
    logger.info(f"Loading project...")
    for d in SUPPORTED_EVM:
        Session(
            destinationDomain=d["destinationDomain"],
            dstSoDiamond=d["dstSoDiamond"],
            dstNet=d["dstNet"],
            name=d["dstNet"],
            project_path=str(project_path),
            dst_storage=dst_storage,
            is_compensate=False
        )


def compensate(src_net="arbitrum-test", dst_net="avax-test"):
    tx_hash = "0x378f7a6e6afc6ede3dfed2baefce700eb23041389b76e2b563ed25e4080616ec"
    project_path = Path(__file__).parent.parent.parent
    name = dst_net
    p = project.load(project_path, name=name)
    p.load_config()
    change_network(src_net)
    logger.info(f"Change net into {network.show_active()}")
    message = get_facet_message(tx_hash=tx_hash)
    logger.info(f"Get message success")
    try:
        change_network(dst_net)
    except:
        network.connect(dst_net)
    logger.info(f"Change net into {network.show_active()}")

    cctp = get_cctp_facet()
    cctp.receiveCCTPMessageByOwner(
        message.token_message.message,
        message.token_message.attestation,
        {"from": get_account()}
    )


if __name__ == "__main__":
    main()
