
from brownie import network, config, Contract, interface


def main():
    net = network.show_active()
    stargate_router = config["networks"][net]["stargate_router"]
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    bridge_address = stragate.bridge()
    bridge = Contract.from_abi("IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi("ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    ultra_light_node_address = endpoint.defaultSendLibrary()
    print("ultra_light_node_address", ultra_light_node_address)
    Contract.from_abi("ILayerZeroUltraLightNodeV1", ultra_light_node_address,
                      interface.ILayerZeroUltraLightNodeV1.abi)
