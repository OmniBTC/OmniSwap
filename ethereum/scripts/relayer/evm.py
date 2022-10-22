import logging
import time
from multiprocessing import Process, set_start_method
from pathlib import Path

from brownie import project, network
import threading

from scripts.helpful_scripts import get_account, change_network
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
#      "dstSoDiamond": "0xEe05F9e2651EBC5dbC66aD54241C6AB24E361228",
#      "dstNet": "bsc-test"
#      },
#     {"dstWormholeChainId": 5,
#      "dstSoDiamond": "0xBae5BeAdBaa65628eA9DC5A5c7F794b4865c8771",
#      "dstNet": "polygon-test"
#      },
#     {"dstWormholeChainId": 6,
#      "dstSoDiamond": "0x802e05b91769342af3F0d13f9DC6Df03a54C2ac7",
#      "dstNet": "avax-test"
#      },
# ]


def process_v1(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    local_logger = logger.getChild(f"[{network.show_active()}]")
    local_logger.info("Starting process v1...")
    has_process = {}
    while True:
        try:
            result = get_signed_vaa_by_to(dstWormholeChainId, url="http://wormhole-vaa.chainx.org")
            result = [d for d in result if (
                int(d["emitterChainId"]), int(d["sequence"])) not in has_process]
        except Exception:
            continue
        local_logger.info(f"Get signed vaa by to length: {len(result)}")
        for d in result[::-1]:
            has_process[(int(d["emitterChainId"]), int(d["sequence"]))] = True

            try:
                # Use bsc-test to decode, too slow may need to change bsc-mainnet
                vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(
                    d["hexString"])
            except Exception as e:
                local_logger.error(f'Parse signed vaa for emitterChainId:{d["emitterChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            if time.time() > int(vaa_data[1]) + 5 * 60:
                local_logger.warning(
                    f'For emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} '
                    f'beyond 5min')
                continue
            if transfer_data[4] != dstSoDiamond:
                local_logger.warning(
                    f'For emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} dstSoDiamond: {dstSoDiamond} '
                    f'not match: {transfer_data[4]}')
                continue
            try:
                get_wormhole_facet().completeSoSwap(
                    d["hexString"], {"from": get_account()})
            except Exception as e:
                local_logger.error(f'Complete so swap for emitterChainId:{d["emitterChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            logger.info(f'Process emitterChainId:{d["emitterChainId"]}, sequence:{d["sequence"]} success!')

        time.sleep(60)


def process_v2(
        _dstWormholeChainId: int,
        dstSoDiamond: str,
):
    local_logger = logger.getChild(f"[{network.show_active()}]")
    local_logger.info("Starting process v2...")
    has_process = {}
    while True:
        pending_data = get_pending_data()
        pending_data = [d for d in pending_data if
                        (int(d["srcWormholeChainId"]), int(d["sequence"])) not in has_process]
        local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        for d in pending_data:
            has_process[(int(d["srcWormholeChainId"]),
                         int(d["sequence"]))] = True
            try:
                vaa = get_signed_vaa(
                    int(d["sequence"]), int(d["srcWormholeChainId"]), url="http://wormhole-vaa.chainx.org")
                if vaa is None:
                    continue
                vaa = vaa["hexString"]
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            try:
                # Use bsc-test to decode, too slow may need to change bsc-mainnet
                vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(
                    vaa)
            except Exception as e:
                local_logger.error(f'Parse signed vaa for emitterChainId:{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            if time.time() > int(vaa_data[1]) + 5 * 60:
                local_logger.warning(
                    f'For emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} '
                    f'beyond 5min')
                continue
            if transfer_data[4] != dstSoDiamond:
                local_logger.warning(
                    f'For emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} '
                    f'dstSoDiamond: {dstSoDiamond} '
                    f'not match: {transfer_data[4]}')
                continue
            try:
                get_wormhole_facet().completeSoSwap(
                    vaa, {"from": get_account()})
            except Exception as e:
                local_logger.error(f'Complete so swap for emitterChainId:{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            logger.info(f'Process emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} success!')
        time.sleep(60)


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
        t1.join()
        t2.join()


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
    process_v1(SUPPORTED_EVM[0]["dstWormholeChainId"], SUPPORTED_EVM[0]["dstSoDiamond"])
