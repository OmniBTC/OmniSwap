import base64
import functools
import logging
import random
import threading
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import ccxt
import pandas as pd
import requests
from brownie import network
from retrying import retry
from sui_brownie import SuiPackage, SuiObject, Argument, U16, NestedResult

from scripts import sui_project
from scripts.serde_sui import parse_vaa_to_wormhole_payload
from scripts.struct_sui import decode_hex_to_ascii, hex_str_to_vector_u8, change_network

FORMAT = '%(asctime)s - %(funcName)s - %(levelname)s - %(name)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel("INFO")

net = sui_project.network
package_id = sui_project.network_config["packages"]["OmniSwap"]
sui_package = SuiPackage(package_id=package_id, package_name="OmniSwap")


def format_emitter_address(addr):
    addr = addr.replace("0x", "")
    if len(addr) < 64:
        addr = "0" * (64 - len(addr)) + addr
    return addr


# network name -> wormhole chain id
NET_TO_WORMHOLE_CHAIN_ID = {
    # mainnet
    "mainnet": 2,
    "bsc-main": 4,
    "polygon-main": 5,
    "avax-main": 6,
    "optimism-main": 24,
    "arbitrum-main": 23,
    "aptos-mainnet": 22,
    "sui-mainnet": 21,
    "base-main": 30,
    # testnet
    "goerli": 2,
    "bsc-test": 4,
    "polygon-test": 5,
    "avax-test": 6,
    "optimism-test": 24,
    "arbitrum-test": 23,
    "aptos-testnet": 22,
    "sui-testnet": 21,
}

WORMHOLE_GUARDIAN_RPC = [
    "https://api.wormholescan.io",
    "https://wormhole-v2-mainnet-api.mcf.rocks",
    "https://wormhole-v2-mainnet-api.chainlayer.network",
    "https://wormhole-v2-mainnet-api.staking.fund",
]

# Net -> emitter

NET_TO_EMITTER = {
    "mainnet": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
    "bsc-main": "0xB6F6D86a8f9879A9c87f643768d9efc38c1Da6E7",
    "polygon-main": "0x5a58505a96D1dbf8dF91cB21B54419FC36e93fdE",
    "avax-main": "0x0e082F06FF657D94310cB8cE8B0D9a04541d8052",
    "optimism-main": "0x1D68124e65faFC907325e3EDbF8c4d84499DAa8b",
    "arbitrum-main": "0x0b2402144Bb366A632D14B83F244D2e0e21bD39c",
    "aptos-mainnet": "0000000000000000000000000000000000000000000000000000000000000001",
    "sui-mainnet": "0xccceeb29348f71bdd22ffef43a2a19c1f5b5e17c5cca5411529120182672ade5",
    "base-main": "0x8d2de8d2f73F1F4cAB472AC9A881C9b123C79627",
}


@retry
def get_token_price():
    kucoin = ccxt.kucoin()
    return float(kucoin.fetch_ticker("SUI/USDT")['close'])


@functools.lru_cache()
def get_chain_id_to_net():
    return {v: k for k, v in NET_TO_WORMHOLE_CHAIN_ID.items() if "main" in k}
    # if "main" in network.show_active():
    #     return {v: k for k, v in NET_TO_WORMHOLE_CHAIN_ID.items() if "main" in k}
    # else:
    #     return {v: k for k, v in NET_TO_WORMHOLE_CHAIN_ID.items() if "main" not in k}


def get_signed_vaa_by_wormhole(
        sequence: int,
        emitter_chain_id: str = None
):
    wormhole_url = random.choice(WORMHOLE_GUARDIAN_RPC)
    src_net = get_chain_id_to_net()[emitter_chain_id]
    emitter = NET_TO_EMITTER[src_net]
    emitter_address = format_emitter_address(emitter)

    url = f"{wormhole_url}/v1/signed_vaa/{emitter_chain_id}/{emitter_address}/{sequence}"
    response = requests.get(url)

    if 'vaaBytes' not in response.json():
        return None

    vaa_bytes = response.json()['vaaBytes']
    vaa = base64.b64decode(vaa_bytes).hex()
    return f"0x{vaa}"


def get_pending_data(url: str = None, dstWormholeChainId=None) -> list:
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
            result.sort(key=lambda x: x["sequence"])
            return [v for v in result if str(v["dstWormholeChainId"]) == str(dstWormholeChainId)]
        else:
            return []
    except:
        return []


@functools.lru_cache()
def get_deepbook_package_id():
    return sui_project.network_config["packages"]["DeepBook"]


@functools.lru_cache()
def get_cetus_package_id():
    return sui_project.network_config["packages"]["CetusClmm"]["origin"]


@functools.lru_cache()
def get_cetus_config():
    return sui_project.network_config["objects"]["GlobalConfig"]


@functools.lru_cache()
def deepbook_v2_storage():
    return sui_project.network_config['objects']['DeepbookV2Storage']


def normal_ty_arg(ty):
    if ty[:2] != "0x":
        ty = "0x" + ty
    return ty


def multi_swap(
        omniswap,
        pool_id: str,
        sending_asset_id: str,
        receiving_asset_id: str,
        pool_id_index: int,
        swap_index: int,
        dex_index: int,
        swap_start_index: int,
):
    sending_asset_id = normal_ty_arg(sending_asset_id)
    receiving_asset_id = normal_ty_arg(receiving_asset_id)

    sui_type: str = sui_project.client.sui_getObject(pool_id, {
        "showType": True,
        "showOwner": True,
        "showPreviousTransaction": False,
        "showDisplay": False,
        "showContent": False,
        "showBcs": False,
        "showStorageRebate": False
    })["data"]["type"]
    origin_type = SuiObject.from_type(sui_type)
    if origin_type.package_id == get_deepbook_package_id():
        dex_name = "deepbook_v2"
    elif origin_type.package_id == get_cetus_package_id():
        dex_name = "cetus"
    else:
        raise ValueError(origin_type.package_id)

    start_index = sui_type.find("<")
    end_index = sui_type.find(",")
    sui_type = SuiObject.from_type(sui_type[start_index + 1:end_index].replace(" ", ""))

    if "2::sui::SUI" in str(sui_type):
        sui_type = "0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI"

    if str(sui_type).replace("0x", "") == str(SuiObject.from_type(sending_asset_id)).replace("0x", ""):
        ty_args = [sending_asset_id, receiving_asset_id]
        reverse = "quote"
    else:
        ty_args = [receiving_asset_id, sending_asset_id]
        reverse = "base"
    return [
        getattr(omniswap.wormhole_facet, f"multi_swap_for_{dex_name}_{reverse}_asset"),
        [
            Argument("Input", U16(6 + dex_index)),
            Argument("Input", U16(swap_start_index + pool_id_index)),
            Argument("NestedResult", NestedResult(U16(swap_index), U16(0))),
            Argument("Input", U16(5)),
        ],
        ty_args
    ]


def process_vaa(
        dstSoDiamond: str,
        vaa_str: str,
        emitterChainId: str,
        sequence: str,
        extrinsicHash: str,
        local_logger,
        is_admin: bool = False,
        price=0,
) -> bool:
    try:
        # Use bsc-test to decode, too slow may need to change bsc-mainnet
        vaa_str = vaa_str if "0x" in vaa_str else "0x" + vaa_str
        vaa_data, transfer_data, wormhole_data = parse_vaa_to_wormhole_payload(
            sui_project, network.show_active(),
            vaa_str)
        dst_max_gas = wormhole_data[1]
        dst_max_gas_price = int(wormhole_data[0] / 1e9)
        dst_max_gas_price = min(sui_project.estimate_gas_price(), dst_max_gas_price)
        if "main" in sui_project.network and dst_max_gas_price == 0:
            local_logger.warning(f'Parse signed vaa for emitterChainId:{emitterChainId}, '
                                 f'sequence:{sequence} dst_max_gas_price is zero')
            return False

    except Exception as e:
        local_logger.error(f'Parse signed vaa for emitterChainId:{emitterChainId}, '
                           f'sequence:{sequence} error: {e}')
        return False

    if transfer_data[4] != dstSoDiamond:
        local_logger.warning(
            f'For emitterChainId:{emitterChainId}, sequence:{sequence} dstSoDiamond: {dstSoDiamond} '
            f'not match: {transfer_data[4]}')
        return False
    try:
        final_asset_id = decode_hex_to_ascii(wormhole_data[2][5])
        final_asset_id = final_asset_id if "0x" == final_asset_id[:2] else "0x" + final_asset_id
        if len(wormhole_data[3]) == 0:
            ty_args = [final_asset_id]
            cross_asset_id = final_asset_id
            pool_id = None
            reverse = None
            dex_name = None
            multi = []
            dex_config = []
        elif len(wormhole_data[3]) == 1:
            multi = []
            dex_config = []
            s1 = decode_hex_to_ascii(wormhole_data[3][0][2])
            s1 = s1 if "0x" == s1[:2] else "0x" + s1
            cross_asset_id = s1
            s2 = final_asset_id
            pool_id = str(wormhole_data[3][0][0])
            sui_type: str = sui_project.client.sui_getObject(pool_id, {
                "showType": True,
                "showOwner": True,
                "showPreviousTransaction": False,
                "showDisplay": False,
                "showContent": False,
                "showBcs": False,
                "showStorageRebate": False
            })["data"]["type"]
            origin_type = SuiObject.from_type(sui_type)
            if origin_type.package_id == get_deepbook_package_id():
                dex_name = "deepbook_v2"
            elif origin_type.package_id == get_cetus_package_id():
                dex_name = "cetus"
            else:
                raise ValueError(origin_type.package_id)

            start_index = sui_type.find("<")
            end_index = sui_type.find(",")
            sui_type = SuiObject.from_type(sui_type[start_index + 1:end_index].replace(" ", ""))

            if str(sui_type).replace("0x", "") == str(SuiObject.from_type(s1)).replace("0x", ""):
                ty_args = [s1, s2]
                reverse = False
            else:
                ty_args = [s2, s1]
                reverse = True
        else:
            multi = []
            pool_id = []
            reverse = None
            dex_name = None
            ty_args = []
            dex_config = []
            s1 = decode_hex_to_ascii(wormhole_data[3][0][2])
            s1 = s1 if "0x" == s1[:2] else "0x" + s1
            cross_asset_id = s1
            for k, d in enumerate(wormhole_data[3]):
                if str(d[0]) not in pool_id:
                    pool_id.append(str(d[0]))
                sui_type: str = sui_project.client.sui_getObject(pool_id[-1], {
                    "showType": True,
                    "showOwner": True,
                    "showPreviousTransaction": False,
                    "showDisplay": False,
                    "showContent": False,
                    "showBcs": False,
                    "showStorageRebate": False
                })["data"]["type"]

                start_index = sui_type.find("<")
                end_index = sui_type.find(",")
                ty_args.append(SuiObject.from_type(sui_type[start_index + 1:end_index].replace(" ", "")))

                origin_type = SuiObject.from_type(sui_type)
                if origin_type.package_id == get_deepbook_package_id():
                    try:
                        dex_index = dex_config.index(deepbook_v2_storage())
                    except:
                        dex_index = -1
                    if dex_index == -1:
                        dex_config.append(deepbook_v2_storage())
                        dex_index = len(dex_config) - 1
                elif origin_type.package_id == get_cetus_package_id():
                    try:
                        dex_index = dex_config.index(get_cetus_config())
                    except:
                        dex_index = -1
                    if dex_index == -1:
                        dex_config.append(get_cetus_config())
                        dex_index = len(dex_config) - 1
                else:
                    raise ValueError(origin_type.package_id)
                multi.append({
                    "pool_id": str(d[0]),
                    "sending_asset_id": normal_ty_arg(str(decode_hex_to_ascii(d[2]))),
                    "receiving_asset_id": normal_ty_arg(str(decode_hex_to_ascii(d[3]))),
                    "pool_id_index": len(pool_id) - 1,
                    "swap_index": k,
                    "dex_index": dex_index
                })
            for d in multi:
                d["swap_start_index"] = 6 + len(dex_config)

        local_logger.info(f'Execute emitterChainId:{emitterChainId}, sequence:{sequence}...')
        storage = sui_project.network_config["objects"]["FacetStorage"]
        token_bridge_state = sui_project.network_config["objects"]["TokenBridgeState"]
        wormhole_state = sui_project.network_config["objects"]["WormholeState"]
        wormhole_fee = sui_project.network_config["objects"]["WormholeFee"]
        clock = sui_project.network_config["objects"]["Clock"]
        facet_manager = sui_project.network_config["objects"]["FacetManager"]
        if not is_admin:
            try:
                if len(multi):
                    mid_params = [
                        multi_swap(sui_package, **v)
                        for v in multi
                    ]

                    result = sui_project.batch_transaction(
                        actual_params=[
                            storage,
                            token_bridge_state,
                            wormhole_state,
                            wormhole_fee,
                            hex_str_to_vector_u8(vaa_str),
                            clock,
                            *dex_config,
                            *pool_id
                        ],
                        transactions=[
                            [
                                sui_package.wormhole_facet.complete_so_multi_swap,
                                [
                                    Argument("Input", U16(0)),
                                    Argument("Input", U16(1)),
                                    Argument("Input", U16(2)),
                                    Argument("Input", U16(3)),
                                    Argument("Input", U16(4)),
                                    Argument("Input", U16(5)),
                                ],
                                [multi[0]["sending_asset_id"]]
                            ],
                            *mid_params,
                            [
                                sui_package.wormhole_facet.complete_multi_dst_swap,
                                [
                                    Argument("NestedResult", NestedResult(U16(len(mid_params)), U16(0))),
                                    Argument("NestedResult", NestedResult(U16(0), U16(1))),
                                ],
                                [multi[-1]["receiving_asset_id"]]
                            ]
                        ]
                    )

                elif pool_id is None:
                    result = sui_package.wormhole_facet.complete_so_swap_without_swap(
                        storage,
                        token_bridge_state,
                        wormhole_state,
                        wormhole_fee,
                        hex_str_to_vector_u8(vaa_str),
                        clock,
                        type_arguments=ty_args,
                        gas_price=dst_max_gas_price
                    )
                elif not reverse:
                    if dex_name == "deepbook_v2":
                        result = sui_package.wormhole_facet.complete_so_swap_for_deepbook_v2_quote_asset(
                            storage,
                            token_bridge_state,
                            wormhole_state,
                            wormhole_fee,
                            pool_id,
                            deepbook_v2_storage(),
                            hex_str_to_vector_u8(vaa_str),
                            clock,
                            type_arguments=ty_args,
                            gas_price=dst_max_gas_price
                        )
                    else:
                        result = sui_package.wormhole_facet.complete_so_swap_for_cetus_quote_asset(
                            storage,
                            token_bridge_state,
                            wormhole_state,
                            wormhole_fee,
                            get_cetus_config(),
                            pool_id,
                            hex_str_to_vector_u8(vaa_str),
                            clock,
                            type_arguments=ty_args,
                            gas_price=dst_max_gas_price
                        )
                else:
                    if dex_name == "deepbook_v2":
                        result = sui_package.wormhole_facet.complete_so_swap_for_deepbook_v2_base_asset(
                            storage,
                            token_bridge_state,
                            wormhole_state,
                            wormhole_fee,
                            pool_id,
                            deepbook_v2_storage(),
                            hex_str_to_vector_u8(vaa_str),
                            clock,
                            type_arguments=ty_args,
                            gas_price=dst_max_gas_price
                        )
                    else:
                        result = sui_package.wormhole_facet.complete_so_swap_for_cetus_base_asset(
                            storage,
                            token_bridge_state,
                            wormhole_state,
                            wormhole_fee,
                            get_cetus_config(),
                            pool_id,
                            hex_str_to_vector_u8(vaa_str),
                            clock,
                            type_arguments=ty_args,
                            gas_price=dst_max_gas_price
                        )

            except Exception as e:
                if time.time() > vaa_data[1] + 60 * 60:
                    assert final_asset_id is not None
                    local_logger.error(f'Complete so swap for emitterChainId:{emitterChainId}, '
                                       f'sequence:{sequence}, start compensate for error: {e}')
                    result = sui_package.wormhole_facet.complete_so_swap_by_relayer(
                        storage,
                        facet_manager,
                        token_bridge_state,
                        wormhole_state,
                        wormhole_fee,
                        hex_str_to_vector_u8(vaa_str),
                        clock,
                        type_arguments=[str(cross_asset_id)],
                        gas_price=dst_max_gas_price
                    )
                else:
                    raise e
        else:
            receiver = wormhole_data[2][1]
            local_logger.info(f"Compensate to:{receiver}")
            assert final_asset_id is not None
            if isinstance(ty_args, list) and len(ty_args) > 0:
                cross_asset_id = ty_args[0]
            else:
                cross_asset_id = final_asset_id
            result = sui_package.wormhole_facet.complete_so_swap_by_admin(
                storage,
                facet_manager,
                token_bridge_state,
                wormhole_state,
                wormhole_fee,
                hex_str_to_vector_u8(vaa_str),
                str(receiver),
                clock,
                type_arguments=[str(cross_asset_id)],
                gas_price=dst_max_gas_price
            )
        gas_price = int(result["transaction"]["data"]['gasData']['price'])
        gasUsedInfo = result["effects"]["gasUsed"]
        gas_used = int(gasUsedInfo["computationCost"]) + int(gasUsedInfo["storageCost"]) - \
                   int(gasUsedInfo["storageRebate"]) + int(gasUsedInfo["nonRefundableStorageFee"])
        gas_used = int(gas_used / gas_price)

        record_gas(
            int(dst_max_gas),
            int(dst_max_gas_price),
            gas_used,
            gas_price,
            src_net=get_chain_id_to_net()[vaa_data["emitterChainId"]]
            if int(vaa_data["emitterChainId"]) in get_chain_id_to_net() else 0,
            dst_net=sui_project.network,
            payload_len=int(len(vaa_str) / 2 - 1),
            swap_len=len(wormhole_data[3]),
            sequence=sequence,
            src_txid=extrinsicHash,
            dst_txid=result["digest"],
            price=price,
        )
    except Exception as e:
        local_logger.error(f'Complete so swap for emitterChainId:{emitterChainId}, '
                           f'sequence:{sequence} error: {e}')
        return False
    local_logger.info(f'Process emitterChainId:{emitterChainId}, sequence:{sequence} success!')
    return True


def process_v2(
        dstWormholeChainId: int = 21,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[v2|{sui_project.network}]")
    local_logger.info("Starting process v2...")
    if "test" in sui_project.network or "test" == "goerli":
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    else:
        pending_url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    has_process = {}
    last_price_update = 0
    interval_price = 3 * 60
    price_info = 0
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
                f'Get pending data for sio error: {e}'
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
                vaa = get_signed_vaa_by_wormhole(int(d["sequence"]), int(d["srcWormholeChainId"]))
                if vaa is None:
                    local_logger.info(
                        f'Waiting vaa for emitterChainId: {d["srcWormholeChainId"]}, sequence:{d["sequence"]}')
                    continue
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            has_key = (int(d["srcWormholeChainId"]), int(d["sequence"]))
            if (
                    has_key in has_process
                    and (time.time() - has_process[has_key]) <= 3 * 60
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
                is_admin=False,
                price=price_info
            )


def compensate(
        sequences: list,
        dstWormholeChainId: int = 21,
        dstSoDiamond: str = None,
):
    local_logger = logger.getChild(f"[compensate|{sui_project.network}]")
    local_logger.info("Starting process compensate...")
    if "test" in sui_project.network or "test" == "goerli":
        pending_url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    else:
        pending_url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    while True:
        try:
            pending_data = get_pending_data(url=pending_url, dstWormholeChainId=dstWormholeChainId)
            local_logger.info(f"Get signed vaa length: {len(pending_data)}")
        except Exception as e:
            local_logger.error(
                f'Get pending data for sio error: {e}'
            )
            continue
        for d in pending_data:
            try:
                vaa = get_signed_vaa_by_wormhole(int(d["sequence"]), int(d["srcWormholeChainId"]))
                if vaa is None:
                    local_logger.info(
                        f'Waiting vaa for emitterChainId: {d["srcWormholeChainId"]}, sequence:{d["sequence"]}')
                    continue
                if int(d["sequence"]) not in sequences:
                    continue
            except Exception as e:
                local_logger.error(f'Get signed vaa for :{d["srcWormholeChainId"]}, '
                                   f'sequence:{d["sequence"]} error: {e}')
                continue
            process_vaa(
                dstSoDiamond=dstSoDiamond,
                vaa_str=vaa,
                emitterChainId=d["srcWormholeChainId"],
                sequence=d["sequence"],
                extrinsicHash=d["extrinsicHash"],
                local_logger=local_logger,
                is_admin=True,
                price=get_token_price()
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
        src_txid=None,
        dst_txid=None,
        price=0,
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
        "dst_txid": dst_txid,
        "src_txid": src_txid,
        "diff_gas": sender_value - actual_value,
        "diff_value": round((sender_value - actual_value) / 1e9 * price, 4)
    })
    columns = list(data.keys())
    data = pd.DataFrame([data])
    data = data[columns]
    if file_name.exists():
        data.to_csv(str(file_name), index=False, header=False, mode='a')
    else:
        data.to_csv(str(file_name), index=False, header=True, mode='w')


def main():
    print(f'SoDiamond:{sui_project.network_config["SoDiamond"]}')
    t2 = threading.Thread(target=process_v2, args=(21, sui_project.network_config["SoDiamond"]))
    t2.start()
    t2.join()


def single_process():
    change_network("polygon-main")
    process_v2(21, sui_project.network_config["SoDiamond"])


if __name__ == "__main__":
    single_process()
