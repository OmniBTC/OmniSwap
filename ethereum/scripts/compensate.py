# @Time    : 2022/7/15 16:40
# @Author  : WeiDai
# @FileName: compensate.py
from brownie import network, interface, SoDiamond, Contract, chain, StargateFacet, WithdrawFacet

from scripts.helpful_scripts import get_account, get_stargate_router


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


def withdraw():
    account = get_account()
    withdraw_contract = Contract.from_abi("WithdrawFacet", "0x2967E7Bb9DaA5711Ac332cAF874BD47ef99B3820",
                                          WithdrawFacet.abi)
    withdraw_contract.withdraw("0x0000000000000000000000000000000000000000",
                               "0x3A9788D3E5B644b97A997DC5aC29736C388af9A3",
                               70032067045653004,
                               {"from": account}
                               )
