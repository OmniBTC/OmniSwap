from brownie import network, config, Contract, interface, SoDiamond


def main():
    net = network.show_active()
    try:
        addr = SoDiamond[-1].address
    except:
        addr = ""
    print(f"network:{net}, SoDiamond: {addr}")
    stargate_router = config["networks"][net]["stargate_router"]
    print(f"stragate router: {stargate_router}")
    stragate = Contract.from_abi("IStargate", stargate_router, interface.IStargate.abi)
    bridge_address = stragate.bridge()
    print(f"bridge: {bridge_address}")
    bridge = Contract.from_abi("IStargateBridge", bridge_address, interface.IStargateBridge.abi)
    endpoint_address = bridge.layerZeroEndpoint()
    endpoint = Contract.from_abi("ILayerZeroEndpoint", endpoint_address, interface.ILayerZeroEndpoint.abi)
    print(f"endpoint: {endpoint_address}")
    ultra_light_node_address = endpoint.defaultSendLibrary()
    print("ultra_light_node_address", ultra_light_node_address)
    ultra_light_node = Contract.from_abi("ILayerZeroUltraLightNodeV1", ultra_light_node_address,
                                         interface.ILayerZeroUltraLightNodeV1.abi)
    src_net = "bsc-main"
    app_config = ultra_light_node.getAppConfig(config["networks"][src_net]["stargate_chainid"],
                                               config["networks"][src_net]["stargate_bridge"]
                                               )
    print("app config", app_config)
