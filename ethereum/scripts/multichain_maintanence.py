import json
import os

from brownie import MultiChainFacet, Contract, SoDiamond, network, chain

from scripts.helpful_scripts import get_account


def callAnySwapOut():
    account = get_account()
    proxy_multichain = Contract.from_abi(
        "MultiChainFacet", SoDiamond[-1], MultiChainFacet.abi
    )

    net = network.show_active()
    print(f"network:{net}, callAnySwapOut...")

    proxy_multichain.anySwapOut(
        "0x106a4Cb3Db8aBe4ffF73263dEa55E56770Ce62f3",  # anyWETH
        "0x0e9d66a7008ca39ae759569ad1e911d29547e892",  # receiver
        int(0.007 * 1e18),  # amount
        42161,  # fromChainId
        {"from": account},
    )


def callAnySwapOutByTxHash():
    cmd = "curl --silent https://scanapi.multichain.org/v3/tx/{tx}"
    txs = ["0xcbfb2a0563eb08662324f87f251e72d6a83f56a9e276337e28a00693328fb640"]

    account = get_account()
    proxy_multichain = Contract.from_abi(
        "MultiChainFacet", SoDiamond[-1], MultiChainFacet.abi
    )

    net = network.show_active()
    print(f"network:{net}, callAnySwapOutByTxHash...")

    for src_txid in txs:
        curl_cmd = cmd.replace("{tx}", src_txid)
        with os.popen(curl_cmd) as f:
            result = json.load(f)
            swaptx = result["info"]["swaptx"]
            fromChainID = result["info"]["fromChainID"]

        tx = chain.get_transaction(swaptx)

        print(tx.events["BackSourceChain"])
        print("fromChainID", int(fromChainID))

        anyToken = tx.events["BackSourceChain"]["token"]
        receiver = tx.events["BackSourceChain"]["sender"]
        amount = tx.events["BackSourceChain"]["amount"]

        if amount > int(0.0062 * 1e18):
            proxy_multichain.anySwapOut(
                anyToken,
                receiver,
                amount,
                int(fromChainID),
                {"from": account},
            )
        else:
            print("less 0.0062 eth")
