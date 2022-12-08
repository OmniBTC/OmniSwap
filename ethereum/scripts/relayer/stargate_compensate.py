# @Time    : 2022/11/30 15:34
# @Author  : WeiDai
# @FileName: stargate_compensate.py
import hashlib
import json
import logging
import time
import traceback
from collections import OrderedDict
from datetime import datetime
from multiprocessing import Process, set_start_method
from pathlib import Path

import pandas as pd
import requests
from brownie import project, network, chain
import threading

from brownie.network.transaction import TransactionReceipt

from scripts.helpful_scripts import get_account, change_network
from scripts.serde import get_stargate_facet

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

SUPPORTED_EVM = [
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "mainnet"
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "bsc-main"
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "polygon-main"
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "avax-main"
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "arbitrum-main"
    },
    {
        "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "dstNet": "optimism-main"
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
        return json.dump(data, f, indent=1, separators=(',', ':'))


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


def process_v2(
        dstSoDiamond: str,
):
    account = get_account()

    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f'SoDiamond:{dstSoDiamond}')
    if "test" in network.show_active() or "test" == "goerli":
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnhandleStargateTransfer"
    else:
        pending_url = "https://crossswap.coming.chat/v1/getUnhandleStargateTransfer"
    while True:
        pending_data = get_stargate_pending_data(url=pending_url)
        pending_data = [d for d in pending_data if int(d["dstChainId"]) == int(chain.id)]
        local_logger.info(f"Get length: {len(pending_data)}")
        for d in pending_data:
            try:
                tx = chain.get_transaction(d["dstTransactionId"])
                info = tx.events["CachedSwapSaved"]
                dv = f'{info["chainId"]}|{info["srcAddress"]}|{info["nonce"]}|' \
                     f'{info["token"]}|{info["amountLD"]}|{info["payload"]}'
                dk = str(hashlib.sha3_256(dv.encode()).digest().hex())
                if dk in HAS_PROCESSED:
                    continue
                HAS_PROCESSED[dk] = dv
                proxy_diamond = get_stargate_facet()
                result: TransactionReceipt = proxy_diamond.sgReceive(
                    info["chainId"],
                    info["srcAddress"],
                    info["nonce"],
                    info["token"],
                    info["amountLD"],
                    info["payload"],
                    {"from": account}
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
            except:
                traceback.print_exc()
                continue
        time.sleep(3 * 60)


class Session(Process):
    def __init__(self,
                 dstSoDiamond: str,
                 dstNet: str,
                 project_path: str,
                 group=None,
                 name=None,
                 daemon=None
                 ):
        self.dstSoDiamond = dstSoDiamond
        self.dstNet = dstNet
        self.project_path = project_path
        super().__init__(
            group=group,
            target=self.worker,
            name=name,
            args=(),
            daemon=daemon)
        self.start()

    def worker(self):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        try:
            change_network(self.dstNet)
        except:
            logger.error(f"Connect {self.dstNet} fail")
            return
        t2 = threading.Thread(target=process_v2, args=(self.dstSoDiamond,))
        t2.start()
        while True:
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
    file_name = file_path.joinpath(f"stargate_{dst_net}_{period1}_{period2}.csv")
    data = {
        "record_time": str(datetime.fromtimestamp(cur_timestamp))[:19],
        "src_transaction": src_transaction,
        "dst_transaction1": dst_transaction1,
        "dst_transaction2": dst_transaction2,
        "src_net": src_net,
        "dst_net": dst_net,
        "actual_gas": actual_gas,
        "actual_gas_price": actual_gas_price,
        "actual_value": actual_gas * actual_gas_price,
    }
    columns = sorted(list(data.keys()))
    data = pd.DataFrame([data])
    data = data[columns]
    if file_name.exists():
        data.to_csv(str(file_name), index=False, header=False, mode='a')
    else:
        data.to_csv(str(file_name), index=False, header=True, mode='w')


def main():
    set_start_method("spawn")
    project_path = Path(__file__).parent.parent.parent
    logger.info(f"Loading project...")
    for d in SUPPORTED_EVM:
        Session(dstSoDiamond=d["dstSoDiamond"],
                dstNet=d["dstNet"],
                name=d["dstNet"],
                project_path=str(project_path)
                )


def single_process():
    process_v2(SUPPORTED_EVM[2]["dstSoDiamond"])
