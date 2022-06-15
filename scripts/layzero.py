# @Time    : 2022/6/15 15:32
# @Author  : WeiDai
# @FileName: layzero.py
from brownie import network, config, Contract, interface, web3
import pandas as pd


# def UltraLightNodeEvents()


def main(file):
    net = network.show_active()
    stargate_router = config["networks"][net]["stargate_router"]
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    bridge_address = stragate.bridge()
    bridge = Contract.from_abi("IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi("ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    print(endpoint.defaultSendLibrary())
    data = pd.read_csv(file)
    for tx in data['Txhash']:
        data = web3.eth.getTransactionReceipt(tx)
        logs = data["logs"]





