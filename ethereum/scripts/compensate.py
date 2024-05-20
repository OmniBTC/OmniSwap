# @Time    : 2022/7/15 16:40
# @Author  : WeiDai
# @FileName: compensate.py
import functools
import json
import os

from brownie import (
    network,
    interface,
    SoDiamond,
    Contract,
    chain,
    StargateFacet,
    WithdrawFacet,
    config,
)

from scripts.helpful_scripts import get_account, get_stargate_router, change_network


def is_weth(net, token: str):
    return config["networks"][net]["token"]["weth"]["address"] == token


def zero_address():
    return "0x0000000000000000000000000000000000000000"


@functools.lru_cache
def chain_info():
    return {
        config["networks"][net]["chainid"]: net
        for net in config["networks"]
        if "chainid" in config["networks"][net]
    }


def get_net(chainid):
    info = chain_info()
    return info[chainid]


def compensate_v1():
    account = get_account()
    tx = chain.get_transaction(
        "0x756ef4f47aacce1cace0c9b3558f140d61abd4835f11c9783f3eea6246a9324a"
    )
    try:
        info = tx.events["CachedSwapSaved"]
    except:
        info = tx.events["CachedSgReceive"]

    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi
    )
    proxy_diamond.sgReceive(
        info["chainId"],
        info["srcAddress"],
        info["nonce"],
        info["token"],
        info["amountLD"],
        info["payload"],
        {"from": account},
    )


def compensate_v2():
    account = get_account()
    net = network.show_active()
    stargate_router = get_stargate_router()
    print(f"stragate router: {stargate_router}")
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)

    _srcChainId = 2
    _srcAddress = "6694340FC020C5E6B96567843DA2DF01B2CE1EB6"
    _nonce = 2084
    cached_info = stragate.cachedSwapLookup(_srcChainId, _srcAddress, _nonce)
    print("cached_info:", cached_info)
    stragate.clearCachedSwap.call(_srcChainId, _srcAddress, _nonce, {"from": account})


def compensate_v3():
    cmd = "curl --silent https://api.celerscan.com/scan/searchByTxHash?tx={tx}"
    receivers = {
        "0xb284673efaf4b855738e835f6ed8f6343095566fe6870671b89b8c668534c1c0": "0x0c8cD6Fa227e8fAF1330B265e496E87846b4f9Bc",
        "0x70d6119f7c76ce87291a747347cd2f9e65a4fbd74398eff9633b3c51668b319d": "0xb380BcB74261956BA7Fa7b7baE1F004383017e54",
        "0x848232e697e548a1ff15fdff4a20ccaaf1f6afd73b19d21b17b35c1437258c34": "0x6a8943b4c779CC30199832A5224280bbaAE02914",
        "0x69a3a3f4b0469593bcecfc5065b8b9c1826388b4d2904f1de6abeee6ee471dc0": "0xfF0b9681ef40Fd0992Ef52fD5bd94E0Fa21c0359",
        "0xf8dcf2fd9df5a1ef43e378e60d635f0adbe0c85169ac88bfb1c8873e0b971f65": "0xA9cC6e06b05eE600b0b58b839B74B981608e055a",
        "0x27e462015f0650dfeb92fb1feb15e7a81a828ab8529f01f19302e39e6977b000": "0x0e73b32E493D081Ee6b2C4766d7478F867B7374b",
        "0x0bfcdd38ff33e184a83fc3a8e429e23b4294c161a0534143f90e90aa69cc9756": "0x69527FEF6AEDb85FDD2851FC1D9F6D10e61864aA",
    }
    account = get_account()
    withdraw_contract = Contract.from_abi(
        "WithdrawFacet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820", WithdrawFacet.abi
    )
    for src_txid in receivers:
        cur_cmd = cmd.replace("{tx}", src_txid)
        with os.popen(cur_cmd) as f:
            result = json.load(f)
            result = result["txSearchInfo"][0]
        if len(result["message"]) == 0 or len(result["transfer"]) == 0:
            continue
        if (
            "execution_tx" in result["message"][0]
            and result["message"][0]["msg_status"] != 3
        ):
            received_amt = result["transfer"][0]["received_amt"]
            dst_token_addr = result["transfer"][0]["dst_token_addr"]
            dst_txid = result["message"][0]["execution_tx"]
            dst_chain_id = result["transfer"][0]["dst_chain_id"]
            src_chain_id = result["base_info"]["src_chain_id"]
            src_net = get_net(src_chain_id)
            dst_net = get_net(dst_chain_id)
            receiver = receivers[src_txid]
            is_weth_flag = is_weth(dst_net, dst_token_addr)
            actual_token_addr = zero_address() if is_weth_flag else dst_token_addr
            print(
                f"src: {src_net}, {src_txid}, dst: {dst_net}, {dst_txid} "
                f"received_amt:{received_amt}, dst_token_addr:{dst_token_addr}, "
                f"receiver:{receiver}, is_weth:{is_weth_flag}, actual_token_addr:{actual_token_addr}\n"
            )
            withdraw_contract.withdraw(
                actual_token_addr, receiver, received_amt, {"from": account}
            )


def compensate_v4():
    cmd = "curl --silent https://api.celerscan.com/scan/searchByTxHash?tx={tx}"
    receivers = {
        "0x80f6b7733c2361aad41923be52bdf896a63cb4cb065cb3046873e1d15d3d8471": "0x226B957018D22D68f11F9adB46873E982D0f080e",
    }
    account = get_account()
    withdraw_contract = Contract.from_abi(
        "WithdrawFacet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820", WithdrawFacet.abi
    )
    for src_txid in receivers:
        cur_cmd = cmd.replace("{tx}", src_txid)
        with os.popen(cur_cmd) as f:
            result = json.load(f)
            result = result["txSearchInfo"][0]
        if len(result["transfer"]) == 0:
            continue
        received_amt = int(result["transfer"][0]["received_amt"])
        dst_token_addr = result["transfer"][0]["dst_token_addr"]
        dst_chain_id = result["transfer"][0]["dst_chain_id"]
        src_chain_id = result["base_info"]["src_chain_id"]
        src_net = get_net(src_chain_id)
        dst_net = get_net(dst_chain_id)
        receiver = receivers[src_txid]
        is_weth_flag = is_weth(dst_net, dst_token_addr)
        actual_token_addr = zero_address() if is_weth_flag else dst_token_addr
        print(
            f"src: {src_net}, {src_txid}, dst: {dst_net}, "
            f"received_amt:{received_amt}, dst_token_addr:{dst_token_addr}, "
            f"receiver:{receiver}, is_weth:{is_weth_flag}, actual_token_addr:{actual_token_addr}\n"
        )
        withdraw_contract.withdraw(
            actual_token_addr, receiver, received_amt, {"from": account}
        )


def compensate_v5():
    change_network("zksync2-main")

    cmd = "curl --silent https://api.celerscan.com/scan/searchByTxHash?tx={tx}"
    receivers = {
        "0x5c0ef9497024799567c2531dc9aa69d256eed23dd7389b6eea9fce5243ef95b8": "0xcf8bA4670664407820a6da53BC0cF607ec4166Ea",
    }
    account = get_account()
    withdraw_contract = Contract.from_abi(
        "WithdrawFacet", "0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577", WithdrawFacet.abi
    )

    for src_txid in receivers:
        cur_cmd = cmd.replace("{tx}", src_txid)
        with os.popen(cur_cmd) as f:
            result = json.load(f)
            result = result["txSearchInfo"][0]
        if len(result["transfer"]) == 0:
            continue
        if (
            result["transfer"][0]["xfer_status"] != 6
            or result["transfer"][0]["refund_tx"] == ""
        ):
            continue

        refund_tx = result["transfer"][0]["refund_tx"]
        refund_amt = int(result["transfer"][0]["refund_amt"])
        src_chain_id = result["base_info"]["src_chain_id"]
        src_net = get_net(src_chain_id)
        receiver = receivers[src_txid]
        actual_token_addr = zero_address()
        print(
            f"src: {src_net}, src_tx:{src_txid}, refund_tx:{refund_tx}\n"
            f"receiver:{receiver}, actual_token_addr:{actual_token_addr}, refund_amt:{refund_amt}\n"
        )
        # withdraw_contract.withdraw(
        #     actual_token_addr, receiver, refund_amt, {"from": account}
        # )


def withdraw():
    account = get_account()
    withdraw_contract = Contract.from_abi(
        "WithdrawFacet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820", WithdrawFacet.abi
    )
    withdraw_contract.withdraw(
        "0x0000000000000000000000000000000000000000",
        "0x3A9788D3E5B644b97A997DC5aC29736C388af9A3",
        70032067045653004,
        {"from": account},
    )
