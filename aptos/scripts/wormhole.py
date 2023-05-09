import functools
import time
from enum import Enum
from typing import List

import aptos_brownie
from brownie import (
    Contract,
    network, web3,
)
from brownie.project.main import Project
from scripts.serde_aptos import get_serde_facet, get_wormhole_facet, get_token_bridge
from scripts.serde_struct import SoData, change_network, hex_str_to_vector_u8, \
    generate_aptos_coin_address_in_wormhole, omniswap_aptos_path, omniswap_ethereum_project, generate_random_bytes32, \
    WormholeData, SwapData, padding_to_bytes

from sui.scripts import sui_project


class AptosSwapType(Enum):
    Liquidswap = "liquidswap"
    Aux = "aux"


class SuiSwapType(Enum):
    OmniswapMock = "OmniswapMock"
    DeepBook = "DeepBook"
    Cetus = "Cetus"


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
    assert path
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


@functools.lru_cache()
def get_sui_token():
    if "tokens" not in sui_project.network_config:
        return {"SUI": {"address": "0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                        "decimal": 8, "name": "SUI",
                        }}

    return sui_project.network_config["tokens"]


def get_dst_wrapped_address_for_aptos(
        package: aptos_brownie.AptosPackage,
        token_name="AptosCoin",
        dst_net=network.show_active()
):
    token_address = generate_aptos_coin_address_in_wormhole(
        get_aptos_token(package)[token_name]["address"])
    token_bridge = get_token_bridge(package, dst_net)
    wrapped_address = token_bridge.wrappedAsset(
        package.network_config["wormhole"]["chainid"], token_address)
    is_wrapped = token_bridge.isWrappedAsset(wrapped_address)
    return token_address, wrapped_address, is_wrapped


def attest_token(
        token_bridge: aptos_brownie.AptosPackage,
        token_name="AptosCoin",
        dst_net=network.show_active()
):
    token_address, wrapped_address, is_wrapped = get_dst_wrapped_address_for_aptos(token_bridge, token_name,
                                                                                   dst_net)
    if not is_wrapped:
        attest_token_address = get_aptos_token(
            token_bridge)[token_name]["address"]
        if token_bridge.network != "aptos-mainnet":
            token_bridge["attest_token::attest_token_entry"](
                ty_args=[attest_token_address])
    return token_address, wrapped_address, is_wrapped


@functools.lru_cache()
def get_aptos_token(package: aptos_brownie.AptosPackage):
    if "token" not in package.network_config:
        return {"AptosCoin": {"address": "0x1::aptos_coin::AptosCoin",
                              "decimal": 8, "name": "AptosCoin",
                              }}
    out = {}
    for t, v in package.network_config["token"].items():
        if "name" in v:
            name = v["name"]
        else:
            name = t
        out[t] = {"address": f"{v['address']}::{v['module']}::{name}",
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


class LiquidswapCurve(Enum):
    Uncorrelated = "Uncorrelated"
    Stable = "Stable"


def get_amounts_out_for_liquidswap(
        package: aptos_brownie.AptosPackage,
        path: list,
        x_amount: int,
        router: AptosSwapType = AptosSwapType.Liquidswap
):
    """
    Unlike solidity, which requires off-chain simulation of on-chain code, manually written.
    Automatic conversion tool:
    1. move-to-ts: https://github.com/hippospace/move-to-ts
    2. move-to-go: https://github.com/Lundalogik/move-to-go

    :param router:
    :param package:
    :param path:
    :param x_amount:
    :return:
    """
    amount_out = 0
    if router == AptosSwapType.Liquidswap:
        resource_addr = package.network_config["replace_address"]["liquidswap_pool_account"]
        for i in range(len(path) - 2):
            x_type = get_aptos_token(package)[path[i]]["address"]
            y_type = get_aptos_token(package)[path[i + 2]]["address"]
            curve_type = get_liquidswap_curve(package, path[i + 1])
            p1 = f'{package.network_config["replace_address"]["liquidswap"]}::liquidity_pool::LiquidityPool<' \
                 f'{x_type},{y_type},{curve_type}>'
            p2 = f'{package.network_config["replace_address"]["liquidswap"]}::liquidity_pool::LiquidityPool<' \
                 f'{y_type},{x_type},{curve_type}>'
            data = package.account_resource(resource_addr, p1)
            if data is None:
                data = package.account_resource(resource_addr, p2)
                x_val = int(data["data"]["coin_y_reserve"]["value"])
                y_val = int(data["data"]["coin_x_reserve"]["value"])
            else:
                x_val = int(data["data"]["coin_x_reserve"]["value"])
                y_val = int(data["data"]["coin_y_reserve"]["value"])
            fee = float(data["data"]["fee"]) / 10000
            x_amount_after_fee = x_amount * (1 - fee)
            amount_out = x_amount_after_fee * y_val / (x_amount_after_fee + x_val)
            x_amount = amount_out
        return amount_out
    else:
        resource_addr = package.network_config["replace_address"]["aux"]
        for i in range(len(path) - 1):
            x_type = get_aptos_token(package)[path[i]]["address"]
            y_type = get_aptos_token(package)[path[i + 1]]["address"]
            p1 = f'{package.network_config["replace_address"]["aux"]}::amm::Pool<' \
                 f'{x_type},{y_type}>'
            p2 = f'{package.network_config["replace_address"]["aux"]}::amm::Pool<' \
                 f'{y_type},{x_type}>'
            data = package.account_resource(resource_addr, p1)
            if data is None:
                data = package.account_resource(resource_addr, p2)
                x_val = int(data["data"]["y_reserve"]["value"])
                y_val = int(data["data"]["x_reserve"]["value"])
            else:
                x_val = int(data["data"]["x_reserve"]["value"])
                y_val = int(data["data"]["y_reserve"]["value"])
            fee = float(data["data"]["fee_bps"]) / 10000
            x_amount_after_fee = x_amount * (1 - fee)
            amount_out = x_amount_after_fee * y_val / (x_amount_after_fee + x_val)
            x_amount = amount_out
        return amount_out


def parse_u256(data):
    output = 0
    output = output + int(data["v3"])
    output = (output << 64) + int(data["v2"])
    output = (output << 64) + int(data["v1"])
    output = (output << 64) + int(data["v0"])
    return output


def estimate_wormhole_fee(
        package: aptos_brownie.AptosPackage,
        dst_chainid: int,
        dst_gas_price: int,
        input_amount: int,
        is_native: bool,
        payload_length: int,
        wormhole_cross_fee: int = 0
):
    """
     wormhole_fee = wormhole_cross_fee + relayer_fee + input_native_amount
    :param dst_gas_price:
    :param dst_chainid:
    :param payload_length:
    :param package:
    :param input_amount:
    :param is_native:
    :param wormhole_cross_fee: wormhole_cross_fee current is 0
    :return:
    """

    RAY = 100000000

    wormhole_fee_resource = package.get_resource_addr(
        str(package.account.account_address), bytes.fromhex(str(dst_chainid).zfill(16)).decode("ascii"))

    input_native_amount = input_amount if is_native else 0
    wormhole_price = package.account_resource(
        wormhole_fee_resource,
        f"{str(package.account.account_address)}::so_fee_wormhole::PriceManager"
    )
    ratio = wormhole_price["data"]["price_data"]["current_price_ratio"]
    base_gas = package.get_table_item(package.network_config["dst_base_gas"]["table_handle"],
                                      package.network_config["dst_base_gas"]["key_type"],
                                      package.network_config["dst_base_gas"]["value_type"],
                                      {"number": str(dst_chainid)})
    base_gas = parse_u256(base_gas)
    gas_per_bytes = package.get_table_item(package.network_config["dst_gas_per_bytes"]["table_handle"],
                                           package.network_config["dst_gas_per_bytes"]["key_type"],
                                           package.network_config["dst_gas_per_bytes"]["value_type"],
                                           {"number": str(dst_chainid)})
    gas_per_bytes = parse_u256(gas_per_bytes)
    estimate_reserve = package.network_config["wormhole"]["estimate_reserve"]

    dst_gas = base_gas + gas_per_bytes * payload_length

    dst_fee = dst_gas * dst_gas_price / 1e10 * int(ratio) / RAY * estimate_reserve / RAY

    # Change into aptos decimal
    dst_fee = dst_fee * 1e8

    return int(dst_fee + wormhole_cross_fee + input_native_amount)


def get_liquidswap_curve(package: aptos_brownie.AptosPackage, curve_name: LiquidswapCurve):
    assert curve_name.value in ["Uncorrelated", "Stable"]
    return f"{package.network_config['replace_address']['liquidswap']}::curves::{curve_name.value}"


def generate_so_data(
        package: aptos_brownie.AptosPackage,
        src_token: str,
        dst_net: str,
        dst_token: str,
        receiver: str,
        amount: int
) -> SoData:
    if "sui" in dst_net:
        receivingAssetId = get_sui_token()[dst_token]["address"].replace("0x", "")
    else:
        receivingAssetId = get_evm_token(package, dst_net)[dst_token]["address"]
    return SoData(
        transactionId=generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=package.config["networks"][package.network]["omnibtc_chainid"],
        sendingAssetId=get_aptos_token(package)[src_token]["address"],
        destinationChainId=package.config["networks"][dst_net]["omnibtc_chainid"],
        receivingAssetId=receivingAssetId,
        amount=amount
    )


def generate_wormhole_data(
        package: aptos_brownie.AptosPackage,
        dst_net: str,
        dst_gas_price: int,
        wormhole_fee: int
) -> WormholeData:
    return WormholeData(
        dstWormholeChainId=package.config["networks"][dst_net]["wormhole"]["chainid"],
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=wormhole_fee,
        dstSoDiamond=package.config["networks"][dst_net]["SoDiamond"]
    )


def generate_src_swap_path(
        package: aptos_brownie.AptosPackage,
        p: list):
    assert len(p) == 3
    return [
        get_aptos_token(package)[p[0]]["address"],
        get_aptos_token(package)[p[2]]["address"],
        get_liquidswap_curve(package, p[1]),
    ]


def generate_src_swap_data(
        package: aptos_brownie.AptosPackage,
        router: AptosSwapType,
        path: list,
        amount: int,
) -> List[SwapData]:
    out = []
    i = 0
    if router == AptosSwapType.Liquidswap:
        while i <= len(path) - 2:
            swap_data = SwapData(
                callTo=package.network_config["replace_address"][router.value],
                approveTo=package.network_config["replace_address"][router.value],
                sendingAssetId=get_aptos_token(package)[path[i]]["address"],
                receivingAssetId=get_aptos_token(package)[path[i + 2]]["address"],
                fromAmount=amount,
                callData=get_liquidswap_curve(package, path[i + 1]) + ",0"
            )
            out.append(swap_data)
            i += 2
    else:
        while i < len(path) - 1:
            swap_data = SwapData(
                callTo=package.network_config["replace_address"][router.value],
                approveTo=package.network_config["replace_address"][router.value],
                sendingAssetId=get_aptos_token(package)[path[i]]["address"],
                receivingAssetId=get_aptos_token(package)[path[i + 1]]["address"],
                fromAmount=amount,
                callData="aux" + ",0"
            )
            out.append(swap_data)
            i += 1
    return out


def generate_dst_eth_swap_data(
        package: aptos_brownie.AptosPackage,
        project: Project,
        dst_net: str,
        router: EvmSwapType,
        func: EvmSwapFunc,
        min_amount: int,
        path: list
) -> List[SwapData]:
    """Evm only test one swap"""
    out = []
    if not path:
        return out

    if router == EvmSwapType.ISwapRouter:
        path_address = encode_path_for_uniswap_v3(package, dst_net, path)
        if func == "exactInput":
            if path[0] == "weth":
                sendingAssetId = evm_zero_address()
            else:
                sendingAssetId = get_evm_token_address(
                    package, dst_net, path[0])
            receivingAssetId = get_evm_token_address(
                package, dst_net, path[-1])
        else:
            raise ValueError("Not support")
    else:
        path_address = encode_path_for_uniswap_v2(package, dst_net, path)
        sendingAssetId = evm_zero_address(
        ) if path[0] == "weth" else path_address[0]
        receivingAssetId = evm_zero_address(
        ) if path[-1] == "weth" else path_address[-1]
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
        fromAmount=0,
        callData=callData
    )
    out.append(swap_data)
    return out


def generate_dst_sui_swap_data(
        router: SuiSwapType,
        path: list,
        min_amount: int,
) -> List[SwapData]:
    out = []
    i = 0

    while i < len(path) - 1:
        if router == SuiSwapType.Cetus:
            token0 = path[i].split("-")[-1]
            token1 = path[i + 1].split("-")[-1]
            if f"Cetus-{token0}-{token1}" in sui_project.network_config['pools']:
                pool_id = sui_project.network_config['pools'][f"Cetus-{token0}-{token1}"]['pool_id']
            elif f"Cetus-{token1}-{token0}" in sui_project.network_config['pools']:
                pool_id = sui_project.network_config['pools'][f"Cetus-{token1}-{token0}"]['pool_id']
            else:
                raise ValueError(f"{token0}, {token1}")
        else:
            raise ValueError(router)

        swap_data = SwapData(
            callTo=pool_id,
            approveTo=pool_id,
            sendingAssetId=get_sui_token()[path[i]]["address"].replace("0x", ""),
            receivingAssetId=get_sui_token()[path[i + 1]]["address"].replace("0x", ""),
            fromAmount=0,
            callData=f"{router.value},{min_amount}",
        )
        out.append(swap_data)
        i += 1
    return out


def corss_swap_to_sui(
        package: aptos_brownie.AptosPackage,
        src_path: list,
        dst_path: list,
        receiver: str,
        input_amount: int,
        dst_gas_price: int = 0,
        dst_router: SuiSwapType = None,
        dst_min_amount: int = 0,
        src_router: AptosSwapType = AptosSwapType.Liquidswap
):
    dst_net = sui_project.network
    # use eth interfaces
    eth_net = network.show_active()
    serde = get_serde_facet(package, eth_net)
    wormhole = get_wormhole_facet(package, eth_net)

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=100000000
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    # construct so data
    so_data = generate_so_data(
        package,
        src_token=src_path[0],
        dst_net=dst_net,
        dst_token=dst_path[-1],
        receiver=receiver,
        amount=input_amount)
    normal_so_data = hex_str_to_vector_u8(
        str(serde.encodeNormalizedSoData(so_data.format_to_contract())))

    # construct src data
    normal_src_swap_data = []
    src_swap_data = []
    if len(src_path) > 1:
        src_swap_data = generate_src_swap_data(
            package, src_router, src_path, input_amount)
        normal_src_swap_data = [d.format_to_contract() for d in src_swap_data]
        normal_src_swap_data = hex_str_to_vector_u8(
            str(serde.encodeNormalizedSwapData(normal_src_swap_data)))

    # construct dst data
    normal_dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_sui_swap_data(
            dst_router,
            dst_path,
            dst_min_amount,
        )
        normal_dst_swap_data = [d.format_to_contract() for d in dst_swap_data]
        normal_dst_swap_data = hex_str_to_vector_u8(
            str(serde.encodeNormalizedSwapData(normal_dst_swap_data)))

    if len(src_swap_data) == 0:
        ty_args = [so_data.sendingAssetId] * 4
    elif len(src_swap_data) == 1:
        ty_args = [src_swap_data[0].sendingAssetId] + \
                  [src_swap_data[0].receivingAssetId] * 3
    elif len(src_swap_data) == 2:
        ty_args = [src_swap_data[0].sendingAssetId, src_swap_data[1].sendingAssetId] + [
            src_swap_data[1].receivingAssetId] * 2
    elif len(src_swap_data) == 3:
        ty_args = [src_swap_data[0].sendingAssetId,
                   src_swap_data[1].sendingAssetId,
                   src_swap_data[2].sendingAssetId,
                   ] + [src_swap_data[2].receivingAssetId]
    else:
        raise ValueError

    payload_length = len(normal_so_data) + \
                     len(normal_wormhole_data) + len(normal_dst_swap_data)

    is_native = src_path[0] == "AptosCoin"
    wormhole_fee = estimate_wormhole_fee(
        package, package.config["networks"][dst_net]["wormhole"]["chainid"], dst_gas_price, input_amount, is_native,
        payload_length, 0)
    print(f"Wormhole fee: {wormhole_fee}")
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=wormhole_fee
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    package["so_diamond::so_swap_via_wormhole"](
        normal_so_data,
        normal_src_swap_data,
        normal_wormhole_data,
        normal_dst_swap_data,
        ty_args=ty_args)


def cross_swap_to_eth(
        package: aptos_brownie.AptosPackage,
        src_path: list,
        dst_path: list,
        receiver: str,
        input_amount: int,
        dst_gas_price: int = 0,
        dst_router: EvmSwapType = None,
        dst_func: EvmSwapFunc = None,
        dst_min_amount: int = 0,
        src_router: AptosSwapType = AptosSwapType.Liquidswap
):
    assert src_path
    assert dst_path
    dst_net = network.show_active()
    serde = get_serde_facet(package, dst_net)
    wormhole = get_wormhole_facet(package, dst_net)

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=100000000
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    # construct so data
    so_data = generate_so_data(
        package,
        src_token=src_path[0],
        dst_net=dst_net,
        dst_token=dst_path[-1],
        receiver=receiver,
        amount=input_amount)
    normal_so_data = hex_str_to_vector_u8(
        str(serde.encodeNormalizedSoData(so_data.format_to_contract())))

    # construct src data
    normal_src_swap_data = []
    src_swap_data = []
    if len(src_path) > 1:
        src_swap_data = generate_src_swap_data(
            package, src_router, src_path, input_amount)
        normal_src_swap_data = [d.format_to_contract() for d in src_swap_data]
        normal_src_swap_data = hex_str_to_vector_u8(
            str(serde.encodeNormalizedSwapData(normal_src_swap_data)))

    # construct dst data
    normal_dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_eth_swap_data(
            package,
            omniswap_ethereum_project,
            dst_net,
            dst_router,
            dst_func,
            dst_min_amount,
            dst_path
        )
        normal_dst_swap_data = [d.format_to_contract() for d in dst_swap_data]
        normal_dst_swap_data = hex_str_to_vector_u8(
            str(serde.encodeNormalizedSwapData(normal_dst_swap_data)))

    if len(src_swap_data) == 0:
        ty_args = [so_data.sendingAssetId] * 4
    elif len(src_swap_data) == 1:
        ty_args = [src_swap_data[0].sendingAssetId] + \
                  [src_swap_data[0].receivingAssetId] * 3
    elif len(src_swap_data) == 2:
        ty_args = [src_swap_data[0].sendingAssetId, src_swap_data[1].sendingAssetId] + [
            src_swap_data[1].receivingAssetId] * 2
    elif len(src_swap_data) == 3:
        ty_args = [src_swap_data[0].sendingAssetId,
                   src_swap_data[1].sendingAssetId,
                   src_swap_data[2].sendingAssetId,
                   ] + [src_swap_data[2].receivingAssetId]
    else:
        raise ValueError

    payload_length = len(normal_so_data) + \
                     len(normal_wormhole_data) + len(normal_dst_swap_data)

    is_native = src_path[0] == "AptosCoin"
    wormhole_fee = estimate_wormhole_fee(
        package, package.config["networks"][dst_net]["wormhole"]["chainid"], dst_gas_price, input_amount, is_native,
        payload_length, 0)
    print(f"Wormhole fee: {wormhole_fee}")
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=wormhole_fee
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    package["so_diamond::so_swap_via_wormhole"](
        normal_so_data,
        normal_src_swap_data,
        normal_wormhole_data,
        normal_dst_swap_data,
        ty_args=ty_args)


def main():
    src_net = "aptos-testnet"
    assert src_net in {"aptos-mainnet", "aptos-devnet", "aptos-testnet"}
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
        try:
            package_mock["setup::add_liquidity"](
                10000000,
                100000000,
                ty_args=generate_src_swap_path(package_mock, ["XBTC", LiquidswapCurve.Uncorrelated, "AptosCoin"]))
            package_mock["setup::add_liquidity"](
                20000 * 1000000000,
                1000000000,
                ty_args=generate_src_swap_path(package_mock, ["USDT", LiquidswapCurve.Uncorrelated, "XBTC"]))
            package_mock["setup::add_liquidity"](
                10000000000,
                10000000000,
                ty_args=generate_src_swap_path(package_mock, ["USDC", LiquidswapCurve.Stable, "USDT"]))
        except:
            pass
        # gas: 9121
        # package_mock["setup::setup_omniswap_enviroment"]()
    # load dst net project
    if "sui" not in dst_net:
        change_network(dst_net)

    ####################################################
    if package.network == "aptos-testnet":
        dst_gas_price = 0

        # gas: 17770
        cross_swap_to_eth(package,
                          src_path=["AptosCoin"],
                          dst_path=["AptosCoin_WORMHOLE"],
                          receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                          input_amount=100000,
                          dst_gas_price=dst_gas_price
                          )

        # gas: 31181
        cross_swap_to_eth(package,
                          src_path=["AptosCoin", LiquidswapCurve.Uncorrelated, "XBTC"],
                          dst_path=["XBTC_WORMHOLE"],
                          receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                          input_amount=10000000,
                          dst_gas_price=dst_gas_price
                          )

        # gas: 46160
        cross_swap_to_eth(package,
                          src_path=["AptosCoin",
                                    LiquidswapCurve.Uncorrelated,
                                    "XBTC",
                                    LiquidswapCurve.Uncorrelated,
                                    "USDT",
                                    ],
                          dst_path=["USDT_WORMHOLE"],
                          receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                          input_amount=10000000,
                          dst_gas_price=dst_gas_price
                          )

        # gas: 313761
        cross_swap_to_eth(package,
                          src_path=["AptosCoin",
                                    LiquidswapCurve.Uncorrelated,
                                    "XBTC",
                                    LiquidswapCurve.Uncorrelated,
                                    "USDT",
                                    LiquidswapCurve.Stable,
                                    "USDC"
                                    ],
                          dst_path=["USDC_WORMHOLE"],
                          receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                          input_amount=10000000,
                          dst_gas_price=dst_gas_price
                          )

        # gas: 35389
        cross_swap_to_eth(
            package,
            src_path=["AptosCoin"],
            dst_path=["AptosCoin_WORMHOLE", "USDT"],
            receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            input_amount=10000000,
            dst_gas_price=dst_gas_price,
            dst_router=EvmSwapType.IUniswapV2Router02,
            dst_func=EvmSwapFunc.swapExactTokensForTokens
        )
    else:
        dst_gas_price = int(30 * 1e9)
        print("estimate out:", get_amounts_out_for_liquidswap(package,
                                                              ["AptosCoin", "USDC_ETH_WORMHOLE"],
                                                              10000000,
                                                              AptosSwapType.Aux))

        if "sui" in dst_net:
            corss_swap_to_sui(
                package,
                src_path=["AptosCoin", "USDC_ETH_WORMHOLE"],
                dst_path=["Wormhole-USDC", "SUI"],
                receiver="0x29b710abd287961d02352a5e34ec5886c63aa5df87a209b2acbdd7c9282e6566",
                input_amount=10000000,
                dst_gas_price=dst_gas_price,
                dst_router=SuiSwapType.Cetus,
                src_router=AptosSwapType.Aux
            )
        else:
            cross_swap_to_eth(
                package,
                src_path=["AptosCoin", "USDC_ETH_WORMHOLE"],
                dst_path=["usdc_eth"],
                receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                input_amount=10000000,
                dst_gas_price=dst_gas_price,
                dst_router=EvmSwapType.IUniswapV2Router02,
                dst_func=EvmSwapFunc.swapExactTokensForTokens,
                src_router=AptosSwapType.Aux
            )
