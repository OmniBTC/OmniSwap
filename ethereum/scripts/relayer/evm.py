import logging
import time
from collections import OrderedDict
from datetime import datetime
from multiprocessing import Process, set_start_method
from pathlib import Path

import ccxt
import pandas as pd
from brownie import project, network, web3
import threading

from brownie.network.transaction import TransactionReceipt
from retrying import retry
from scripts.helpful_scripts import get_account, change_network, reconnect_random_rpc, PersistentDictionary
from scripts.relayer.select_evm import (
    get_pending_data,
    get_signed_vaa_by_wormhole,
    get_chain_id_to_net,
    NET
)
from scripts.relayer.wormhole_serder import parseTransferWithPayloadVaa
from scripts.serde import parse_vaa_to_wormhole_payload, get_wormhole_facet

FORMAT = "%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

if NET == "mainnet":
    SUPPORTED_EVM = [
        {
            "dstWormholeChainId": 2,
            "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
            "dstNet": "mainnet",
        },
        {
            "dstWormholeChainId": 4,
            "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
            "dstNet": "bsc-main",
        },
        {
            "dstWormholeChainId": 5,
            "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
            "dstNet": "polygon-main",
        },
        {
            "dstWormholeChainId": 6,
            "dstSoDiamond": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
            "dstNet": "avax-main",
        },
    ]
else:
    SUPPORTED_EVM = [
        {"dstWormholeChainId": 4,
         "dstSoDiamond": "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc",
         "dstNet": "bsc-test"
         }
    ]


def get_pending_data_from_solana(dstWormholeChainId):
    evm_net = network.show_active()
    if evm_net is None:
        evm_net = "bsc-test"
    local_logger = logger.getChild(f"[{evm_net}]")
    sequence_dict = PersistentDictionary(f"./cache/solana_{evm_net}_sequence.json")
    dst_diamond = list(filter(lambda d: d["dstNet"] == evm_net, SUPPORTED_EVM))[0]["dstSoDiamond"]
    dst_diamond = dst_diamond.replace("0x", "").lower()
    if NET == "mainnet":
        solana_net = "solana-mainnet"
    else:
        solana_net = "solana-testnet"
    default_value = 25508
    sequence = sequence_dict.get(solana_net, default_value)
    emitter_chain_id = 1
    while True:
        sequence += 1
        while True:
            vaa = get_signed_vaa_by_wormhole(sequence, emitter_chain_id)
            if vaa is None:
                local_logger.info(f"Query sequence {sequence} is None, waiting")
                time.sleep(10)
                continue
            else:
                local_logger.info(f"Query sequence {sequence} finish")
            break
        sequence_dict.set(solana_net, sequence)
        try:
            parsed_vaa, parsed_transfer, parsed_transfer_payload = parseTransferWithPayloadVaa(vaa)
            parsed_vaa = parsed_vaa.format_json()
            parsed_transfer = parsed_transfer.format_json()
            _parsed_transfer_payload = parsed_transfer_payload.format_json()
        except:
            continue
        if dst_diamond not in parsed_transfer["redeemer"].lower():
            continue
        if parsed_transfer["redeemerChain"] != dstWormholeChainId:
            continue
        info = {'chainName': solana_net,
                'extrinsicHash': parsed_vaa["hash"],
                'srcWormholeChainId': parsed_vaa["emitterChain"],
                'dstWormholeChainId': parsed_transfer["redeemerChain"],
                'sequence': parsed_vaa["sequence"],
                'blockTimestamp': parsed_vaa["timestamp"]
                }
        return info, vaa


@retry
def get_token_price():
    kucoin = ccxt.kucoin()
    result = {}
    for v in SUPPORTED_EVM:
        if v["dstNet"] in ["mainnet", "goerli",
                           "arbitrum-main", "arbitrum-test",
                           "optimism-main", "optimism-test",
                           "base-main", "base-test",
                           ]:
            result[v["dstWormholeChainId"]] = float(kucoin.fetch_ticker("ETH/USDT")['close'])
        elif v["dstNet"] in ["bsc-main", "bsc-test"]:
            result[v["dstWormholeChainId"]] = float(kucoin.fetch_ticker("BNB/USDT")['close'])
        elif v["dstNet"] in ["polygon-main", "polygon-test"]:
            result[v["dstWormholeChainId"]] = float(kucoin.fetch_ticker("MATIC/USDT")['close'])
        elif v["dstNet"] in ["avax-main", "avax-test"]:
            result[v["dstWormholeChainId"]] = float(kucoin.fetch_ticker("AVAX/USDT")['close'])
        else:
            raise ValueError(f"{v['dstNet']} not found")
    return result


def process_vaa(
        dstSoDiamond: str,
        vaa_str: str,
        emitterChainId: str,
        sequence: str,
        extrinsicHash: str,
        local_logger,
        limit_gas_price=True,
        price=0
) -> bool:
    try:
        # Use bsc-test to decode, too slow may need to change bsc-mainnet
        vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(vaa_str)
        dst_max_gas = wormhole_data[1]
        dst_max_gas_price = int(wormhole_data[0])
        if "main" in network.show_active() and dst_max_gas_price == 0:
            local_logger.warning(
                f"Parse signed vaa for emitterChainId:{emitterChainId}, "
                f"sequence:{sequence} dst_max_gas_price is 0"
            )
            return False
        dst_max_gas_price = (
            int(10 * 1e9) if dst_max_gas_price == 0 else dst_max_gas_price
        )
        estimate_gas_price = web3.eth.gas_price
        if dst_max_gas_price < estimate_gas_price * 0.5:
            local_logger.warning(
                f"Parse signed vaa for emitterChainId:{emitterChainId}, "
                f"sequence:{sequence} dst_max_gas_price: {dst_max_gas_price} lower 0.5 for "
                f"{estimate_gas_price}, pending")
            return False
        dst_max_gas_price = min(estimate_gas_price, dst_max_gas_price)
    except Exception as e:
        local_logger.error(
            f"Parse signed vaa for emitterChainId:{emitterChainId}, "
            f"sequence:{sequence} error: {e}"
        )
        return False

    if transfer_data[4] != dstSoDiamond:
        local_logger.warning(
            f"For emitterChainId:{emitterChainId}, sequence:{sequence} dstSoDiamond: {dstSoDiamond} "
            f"not match: {transfer_data[4]}"
        )
        return False
    try:
        local_logger.info(
            f"Start execute emitterChainId:{emitterChainId}, sequence:{sequence}"
        )
        acc = get_account()
        if limit_gas_price:
            result = get_wormhole_facet().completeSoSwap(
                vaa_str,
                {"from": acc, "nonce": acc.nonce, "gas_price": dst_max_gas_price},
            )
        else:
            result: TransactionReceipt = get_wormhole_facet().completeSoSwap(
                vaa_str, {"from": acc, "nonce": acc.nonce}
            )
        if isinstance(result.gas_used, int) and isinstance(result.gas_price, int):
            record_gas(
                dst_max_gas,
                dst_max_gas_price,
                result.gas_used,
                result.gas_price,
                src_net=get_chain_id_to_net()[vaa_data["emitterChainId"]]
                if int(vaa_data["emitterChainId"]) in get_chain_id_to_net()
                else 0,
                dst_net=network.show_active(),
                payload_len=int(len(vaa_str) / 2 - 1),
                swap_len=len(wormhole_data[3]),
                sequence=sequence,
                src_txid=extrinsicHash,
                dst_txid=result.txid,
                price=price
            )
            local_logger.info(
                f"Process emitterChainId:{emitterChainId}, sequence:{sequence}, txid:{result.txid}"
                f" success!"
            )
        else:
            local_logger.info(
                f"Process emitterChainId:{emitterChainId}, sequence:{sequence}, txid:{result.txid}"
                f" pending!"
            )
            return False
    except Exception as e:
        local_logger.error(
            f"Complete so swap for emitterChainId:{emitterChainId}, "
            f"sequence:{sequence} error: {e}"
        )
        return False
    return True


def process_v1(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    local_logger = logger.getChild(f"[v1|{network.show_active()}]")
    local_logger.info("Starting process v1...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}, acc:{get_account().address}")
    reconnect_random_rpc()
    last_update_endpoint = 0
    endpoint_interval = 30
    last_price_update = 0
    interval_price = 3 * 60
    price_info = {}
    has_process = {}
    while True:
        try:
            if time.time() >= interval_price + last_price_update:
                local_logger.info("Get token price")
                price_info = get_token_price()
                last_price_update = time.time()
        except Exception as e:
            local_logger.error(f'Get token price error: {e}')
            continue
        try:
            d, vaa = get_pending_data_from_solana(dstWormholeChainId)
        except Exception as e:
            local_logger.error(
                f'Get pending data from solana for {network.show_active()} error: {e}'
            )
            continue
        try:
            if time.time() > last_update_endpoint + endpoint_interval:
                reconnect_random_rpc()
                local_logger.info(f"Update rpc")
                last_update_endpoint = time.time()
            vaa = get_signed_vaa_by_wormhole(int(d["sequence"]), int(d["srcWormholeChainId"]))
            if vaa is None:
                local_logger.info(
                    f'Waiting vaa for emitterChainId: {d["srcWormholeChainId"]}, sequence:{d["sequence"]}')
                continue
        except Exception as e:
            local_logger.error(
                f'Get signed vaa for: emitterChainId: {d["srcWormholeChainId"]}, '
                f'sequence:{d["sequence"]} error: {e}'
            )
            continue
        try:
            # If gas price not enough, pending 7 day to manual process
            if (time.time() - d["blockTimestamp"]) >= 7 * 24 * 60 * 60 or NET != "mainnet":
                limit_gas_price = False
            else:
                limit_gas_price = True
        except:
            limit_gas_price = True
        has_key = (int(d["srcWormholeChainId"]), int(d["sequence"]))
        if (
                has_key in has_process
                and (time.time() - has_process[has_key]) <= 10 * 60
        ):
            local_logger.warning(
                f'emitterChainId:{d["srcWormholeChainId"]} sequence:{d["sequence"]} '
                f"inner 10min has process!"
            )
            continue
        else:
            has_process[has_key] = time.time()
        process_vaa(
            dstSoDiamond=dstSoDiamond,
            vaa_str=vaa,
            emitterChainId=d["srcWormholeChainId"],
            sequence=d["sequence"],
            extrinsicHash=d["extrinsicHash"],
            local_logger=local_logger,
            limit_gas_price=limit_gas_price,
            price=price_info[d["dstWormholeChainId"]]
        )


def process_v2(
        dstWormholeChainId: int,
        dstSoDiamond: str,
):
    local_logger = logger.getChild(f"[v2|{network.show_active()}]")
    local_logger.info("Starting process v2...")
    local_logger.info(f"SoDiamond:{dstSoDiamond}, acc:{get_account().address}")
    reconnect_random_rpc()
    last_update_endpoint = 0
    endpoint_interval = 30
    last_price_update = 0
    interval_price = 3 * 60
    price_info = {}
    has_process = {}
    if "test" in network.show_active() or "test" == "goerli":
        _pending_url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
        local_logger.info("Not process v2, end")
        return
    else:
        pending_url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    last_pending_time = 0
    pending_interval = 30
    while True:
        try:
            if time.time() < last_pending_time + pending_interval:
                continue
            else:
                last_pending_time = time.time()
            pending_data = get_pending_data(url=pending_url, dstWormholeChainId=dstWormholeChainId)
            local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        except Exception as e:
            local_logger.error(
                f'Get pending data for {network.show_active()} error: {e}'
            )
            continue

        try:
            if time.time() >= interval_price + last_price_update:
                local_logger.info("Get token price")
                price_info = get_token_price()
                last_price_update = time.time()
        except Exception as e:
            local_logger.error(f'Get token price error: {e}')
            continue

        for d in pending_data:
            try:
                if time.time() > last_update_endpoint + endpoint_interval:
                    reconnect_random_rpc()
                    local_logger.info(f"Update rpc")
                    last_update_endpoint = time.time()
                vaa = get_signed_vaa_by_wormhole(int(d["sequence"]), int(d["srcWormholeChainId"]))
                if vaa is None:
                    local_logger.info(
                        f'Waiting vaa for emitterChainId: {d["srcWormholeChainId"]}, sequence:{d["sequence"]}')
                    continue
            except Exception as e:
                local_logger.error(
                    f'Get signed vaa for: emitterChainId: {d["srcWormholeChainId"]}, '
                    f'sequence:{d["sequence"]} error: {e}'
                )
                continue
            try:
                # If gas price not enough, pending 7 day to manual process
                if (time.time() - d["blockTimestamp"]) >= 7 * 24 * 60 * 60:
                    limit_gas_price = False
                else:
                    limit_gas_price = True
            except:
                limit_gas_price = True
            has_key = (int(d["srcWormholeChainId"]), int(d["sequence"]))
            if (
                    has_key in has_process
                    and (time.time() - has_process[has_key]) <= 10 * 60
            ):
                local_logger.warning(
                    f'emitterChainId:{d["srcWormholeChainId"]} sequence:{d["sequence"]} '
                    f"inner 10min has process!"
                )
                continue
            else:
                has_process[has_key] = time.time()
            process_vaa(
                dstSoDiamond=dstSoDiamond,
                vaa_str=vaa,
                emitterChainId=d["srcWormholeChainId"],
                sequence=d["sequence"],
                extrinsicHash=d["extrinsicHash"],
                local_logger=local_logger,
                limit_gas_price=limit_gas_price,
                price=price_info[d["dstWormholeChainId"]]
            )


class Session(Process):
    def __init__(
            self,
            dstWormholeChainId: int,
            dstSoDiamond: str,
            dstNet: str,
            project_path: str,
            group=None,
            name=None,
            daemon=None,
    ):
        self.dstWormholeChainId = dstWormholeChainId
        self.dstSoDiamond = dstSoDiamond
        self.dstNet = dstNet
        self.project_path = project_path
        super().__init__(
            group=group, target=self.worker, name=name, args=(), daemon=daemon
        )
        self.start()

    def worker(self):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        try:
            change_network(self.dstNet)
        except:
            logger.error(f"Connect {self.dstNet} fail")
            return
        t1 = None
        if NET == "testnet":
            t1 = threading.Thread(
                target=process_v1, args=(self.dstWormholeChainId, self.dstSoDiamond)
            )
            t1.start()
        t2 = threading.Thread(
            target=process_v2, args=(self.dstWormholeChainId, self.dstSoDiamond)
        )
        t2.start()
        while True:
            if t1 is not None and not t1.is_alive():
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
        file_path=Path(__file__).parent.parent.parent.parent.joinpath("gas"),
        sequence=None,
        src_txid=None,
        dst_txid=None,
        price=None,
):
    if not isinstance(actual_gas, int):
        actual_gas = sender_gas
    if not isinstance(actual_gas_price, int):
        actual_gas_price = sender_gas_price
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
    sender_value = sender_gas * sender_gas_price
    actual_value = actual_gas * actual_gas_price
    data = OrderedDict({
        "record_time": str(datetime.fromtimestamp(cur_timestamp))[:19],
        "src_net": src_net,
        "dst_net": dst_net,
        "sender_gas": sender_gas,
        "sender_gas_price": sender_gas_price,
        "sender_value": sender_value,
        "actual_gas": actual_gas,
        "actual_gas_price": actual_gas_price,
        "actual_value": actual_value,
        "payload_len": payload_len,
        "swap_len": swap_len,
        "sequence": sequence,
        "src_txid": src_txid,
        "dst_txid": dst_txid,
        "diff_gas": sender_value - actual_value,
        "diff_value": round((sender_value - actual_value) / 1e18 * price, 4)
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
    for d in SUPPORTED_EVM:
        Session(
            dstWormholeChainId=d["dstWormholeChainId"],
            dstSoDiamond=d["dstSoDiamond"],
            dstNet=d["dstNet"],
            name=d["dstNet"],
            project_path=str(project_path),
        )


def single_process():
    index = 1

    project_path = Path(__file__).parent.parent.parent
    p = project.load(project_path, raise_if_loaded=False)
    p.load_config()
    change_network(SUPPORTED_EVM[index]["dstNet"])

    process_v2(SUPPORTED_EVM[index]["dstWormholeChainId"], SUPPORTED_EVM[index]["dstSoDiamond"])


if __name__ == "__main__":
    main()
