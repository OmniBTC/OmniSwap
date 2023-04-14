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
    cmd = "curl --silent https://scanapi.multichain.org/v3/tx/{tx}"
    receivers = {
        "mainnet": [
            {
                "tx": "0x392c0f395b196a9e05b38c3c94e2cb22d86ebb96e778b611fa0da426f577a031",
                "receiver": "0xaE3e419dA4740bA6AF85fcAE315f696fE6F8841d",
            },
            {
                "tx": "0x1060668e2aaf4204c9f6b76bb6ba008314c2279276c76b54ce14f6e1fa1ac747",
                "receiver": "0xe52aE1C32AF9E2d1ea1B180998a0cd4adC27F00E",
            },
        ],
        "avax-main": [
            {
                "tx": "0xa4ddb4499e191b3028c1bb3a84eb5a39dc7f5f506e3d43bf330063c6720852a1",
                "receiver": "0x372D0E22Ad7Db405bfe453f5b120ECDeDd65E1A2",
            }
        ],
        "bsc-main": [
            {
                "tx": "0xe2db5516c997c997127350ac891ed467c525c348f27c62bd41e4ecac19902815",
                "receiver": "0xC24b755A3071BA5C5833C17a8B76A00fF212B935",
            },
            {
                "tx": "0xffb3d2ad8b3463d0c0a7681122e63f7ac5b6f13f6171909734a027ea7518b244",
                "receiver": "0x5F94D02B0B6087D22cDF40339df7796D0f93CC0A",
            },
            {
                "tx": "0xa8f2b5ebcee7777a749091cf6ed34bd9ced7b144dc78de9a4ccfaba6d688447b",
                "receiver": "0xDFAB516FE8B7c06e06E725F9d0C1735Ad1B2558D",
            },
            {
                "tx": "0x5ce298e82a2b64a8b2e9492e493264ec42666ee30842a9dab8ab1825518bfb85",
                "receiver": "0x5f72B0A205d655a2c03bcaF87A45600c386101C7",
            },
        ],
        "optimism-main": [
            {
                "tx": "0xd4c668e038de04a772efdb3473fe330d5e43e6e4b72dd5ec68c37d8629d8dc30",
                "receiver": "0x38E25E37dca1c7b672235c14E592acDED7F0944D",
            },
            {
                "tx": "0xfe529fe4a8b31d1f006ecce50dafdc9ae375108788d787689e01a6041373062e",
                "receiver": "0xfa6ECa16A900EFDf94027D1e30EA16310a7C37A7",
            },
            {
                "tx": "0x65c933e53c4234b4da7d364bc65e1dc27655b24a1b6fc926d29ec28023f13200",
                "receiver": "0x1487d6559001964Ff1CF52570176Eecec145f9C4",
            },
        ],
    }

    account = get_account()
    withdraw_contract = Contract.from_abi(
        "WithdrawFacet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820", WithdrawFacet.abi
    )

    for (network, txs) in receivers.items():
        change_network(network)

        for src_tx in txs:
            curl_cmd = cmd.replace("{tx}", src_tx["tx"])
            receiver = src_tx["receiver"]
            with os.popen(curl_cmd) as f:
                result = json.load(f)
                swaptx = result["info"]["swaptx"]
                symbol = result["info"]["swapinfo"]["routerSwapInfo"]["tokenID"]

                tx = chain.get_transaction(swaptx)

                anyToken = tx.events["LogAnySwapInAndExec"]["token"]
                amount = tx.events["LogAnySwapInAndExec"]["amount"]

                proxy_anyToken = Contract.from_abi(
                    "IMultiChainUnderlying",
                    anyToken,
                    interface.IMultiChainUnderlying.abi,
                )
                token = proxy_anyToken.underlying()

                print(network, receiver, token, symbol, amount)

                withdraw_contract.withdraw(token, receiver, amount, {"from": account})


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
