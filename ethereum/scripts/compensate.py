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

from scripts.helpful_scripts import get_account, get_stargate_router


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
        "0x0f2c5a8c7d1266d4d1206c736650d64a3210d6096db4c353ff7301fa658370d1": "0xD3064a2c76Ac1e4a3aa54365f692D0611ab5866b",
        "0x1eaaf3bfa7e864ce0d09ace5a0f95c90eb0cb50baec671cbcf9528d74b9a9262": "0xe10c0E94B2C87CeBCA499Ae421de8B8dc8467256",
        "0xab9cffc8bc2494d56b12ca27b94489f8d1ca84186cb3120daf77a83c5617639c": "0x570C3A5CcBadBF5190bf000B1D1c54ECC1ae79dc",
        "0xa5f0b04367656198adeea004d5cf763930c0799d073fd4ba2ac3dde186aebcf1": "0xecB87EFD94CD0be564b7Cc959E176D217c6dc1FC",
        "0xa45fef3ff8d3295e9a2138f58b813a43802785bf2e6bd094bc2ede056386a8c6": "0xb204174fDFafD413616E1696498f12d39161351F",
        "0x5e447edaad94daacbed47b50add0a038771e981d0c125d4bd8476a9799da6984": "0xcf8cf5dF28dB4F4e8376C90D8CEbd5f7A4F73620",
        "0x200774e4e6759c215806f06f6e36470afd6737f94aa9f80ffd276968b577aa25": "0xd798dFAD9CE8FcD535A54E963dBD5Ea6c4985530",
        "0xbe78839e6b5bb98f9fb9cd11a0d99a2609a290464455880c94d6e98a322c7d20": "0x87B7F62CE23a8687EaF0E2C457AD0C22CA3554BF",
        "0xfc3cef5fcdc8a8759a43d027b5bbc6a46180a03e9ca334b8bddf2c49eb939299": "0x6d0EcBDfdDFb204b3cabA1B07B3Ef4436c10A84b",
        "0x07a5f7ff2ee23619affb24c9b5b7a397635bb82b7ce69d70eeccae5fc4084dce": "0xA09B6900FfE71D0674fa6d4fC7e157129510Ff41",
        "0x0f0c8356e44675c8176739c36ee23f48b66db2b4e8e44a6b2420d4d15567d90b": "0x7206BC81E2C52441EEFfE120118aC880f4528dDA",
        "0xb0a3ed86668e6dec58038b2b5894aef38d63cd1288699a07e5177f5bb26c2584": "0x2ADa4a982200f4A433Ab021A4a8dC9eEbCc1640d",
        "0x458e82892947136a992c9a5753e3f79aff677ce3c01b6be935186273a9f1d634": "0xae9B0430Edd78f20c90BF38FDAD7C4dC823b8308",
        "0x645c8d22da3e9da9bc2f88127967a703da8aac9f2b6eace4f780000ad8fdbfe7": "0x62298E04A3a8424FE10072387aa83343D43A5d9f",
        "0xb673a3504637508de570c343b47c47636d49a9719fa35a9453f55d2f7d549c1a": "0xF87f42c3AD75941227F8bab0e775596371cEFCca",
        "0x4cdb806413e2a5c51960ef3c2428fcd0b56406572e20f5f6c539adbbbdd48c6d": "0x866959f5a67C5B791a7A42d777a33e34Fd0e3cc6",
        "0x3393b6a64aef7d36e00498c5f92b82d385ea8a6307b61435daaa9ffa743bddc2": "0x2745Bc98db272ea5bbf70C1FE373dF4812E5F2dC",
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
        # withdraw_contract.withdraw(
        #     actual_token_addr, receiver, received_amt, {"from": account}
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
