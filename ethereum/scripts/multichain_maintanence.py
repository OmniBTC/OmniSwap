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
    account = get_account()
    proxy_multichain = Contract.from_abi(
        "MultiChainFacet", SoDiamond[-1], MultiChainFacet.abi
    )

    net = network.show_active()
    print(f"network:{net}, callAnySwapOutByTxHash...")

    txHash = ""
    tx = chain.get_transaction(txHash)

    print(tx.events["BackSourceChain"])

    anyToken = tx.events["BackSourceChain"]["token"]
    receiver = tx.events["BackSourceChain"]["sender"]
    amount = tx.events["BackSourceChain"]["amount"]
    chainId = tx.events["BackSourceChain"]["chainId"]

    if amount > int(0.0062 * 1e18):
        proxy_multichain.anySwapOut(
            anyToken,
            receiver,
            amount,
            chainId,  # fromChainId
            {"from": account},
        )
    else:
        print("less 0.0062 eth")
