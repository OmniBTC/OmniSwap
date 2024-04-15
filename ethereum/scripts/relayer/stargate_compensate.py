# @Time    : 2022/11/30 15:34
# @Author  : WeiDai
# @FileName: stargate_compensate.py
import functools
import hashlib
import json
import logging
import time
import traceback
from collections import OrderedDict
from datetime import datetime
from multiprocessing import Process, set_start_method, Queue
from pathlib import Path

import pandas as pd
import requests
from brownie import project, network, chain, web3
import threading

from brownie.network.transaction import TransactionReceipt

from scripts.helpful_scripts import get_account, change_network, reconnect_random_rpc, zero_address
from scripts.serde import get_stargate_facet, get_stargate_helper_facet
from web3._utils.events import get_event_data

FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

SUPPORTED_EVM = [
    {"dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820", "dstChainId": 1, "dstNet": "mainnet"},
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "bsc-main",
        "dstChainId": 56
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "polygon-main",
        "dstChainId": 137
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "avax-main",
        "dstChainId": 43114
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "arbitrum-main",
        "dstChainId": 42161
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "optimism-main",
        "dstChainId": 10
    },
    {
        "dstSoDiamond": "0xfDa613cb7366b1812F2d33fC95D1d4DD3896aeb8",
        "dstNet": "base-main",
        "dstChainId": 8453
    },
    {
        "dstSoDiamond": "0x0B77E63db1cd9F4f7cdAfb4a1C39f6ABEB764B66",
        "dstNet": "metis-main",
        "dstChainId": 1088
    },
    {
        "dstSoDiamond": "0x0B77E63db1cd9F4f7cdAfb4a1C39f6ABEB764B66",
        "dstNet": "mantle-main",
        "dstChainId": 5000
    },
{
        "dstSoDiamond": "0x6e166933CACB57b40f5C5D1a2D275aD997A7D318",
        "dstNet": "linea-main",
        "dstChainId": 59144
    },
]


def get_stargate_pending_data(url: str = None) -> list:
    """
    Get data for pending relayer
    :return: list
        {"data":[
        {"srcTransactionId":"0x3699e57b13369133701148e2b9a14ef143ac06270e2f51b15eac37002345642a",
        "dstTransactionId":"0x6ef714d2c38a201db45c2b4614c955e802d132378ef1dfcf0e17c04035d01e9d",
        "srcNet":"binance",
        "dstNet":"arbitrum",
        "srcChainId":56,
        "dstChainId":42161}]}
    """
    if url is None:
        url = "https://crossswap-pre.coming.chat/v1/getUnhandleStargateTransfer"
    try:
        response = requests.get(url)
        result = response.json()["data"]
        if isinstance(result, list):
            return result
        else:
            return []
    except:
        return []


def read_json(file) -> dict:
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}


def write_json(file, data: dict):
    with open(file, "w") as f:
        return json.dump(data, f, indent=1, separators=(",", ":"))


class RWDict(OrderedDict):
    def __init__(self, file, *args, **kwargs):
        file_path = Path(__file__).parent.joinpath("gas")
        if not file_path.exists():
            file_path.mkdir()
        file_file = file_path.joinpath(file)
        self.file = file_file
        super(RWDict, self).__init__(*args, **kwargs)
        self.read_data()

    def read_data(self):
        data = read_json(self.file)
        for k in data:
            self[k] = data[k]

    def __setitem__(self, key, value):
        super(RWDict, self).__setitem__(key, value)
        write_json(self.file, self)


HAS_PROCESSED = RWDict("processed_stargate.json")


def process_v1(
        dstSoDiamond: str,
        dst_storage,
):
    local_logger = logger.getChild(f"[v1|{network.show_active()}]")
    local_logger.info("Starting process v1...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}")
    if "test" in network.show_active() or "test" == "goerli":
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnhandleStargateTransfer"
    else:
        pending_url = "https://crossswap.coming.chat/v1/getUnhandleStargateTransfer"

    src_chain_id = None

    last_update_endpoint = 0
    endpoint_interval = 30
    last_pending_time = 0
    pending_interval = 30

    while True:
        try:
            if time.time() > last_update_endpoint + endpoint_interval:
                reconnect_random_rpc()
                local_logger.info(f"Update rpc")
                last_update_endpoint = time.time()

            if src_chain_id is None:
                src_chain_id = chain.id

            if time.time() < last_pending_time + pending_interval:
                continue
            else:
                last_pending_time = time.time()

            pending_data = get_stargate_pending_data(url=pending_url)
            pending_data = [
                d for d in pending_data if int(d["srcChainId"]) == int(src_chain_id)
            ]
            local_logger.info(f"Get length: {len(pending_data)}")
        except:
            traceback.print_exc()
            continue

        for d in pending_data:
            try:
                proxy_diamond = get_stargate_facet()
                tx = chain.get_transaction(d["srcTransactionId"])
                dstGas = int(proxy_diamond.decode_input(tx.input)[-1][-2][-2])
                if dstGas < 160000:
                    local_logger.warning(f"{d['srcTransactionId']} not enough dst gas:{dstGas}!")
                else:
                    local_logger.warning(f"Put {d['srcTransactionId']} into queue!")
                    dst_storage[int(d['dstChainId'])].put(d)
            except:
                traceback.print_exc()
                continue
        time.sleep(3 * 60)


@functools.lru_cache()
def get_event_abi_by_interface(interface_name, event_name):
    p = project.get_loaded_projects()[-1]
    for v in getattr(p.interface, interface_name).abi:
        if v["type"] == "event" and v["name"] == event_name:
            return v
    return None


@functools.lru_cache()
def get_event_abi_by_contract(contract_name, event_name):
    p = project.get_loaded_projects()[-1]
    for v in getattr(p, contract_name).abi:
        if v["type"] == "event" and v["name"] == event_name:
            return v
    return None


def process_v2(
        dstSoDiamond: str,
        dst_storage,
):
    account = get_account()

    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}")

    src_chain_id = None
    last_update_endpoint = 0
    endpoint_interval = 30

    stargate_helper = None
    proxy_diamond = None

    while True:
        try:
            if stargate_helper is None:
                stargate_helper = get_stargate_helper_facet()
            if proxy_diamond is None:
                proxy_diamond = get_stargate_facet()
            if time.time() > last_update_endpoint + endpoint_interval:
                reconnect_random_rpc()
                local_logger.info(f"Update rpc")
                last_update_endpoint = time.time()

            if src_chain_id is None:
                src_chain_id = chain.id

            d = dst_storage[src_chain_id].get()

            tx = chain.get_transaction(d["dstTransactionId"])

            (_, payload) = stargate_helper.tryFindStargatePayload(
                tx.input,
                proxy_diamond.address
            )

            if len(payload) == 0:
                local_logger.warning(f"{d['srcTransactionId']}, Payload not found")
                continue

            receipt = web3.eth.get_transaction_receipt(d["dstTransactionId"])
            logs = receipt["logs"]
            message_abi = get_event_abi_by_interface("IStargate", "CachedSwapSaved")
            transfer_abi = get_event_abi_by_interface("IERC20", "Transfer")
            transfer_native_abi = get_event_abi_by_interface("IStargateEthVault", "TransferNative")
            events = {"CachedSwapSaved": {}, "Transfer": {}}

            for log in logs:
                try:
                    data = get_event_data(web3.codec, message_abi, log)
                    events["CachedSwapSaved"] = data
                except:
                    pass
                try:
                    data = get_event_data(web3.codec, transfer_abi, log)
                    if str(data["args"]["to"]).lower() == str(proxy_diamond.address).lower():
                        events["Transfer"] = data
                except:
                    pass
                try:
                    data = get_event_data(web3.codec, transfer_native_abi, log)
                    if str(data["args"]["dst"]).lower() == str(proxy_diamond.address).lower():
                        events["Transfer"] = data
                        events["Transfer"]["address"] = zero_address()
                except:
                    pass

            if len(events["CachedSwapSaved"]) == 0:
                local_logger.warning(f"{d['srcTransactionId']}, CachedSwapSaved not found")
                continue

            if len(events["Transfer"]) == 0:
                local_logger.warning(f"{d['srcTransactionId']}, Transfer not found")
                continue
            info = {
                "chainId": events["CachedSwapSaved"]["args"]["chainId"],
                "srcAddress": events["CachedSwapSaved"]["args"]["srcAddress"],
                "nonce": events["CachedSwapSaved"]["args"]["nonce"],
                "token": events["Transfer"]["address"],
                "amountLD": events["Transfer"]["args"]["value"] if "value" in events["Transfer"]["args"]
                else events["Transfer"]["args"]["wad"],
                "payload": payload
            }

            dv = (
                f'{info["chainId"]}|{info["srcAddress"]}|{info["nonce"]}|'
                f'{info["token"]}|{info["amountLD"]}|{info["payload"]}'
            )
            dk = str(hashlib.sha3_256(dv.encode()).digest().hex())
            if dk in HAS_PROCESSED:
                local_logger.warning(f"{d['srcTransactionId']}, HAS PROCESSED")
                continue
            local_logger.info(f"Process {d['srcTransactionId']}")
            result: TransactionReceipt = proxy_diamond.sgReceive(
                info["chainId"],
                info["srcAddress"],
                info["nonce"],
                info["token"],
                info["amountLD"],
                info["payload"],
                {"from": account},
            )
            record_gas(
                d["srcTransactionId"],
                d["dstTransactionId"],
                result.txid,
                result.gas_used,
                result.gas_price,
                d["srcNet"],
                dst_net=network.show_active(),
            )
            HAS_PROCESSED[dk] = dv
        except:
            traceback.print_exc()
            continue
        time.sleep(3 * 60)


class Session(Process):
    def __init__(
            self,
            dstSoDiamond: str,
            dstNet: str,
            project_path: str,
            dst_storage: dict,
            group=None,
            name=None,
            daemon=None,
    ):
        self.dstSoDiamond = dstSoDiamond
        self.dstNet = dstNet
        self.project_path = project_path
        super().__init__(
            group=group, target=self.worker, name=name, args=(dst_storage,), daemon=daemon
        )
        self.start()
        time.sleep(10)

    def worker(self, dst_storage):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        try:
            change_network(self.dstNet)
        except:
            logger.error(f"Connect {self.dstNet} fail")
            return
        t1 = threading.Thread(
            target=process_v1, args=(self.dstSoDiamond, dst_storage)
        )
        t1.start()
        t2 = threading.Thread(target=process_v2, args=(self.dstSoDiamond, dst_storage))
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
        src_transaction: str,
        dst_transaction1: str,
        dst_transaction2: str,
        actual_gas: int,
        actual_gas_price: int,
        src_net: str,
        dst_net: str,
        file_path=Path(__file__).parent.parent.parent.parent.joinpath("gas"),
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
    file_name = file_path.joinpath(f"stargate_{dst_net}_{period1}_{period2}.csv")
    data = OrderedDict({
        "record_time": str(datetime.fromtimestamp(cur_timestamp))[:19],
        "src_transaction": src_transaction,
        "dst_transaction1": dst_transaction1,
        "dst_transaction2": dst_transaction2,
        "src_net": src_net,
        "dst_net": dst_net,
        "actual_gas": actual_gas,
        "actual_gas_price": actual_gas_price,
        "actual_value": actual_gas * actual_gas_price,
    })
    columns = list(data.keys())
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
    dst_storage = {
        v["dstChainId"]: Queue()
        for v in SUPPORTED_EVM
    }
    for d in SUPPORTED_EVM:
        Session(
            dstSoDiamond=d["dstSoDiamond"],
            dstNet=d["dstNet"],
            name=d["dstNet"],
            dst_storage=dst_storage,
            project_path=str(project_path),
        )


if __name__ == "__main__":
    main()
