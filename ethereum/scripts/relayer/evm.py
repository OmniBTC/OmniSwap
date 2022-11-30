import logging
import time
from datetime import datetime
from multiprocessing import Process, set_start_method
from pathlib import Path

import pandas as pd
from brownie import project, network, config
import threading

from scripts.helpful_scripts import get_account, change_network, padding_to_bytes
from scripts.relayer.select import get_pending_data, get_signed_vaa, get_signed_vaa_by_to
from scripts.serde import parse_vaa_to_wormhole_payload, get_wormhole_facet

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

SUPPORTED_EVM = [
    {"dstWormholeChainId": 2,
     "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
     "dstNet": "mainnet"
     },
    {"dstWormholeChainId": 4,
     "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
     "dstNet": "bsc-main"
     },
    {"dstWormholeChainId": 5,
     "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
     "dstNet": "polygon-main"
     },
    {"dstWormholeChainId": 6,
     "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
     "dstNet": "avax-main"
     },
]


# SUPPORTED_EVM = [
#     {"dstWormholeChainId": 4,
#      "dstSoDiamond": "0xFeEE07da1B3513BdfD5440562e962dfAac19566F",
#      "dstNet": "bsc-test"
#      },
#     {"dstWormholeChainId": 6,
#      "dstSoDiamond": "0xBb032459B39547908eDB8E690c030Dc4F31DA673",
#      "dstNet": "avax-test"
#      },
# ]


def process_vaa(
        dstSoDiamond: str,
        vaa_str: str,
        emitterChainId: str,
        sequence: str,
        local_logger,
        inner_interval: int = None,
        over_interval: int = None,
        WORMHOLE_CHAINID_TO_NET: dict = None,
        limit_gas_price=True
) -> bool:
    try:
        # Use bsc-test to decode, too slow may need to change bsc-mainnet
        vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(
            vaa_str)
        dst_max_gas = wormhole_data[1]
        dst_max_gas_price = int(wormhole_data[0])
        if "main" in network.show_active():
            assert dst_max_gas_price > 0, "dst_max_gas_price is 0"
        else:
            dst_max_gas_price = int(10 * 1e9) if dst_max_gas_price == 0 else dst_max_gas_price
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
        if limit_gas_price:
            result = get_wormhole_facet().completeSoSwap(
                vaa_str, {"from": get_account(),
                          "gas_price": dst_max_gas_price,
                          "required_confs": 0,
                          })
        else:
            result = get_wormhole_facet().completeSoSwap(
                vaa_str, {"from": get_account(), "required_confs": 0})
        local_logger.info(f'Execute emitterChainId:{emitterChainId}, sequence:{sequence}...')
        record_gas(
            dst_max_gas,
            dst_max_gas_price,
            result.gas_used,
            result.gas_price,
            src_net=WORMHOLE_CHAINID_TO_NET[vaa_data["emitterChainId"]]
            if int(vaa_data["emitterChainId"]) in WORMHOLE_CHAINID_TO_NET else 0,
            dst_net=network.show_active(),
            payload_len=int(len(vaa_str) / 2 - 1),
            swap_len=len(wormhole_data[3])
        )
    except Exception as e:
        local_logger.error(f'Complete so swap for emitterChainId:{emitterChainId}, '
                           f'sequence:{sequence} error: {e}')
        return False
    local_logger.info(f'Process emitterChainId:{emitterChainId}, sequence:{sequence} success!')
    return True


def process_v1(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    WORMHOLE_CHAINID_TO_NET = {
        config["networks"][net]["wormhole"]["chainid"]: net
        for net in config["networks"]
        if "wormhole" in config["networks"][net]
           and "chainid" in config["networks"][net]["wormhole"]
        if ("main" in list(SUPPORTED_EVM)[0]["dstNet"] and "main" in net)
           or ("main" not in list(SUPPORTED_EVM)[0]["dstNet"] and "main" not in net)
    }
    local_logger = logger.getChild(f"[v1|{network.show_active()}]")
    local_logger.info("Starting process v1...")
    local_logger.info(f'SoDiamond:{dstSoDiamond}')
    has_process = {}
    if "test" in network.show_active() or "test" == "goerli":
        url = "http://wormhole-testnet.sherpax.io"
    else:
        url = "http://wormhole-vaa.chainx.org"
    while True:
        try:
            result = get_signed_vaa_by_to(dstWormholeChainId, url=url)
            result = [d for d in result if (
                int(d["emitterChainId"]), int(d["sequence"])) not in has_process]
        except Exception:
            continue
        local_logger.info(f"Get signed vaa by to length: {len(result)}")
        for d in result[::-1]:
            has_process[(int(d["emitterChainId"]), int(d["sequence"]))] = True
            process_vaa(
                dstSoDiamond,
                d["hexString"],
                d["emitterChainId"],
                d["sequence"],
                local_logger,
                inner_interval=30 * 60,
                WORMHOLE_CHAINID_TO_NET=WORMHOLE_CHAINID_TO_NET,
            )
        time.sleep(60)


def process_v2(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    WORMHOLE_CHAINID_TO_NET = {
        config["networks"][net]["wormhole"]["chainid"]: net
        for net in config["networks"]
        if "wormhole" in config["networks"][net]
           and "chainid" in config["networks"][net]["wormhole"]
        if ("main" in list(SUPPORTED_EVM)[0]["dstNet"] and "main" in net)
           or ("main" not in list(SUPPORTED_EVM)[0]["dstNet"] and "main" not in net)
    }
    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f'SoDiamond:{dstSoDiamond}')
    has_process = {}
    if "test" in network.show_active() or "test" == "goerli":
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
                vaa = get_signed_vaa(
                    int(d["sequence"]), int(d["srcWormholeChainId"]), url=url)
                if vaa is None:
                    continue
                if int(vaa.get("toChain", -1)) != dstWormholeChainId:
                    continue
                vaa = vaa["hexString"]
            except Exception as e:
                local_logger.error(f'Get signed vaa for: emitterChainId: {d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            try:
                if (time.time() - d["blockTimestamp"]) >= 60 * 60:
                    limit_gas_price = False
                else:
                    limit_gas_price = True
            except:
                limit_gas_price = True
            has_key = (int(d["srcWormholeChainId"]), int(d["sequence"]))
            if has_key in has_process and (time.time() - has_process[has_key]) <= 10 * 60:
                local_logger.warning(f'emitterChainId:{d["srcWormholeChainId"]} sequence:{d["sequence"]} '
                                     f'inner 10min has process!')
                continue
            else:
                has_process[has_key] = time.time()
            process_vaa(
                dstSoDiamond,
                vaa,
                d["srcWormholeChainId"],
                d["sequence"],
                local_logger,
                over_interval=10 * 60,
                WORMHOLE_CHAINID_TO_NET=WORMHOLE_CHAINID_TO_NET,
                limit_gas_price=limit_gas_price
            )
        time.sleep(2 * 60)


class Session(Process):
    def __init__(self,
                 dstWormholeChainId: int,
                 dstSoDiamond: str,
                 dstNet: str,
                 project_path: str,
                 group=None,
                 name=None,
                 daemon=None
                 ):
        self.dstWormholeChainId = dstWormholeChainId
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
        t1 = threading.Thread(target=process_v1, args=(
            self.dstWormholeChainId, self.dstSoDiamond))
        t2 = threading.Thread(target=process_v2, args=(
            self.dstWormholeChainId, self.dstSoDiamond))
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
        sender_gas: int,
        sender_gas_price: int,
        actual_gas: int,
        actual_gas_price: int,
        src_net: str,
        dst_net: str,
        payload_len=0,
        swap_len=0,
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
    file_name = file_path.joinpath(f"{dst_net}_{period1}_{period2}.csv")
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
        "swap_len": swap_len
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
        Session(dstWormholeChainId=d["dstWormholeChainId"],
                dstSoDiamond=d["dstSoDiamond"],
                dstNet=d["dstNet"],
                name=d["dstNet"],
                project_path=str(project_path)
                )


def single_process():
    process_v2(SUPPORTED_EVM[2]["dstWormholeChainId"], SUPPORTED_EVM[2]["dstSoDiamond"])
