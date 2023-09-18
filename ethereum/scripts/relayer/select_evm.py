import base64
import functools
import random

import requests
from brownie import network


def get_wormhole_info(package) -> dict:
    """Get token bridge info"""
    info = {}
    for net, c in package.config["networks"].items():
        try:
            info[c["wormhole"]["chainid"]] = c["wormhole"]["token_bridge"]
        except:
            pass
    return info


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
    "https://wormhole-v2-mainnet-api.certus.one",
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
