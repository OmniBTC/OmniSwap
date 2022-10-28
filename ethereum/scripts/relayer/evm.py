import logging
import time
from multiprocessing import Process, set_start_method
from pathlib import Path

from brownie import project, network
import threading

from scripts.helpful_scripts import get_account, change_network, padding_to_bytes
from scripts.relayer.select import get_pending_data, get_signed_vaa, get_signed_vaa_by_to
from scripts.serde import parse_vaa_to_wormhole_payload, get_wormhole_facet

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")


# SUPPORTED_EVM = [
#     {"dstWormholeChainId": 2,
#      "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
#      "dstNet": "mainnet"
#      },
#     {"dstWormholeChainId": 4,
#      "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
#      "dstNet": "bsc-main"
#      },
#     {"dstWormholeChainId": 5,
#      "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
#      "dstNet": "polygon-main"
#      },
#     {"dstWormholeChainId": 6,
#      "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
#      "dstNet": "avax-main"
#      },
# ]


SUPPORTED_EVM = [
    {"dstWormholeChainId": 4,
     "dstSoDiamond": "0xFeEE07da1B3513BdfD5440562e962dfAac19566F",
     "dstNet": "bsc-test"
     },
    {"dstWormholeChainId": 6,
     "dstSoDiamond": "0xBb032459B39547908eDB8E690c030Dc4F31DA673",
     "dstNet": "avax-test"
     },
]


def process_v1(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    local_logger = logger.getChild(f"[{network.show_active()}]")
    local_logger.info("Starting process v1...")
    local_logger.info(f'SoDiamond:{dstSoDiamond}')
    has_process = {}
    while True:
        try:
            if "test" in network.show_active() or "test" == "goerli":
                url = "http://wormhole-testnet.sherpax.io"
            else:
                url = "http://wormhole-vaa.chainx.org"
            result = get_signed_vaa_by_to(dstWormholeChainId, url=url)
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
    local_logger.info(f'SoDiamond:{dstSoDiamond}')
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
                if "test" in network.show_active() or "test" == "goerli":
                    url = "http://wormhole-testnet.sherpax.io"
                else:
                    url = "http://wormhole-vaa.chainx.org"
                vaa = get_signed_vaa(
                    int(d["sequence"]), int(d["srcWormholeChainId"]), url=url)
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
            # interval = 3 * 60 * 60
            # if time.time() > int(vaa_data[1]) + interval:
            #     local_logger.warning(
            #         f'For emitterChainId:{d["srcWormholeChainId"]}, sequence:{d["sequence"]} '
            #         f'beyond {int(interval / 60)}min')
            #     continue
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
        # t2 = threading.Thread(target=process_v2, args=(
        #     self.dstWormholeChainId, self.dstSoDiamond))
        t1.start()
        # t2.start()
        while True:
            if not t1.is_alive():
                if not network.is_connected():
                    change_network(self.dstNet)
                t1.start()
            # if not t2.is_alive():
            #     if not network.is_connected():
            #         change_network(self.dstNet)
            #     t2.start()
            time.sleep(10 * 60 * 60)


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
