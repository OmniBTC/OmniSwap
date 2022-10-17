from brownie import (
    Contract,
    network,
    project,
)
from brownie.project.main import Project

from scripts.serde import get_serde_facet, get_wormhole_facet
from scripts.struct import SoData, to_hex_str, change_network, hex_str_to_vector_u8, \
    generate_aptos_coin_address_in_wormhole, omniswap_aptos_path, omniswap_ethereum_project
from scripts.utils import aptos_brownie


def get_dst_wrapped_address_for_aptos(
        package: aptos_brownie.AptosPackage,
        omniswap_ethereum_project: Project,
        token_name="APT",
        dst_net=network.show_active()
):
    token_address = generate_aptos_coin_address_in_wormhole(token_name)
    token_bridge = Contract.from_abi("TokenBridge",
                                     package.config["networks"][dst_net]["wormhole"]["token_bridge"],
                                     omniswap_ethereum_project.interface.IWormholeBridge.abi)
    wrapped_address = token_bridge.wrappedAsset(package.network_config["wormhole"]["chainid"], token_address)
    is_wrapped = token_bridge.isWrappedAsset(wrapped_address)
    return token_address, wrapped_address, is_wrapped


def main():
    src_net = "aptos-testnet"
    assert src_net in ["aptos-mainnet", "aptos-devnet", "aptos-testnet"]
    dst_net = "bsc-test"

    # load src net aptos package
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=src_net
    )

    # load dst net project
    change_network(dst_net)

    # cross token info
    token_name = "APT"
    (token_address, wrapped_address, is_wrapped) = get_dst_wrapped_address_for_aptos(
        package, omniswap_ethereum_project, token_name, dst_net)
    print(f"{token_name} aptos source address: {token_address}, "
          f"dst {dst_net} address: {wrapped_address}, wrapped {is_wrapped}")

    # load facet
    serde = get_serde_facet(package, dst_net)
    wormhole = get_wormhole_facet(package, dst_net)

    # construct data
    wormhole_data = [4, 1, 100000000, "0x379838Ab3cab29F5BdA0FFD62547c90E8AeB6Ecc"]
    normal_wormhole_data = hex_str_to_vector_u8(str(wormhole.encodeNormalizedWormholeData(wormhole_data)))
    so_data = SoData(
        transactionId="0x4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        sourceChainId=22,
        sendingAssetId=to_hex_str("0x1::aptos_coin::AptosCoin"),
        destinationChainId=4,
        receivingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        amount=100000000
    )
    normal_so_data = hex_str_to_vector_u8(str(serde.encodeNormalizedSoData(so_data.format_to_contract())))
    src_swap_data = []
    dst_swap_data = []
    aptos_str = "0x1::aptos_coin::AptosCoin"
    package["wormhole_facet::attest_token"](ty_args=[aptos_str])
    package["so_diamond::so_swap_via_wormhole"](
        normal_so_data,
        src_swap_data,
        normal_wormhole_data,
        dst_swap_data,
        ty_args=[aptos_str, aptos_str, aptos_str, aptos_str])
