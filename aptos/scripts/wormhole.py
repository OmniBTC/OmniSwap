import functools
import time
from enum import Enum

from brownie import (
    Contract,
    network, web3,
)
from brownie.project.main import Project

from scripts.serde import get_serde_facet, get_wormhole_facet
from scripts.struct import SoData, change_network, hex_str_to_vector_u8, \
    generate_aptos_coin_address_in_wormhole, omniswap_aptos_path, omniswap_ethereum_project, generate_random_bytes32, \
    WormholeData, SwapData, padding_to_bytes
from scripts.utils import aptos_brownie


class EvmSwapType(Enum):
    """Interfaces that may be called"""
    IUniswapV2Router02 = "IUniswapV2Router02"
    IUniswapV2Router02AVAX = "IUniswapV2Router02AVAX"
    ISwapRouter = "ISwapRouter"


class EvmSwapFunc(Enum):
    """Swap functions that may be called"""
    swapExactETHForTokens = "swapExactETHForTokens"
    swapExactAVAXForTokens = "swapExactAVAXForTokens"
    swapExactTokensForETH = "swapExactTokensForETH"
    swapExactTokensForAVAX = "swapExactTokensForAVAX"
    swapExactTokensForTokens = "swapExactTokensForTokens"
    exactInput = "exactInput"


def encode_path_for_uniswap_v2(package: aptos_brownie.AptosPackage, dst_net: str, path: list):
    return [get_evm_token_address(package, dst_net, v) for v in path]


def encode_path_for_uniswap_v3(package: aptos_brownie.AptosPackage, dst_net: str, path: list):
    assert len(path) > 0
    assert (len(path) - 3) % 2 == 0, "path length not right"
    uniswap_v3_fee_decimal = 1e6
    path = [
        padding_to_bytes(web3.toHex(
            int(path[i] * uniswap_v3_fee_decimal)), padding="left", length=3).replace("0x", "")
        if (i + 1) % 2 == 0
        else get_evm_token_address(package, dst_net, path[i])
        for i in range(len(path))
    ]
    return "0x" + "".join(path)


def get_dst_wrapped_address_for_aptos(
        package: aptos_brownie.AptosPackage,
        project: Project,
        token_name="AptosCoin",
        dst_net=network.show_active()
):
    token_address = generate_aptos_coin_address_in_wormhole(token_name)
    token_bridge = Contract.from_abi("TokenBridge",
                                     package.config["networks"][dst_net]["wormhole"]["token_bridge"],
                                     project.interface.IWormholeBridge.abi)
    wrapped_address = token_bridge.wrappedAsset(package.network_config["wormhole"]["chainid"], token_address)
    is_wrapped = token_bridge.isWrappedAsset(wrapped_address)
    return token_address, wrapped_address, is_wrapped


@functools.lru_cache()
def get_aptos_token(package: aptos_brownie.AptosPackage):
    out = {"AptosCoin": {"address": "0x1::aptos_coin::AptosCoin",
                         "decimal": 8}}
    if "token" not in package.network_config:
        return out
    for t, v in package.network_config["token"].items():
        out[t] = {"address": f"{v['address']}::{v['module']}::{t}",
                  "decimal": v['decimal']
                  }
    return out


@functools.lru_cache()
def get_evm_token(package: aptos_brownie.AptosPackage, dst_net: str):
    if dst_net not in package.config["networks"] or "token" not in package.config["networks"][dst_net]:
        return {}
    out = {}
    for t, v in package.config["networks"][dst_net]["token"].items():
        out[t] = {"address": v["address"],
                  "decimal": v["decimal"]
                  }
    return out


def evm_zero_address():
    return "0x" + "0" * 40


@functools.lru_cache()
def get_evm_token_address(package: aptos_brownie.AptosPackage, dst_net: str, token_name: str):
    result = get_evm_token(package, dst_net)
    if token_name.lower() == "eth":
        return evm_zero_address()
    else:
        return result[token_name]["address"]


def get_liquidswap_curve(package: aptos_brownie.AptosPackage, curve_name):
    assert curve_name in ["Uncorrelated", "Stable"]
    return f"{package.network_config['replace_address']['liquidswap']}::curves::{curve_name}"


def generate_so_data(
        package: aptos_brownie.AptosPackage,
        src_token: str,
        dst_net: str,
        dst_token: str,
        receiver: str,
        amount: int
) -> SoData:
    so_data = SoData(
        transactionId=generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=package.config["networks"][package.network]["omnibtc_chainid"],
        sendingAssetId=get_aptos_token(package)[src_token]["address"],
        destinationChainId=package.config["networks"][dst_net]["omnibtc_chainid"],
        receivingAssetId=get_evm_token(package, dst_net)[dst_token]["address"],
        amount=amount
    )
    return so_data


def generate_wormhole_data(
        package: aptos_brownie.AptosPackage,
        dst_net: str,
        dst_gas_price: int,
        wormhole_fee: int
) -> WormholeData:
    wormhole_data = WormholeData(
        dstWormholeChainId=package.config["networks"][dst_net]["wormhole"]["chainid"],
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=wormhole_fee,
        dstSoDiamond=package.config["networks"][dst_net]["SoDiamond"]
    )
    return wormhole_data


def generate_src_swap_data(
        package: aptos_brownie.AptosPackage,
        router: str,
        path: list,
        amount: int,
):
    out = []
    i = 0
    while i <= len(path) - 2:
        swap_data = SwapData(
            callTo=package.network_config["replace_address"][router],
            approveTo=package.network_config["replace_address"][router],
            sendingAssetId=get_aptos_token(package)[path[i]],
            receivingAssetId=get_aptos_token(package)[path[i + 2]],
            fromAmount=amount,
            callData=get_liquidswap_curve(package, path[i + 1])
        )
        out.append(swap_data)
        i += 2
    return out


def generate_dst_swap_data(
        package: aptos_brownie.AptosPackage,
        project: Project,
        dst_net: str,
        router: EvmSwapType,
        func: EvmSwapFunc,
        min_amount: int,
        path: list
):
    """Evm only test one swap"""
    out = []
    if len(path) == 0:
        return out

    if router == EvmSwapType.ISwapRouter:
        path_address = encode_path_for_uniswap_v3(package, dst_net, path)
        if func == "exactInput":
            if path[0] == "weth":
                sendingAssetId = evm_zero_address()
            else:
                sendingAssetId = get_evm_token_address(package, dst_net, path[0])
            receivingAssetId = get_evm_token_address(package, dst_net, path[-1])
        else:
            raise ValueError("Not support")
    else:
        path_address = encode_path_for_uniswap_v2(package, dst_net, path)
        if path[0] == "weth":
            sendingAssetId = evm_zero_address()
        else:
            sendingAssetId = path[0]
        if path[-1] == "weth":
            receivingAssetId = evm_zero_address()
        else:
            receivingAssetId = path[-1]

    swap_contract = Contract.from_abi(
        router.value,
        package.config["networks"][dst_net]["swap"][router.value]["router"],
        getattr(project.interface, router.value).abi)

    fromAmount = 0
    if func in [EvmSwapFunc.swapExactTokensForETH, EvmSwapFunc.swapExactTokensForAVAX,
                EvmSwapFunc.swapExactTokensForTokens]:
        callData = getattr(swap_contract, func.value).encode_input(
            fromAmount,
            min_amount,
            path_address,
            package.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    elif func == EvmSwapFunc.exactInput:
        callData = getattr(swap_contract, func.value).encode_input([
            path_address,
            package.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000),
            fromAmount,
            min_amount]
        )
    elif func in [EvmSwapFunc.swapExactETHForTokens, EvmSwapFunc.swapExactAVAXForTokens]:
        callData = getattr(swap_contract, func.value).encode_input(
            min_amount,
            path_address,
            package.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    else:
        raise ValueError("Not support")

    swap_data = SwapData(
        callTo=package.config["networks"][dst_net]["swap"][router.value]["router"],
        approveTo=package.config["networks"][dst_net]["swap"][router.value]["router"],
        sendingAssetId=sendingAssetId,
        receivingAssetId=receivingAssetId,
        fromAmount=project,
        callData=callData
    )
    out.append(swap_data)
    return out


def main():
    src_net = "aptos-testnet"
    assert src_net in ["aptos-mainnet", "aptos-devnet", "aptos-testnet"]
    dst_net = "bsc-test"

    # Prepare environment
    # load src net aptos package
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=src_net
    )

    if "test" in src_net and "test" in dst_net:
        package_mock = aptos_brownie.AptosPackage(
            project_path=omniswap_aptos_path,
            network=src_net,
            package_path=omniswap_aptos_path.joinpath("mocks")
        )
        package_mock["setup::setup_omniswap_enviroment"]()

    # load dst net project
    change_network(dst_net)

    ####################################################

    # load serde related facet
    serde = get_serde_facet(package, dst_net)
    wormhole = get_wormhole_facet(package, dst_net)

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=0,
        wormhole_fee=100000000
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    # construct so data
    so_data = generate_so_data(
        package,
        src_token="AptosCoin",
        dst_net=dst_net,
        dst_token="USDT",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        amount=100000000)
    normal_so_data = hex_str_to_vector_u8(str(serde.encodeNormalizedSoData(so_data.format_to_contract())))

    # construct src data
    src_swap_data = []

    # construct dst data
    dst_swap_data = []
    aptos_str = "0x1::aptos_coin::AptosCoin"
    package["wormhole_facet::attest_token"](ty_args=[aptos_str])
    package["so_diamond::so_swap_via_wormhole"](
        normal_so_data,
        src_swap_data,
        normal_wormhole_data,
        dst_swap_data,
        ty_args=[aptos_str, aptos_str, aptos_str, aptos_str])
