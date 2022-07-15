# @Time    : 2022/7/15 16:40
# @Author  : WeiDai
# @FileName: compensate.py
from brownie import network, config, interface, SoDiamond, Contract, chain, StargateFacet

from scripts.helpful_scripts import get_account


def compensate_v1():
    account = get_account()
    tx = chain.get_transaction("0x73366d95464ca263fe82bd1521104bc373ed06293cafca1504cc2f4ee1437064")
    info = tx.events["CachedSwapSaved"]
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    proxy_diamond.sgReceive(
        info["chainId"],
        info["srcAddress"],
        info["nonce"],
        info["token"],
        info["amountLD"],
        info["payload"],
        {"from": account}
    )


def main():
    account = get_account()
    net = network.show_active()
    stargate_router = config["networks"][net]["stargate_router"]
    print(f"stragate router: {stargate_router}")
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)

    _srcChainId = 2
    _srcAddress = "6694340FC020C5E6B96567843DA2DF01B2CE1EB6"
    _nonce = 2084
    cached_info = stragate.cachedSwapLookup(_srcChainId, _srcAddress, _nonce)
    print("cached_info:", cached_info)
    stragate.clearCachedSwap.call(_srcChainId, _srcAddress, _nonce, {"from": account})
