import sui_brownie
from sui_brownie import SuiObject

from scripts import sui_project
from scripts.struct import SoData, change_network, hex_str_to_vector_u8, \
    generate_aptos_coin_address_in_wormhole, omniswap_sui_path, omniswap_ethereum_project, generate_random_bytes32, \
    WormholeData, SwapData, padding_to_bytes
from scripts.serde_sui import get_serde_facet, get_wormhole_facet, get_token_bridge
import functools
import time
from enum import Enum
from typing import List

from brownie import (
    Contract,
    network, web3,
)
from brownie.project.main import Project


class SuiSwapType(Enum):
    OmniswapMock = "OmniswapMock"


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


def encode_path_for_uniswap_v2(dst_net: str, path: list):
    return [get_evm_token_address(dst_net, v) for v in path]


def encode_path_for_uniswap_v3(dst_net: str, path: list):
    assert path
    assert (len(path) - 3) % 2 == 0, "path length not right"
    uniswap_v3_fee_decimal = 1e6
    path = [
        padding_to_bytes(web3.toHex(
            int(path[i] * uniswap_v3_fee_decimal)), padding="left", length=3).replace("0x", "")
        if (i + 1) % 2 == 0
        else get_evm_token_address(dst_net, path[i])
        for i in range(len(path))
    ]
    return "0x" + "".join(path)


def get_dst_wrapped_address_for_aptos(
        token_name="SUI",
        dst_net=network.show_active()
):
    token_address = generate_aptos_coin_address_in_wormhole(
        get_sui_token()[token_name]["address"])
    token_bridge = get_token_bridge(dst_net)
    wrapped_address = token_bridge.wrappedAsset(
        sui_project.network_config["wormhole"]["chainid"], token_address)
    is_wrapped = token_bridge.isWrappedAsset(wrapped_address)
    return token_address, wrapped_address, is_wrapped


def attest_token(
        token_bridge: sui_brownie.SuiPackage,
        token_name="SUI",
        dst_net=network.show_active()
):
    token_address, wrapped_address, is_wrapped = get_dst_wrapped_address_for_aptos(token_bridge, token_name,
                                                                                   dst_net)
    if not is_wrapped:
        attest_token_address = get_sui_token()
        if token_bridge.network != "sui-mainnet":
            result = sui_project.pay_sui([0])
            zero_coin = result['objectChanges'][-1]['objectId']
            # todo: find coin_metadata
            coin_metadata = ""
            token_bridge.attest_token.attest_token(
                sui_project.config["networks"]["token_bridge_state"],
                sui_project.config["networks"]["wormhole_state"],
                zero_coin,
                coin_metadata,
                0,
                clock()
            )
            token_bridge["attest_token::attest_token_entry"](
                ty_args=[attest_token_address])
    return token_address, wrapped_address, is_wrapped


@functools.lru_cache()
def get_sui_token():
    if "token" not in sui_project.network_config:
        return {"SUI": {"address": "0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                        "decimal": 8, "name": "SUI",
                        }}
    out = {}
    for t, v in sui_project.network_config["token"].items():
        if "name" in v:
            name = v["name"]
        else:
            name = t
        out[t] = {"address": f"{v['address']}::{v['module']}::{name}",
                  "decimal": v['decimal']
                  }
    return out


@functools.lru_cache()
def get_evm_token(dst_net: str):
    if dst_net not in sui_project.config["networks"] or "token" not in sui_project.config["networks"][dst_net]:
        return {}
    return {
        t: {"address": v["address"], "decimal": v["decimal"]}
        for t, v in sui_project.config["networks"][dst_net]["token"].items()
    }


def evm_zero_address():
    return "0x" + "0" * 40


@functools.lru_cache()
def get_evm_token_address(dst_net: str, token_name: str):
    result = get_evm_token(dst_net)
    if token_name.lower() == "eth":
        return evm_zero_address()
    else:
        return result[token_name]["address"]


class LiquidswapCurve(Enum):
    Uncorrelated = "Uncorrelated"
    Stable = "Stable"


def pool(x_type, y_type):
    return f"{sui_project.OmniSwapMock[-1]}::pool::Pool<{sui_project.OmniSwapMock[-1]}::setup::OmniSwapMock,{x_type},{y_type}>"


def clock():
    return "0x0000000000000000000000000000000000000000000000000000000000000006"


def coin(coin_type):
    return f"0x2::coin::Coin<{coin_type}>"


def sui():
    return "0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI"


def get_amounts_out(
        package: sui_brownie.SuiPackage,
        path: list,
        x_amount: int,
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
    for i in range(len(path) - 2):
        x_type = get_sui_token()[path[i]]["address"]
        y_type = get_sui_token()[path[i + 1]]["address"]
        pool_address = sui_project[SuiObject.from_type(pool(x_type, y_type))][-1]
        (x_val, y_val, _) = package.pool.get_amounts.inspect(pool_address)
        fee = 3 / 1000
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
        package: sui_brownie.SuiPackage,
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
    ray = 100000000

    input_native_amount = input_amount if is_native else 0
    ratio = package.so_fee_wormhole.get_price_ratio.inspect(
        package.so_fee_wormhole.PriceManager[-1],
        dst_chainid
    )
    (base_gas, gas_per_bytes) = package.womrhole_facet.get_dst_gas.inspect(
        package.wormhole_facet.Storage[-1],
        dst_chainid
    )
    estimate_reserve = package.network_config["wormhole"]["estimate_reserve"]

    dst_gas = base_gas + gas_per_bytes * payload_length

    dst_fee = dst_gas * dst_gas_price / 1e10 * int(ratio) / ray * estimate_reserve / ray

    # Change into aptos decimal
    dst_fee = dst_fee * 1e8

    return int(dst_fee + wormhole_cross_fee + input_native_amount)


def generate_so_data(
        src_token: str,
        dst_net: str,
        dst_token: str,
        receiver: str,
        amount: int
) -> SoData:
    return SoData(
        transactionId=generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=sui_project.config["networks"][sui_project.network]["omnibtc_chainid"],
        sendingAssetId=get_sui_token()[src_token]["address"],
        destinationChainId=sui_project.config["networks"][dst_net]["omnibtc_chainid"],
        receivingAssetId=get_evm_token(dst_net)[dst_token]["address"],
        amount=amount
    )


def generate_wormhole_data(
        dst_net: str,
        dst_gas_price: int,
        wormhole_fee: int
) -> WormholeData:
    return WormholeData(
        dstWormholeChainId=sui_project.config["networks"][dst_net]["wormhole"]["chainid"],
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=wormhole_fee,
        dstSoDiamond=sui_project.config["networks"][dst_net]["SoDiamond"]
    )


def generate_src_swap_path(p: list):
    return [
        get_sui_token()[p[0]]["address"],
        get_sui_token()[p[1]]["address"],
    ]


def generate_src_swap_data(
        router: SuiSwapType,
        path: list,
        amount: int,
) -> List[SwapData]:
    out = []
    i = 0

    while i < len(path) - 1:
        swap_data = SwapData(
            callTo=sui_project.network_config["replace_address"][router.value],
            approveTo=sui_project.network_config["replace_address"][router.value],
            sendingAssetId=get_sui_token()[path[i]]["address"],
            receivingAssetId=get_sui_token()[path[i + 1]]["address"],
            fromAmount=amount,
            callData="OmniswapMock" + ",0"
        )
        out.append(swap_data)
        i += 1
    return out


def generate_dst_swap_data(
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
        path_address = encode_path_for_uniswap_v3(dst_net, path)
        if func != "exactInput":
            raise ValueError("Not support")
        sendingAssetId = (
            evm_zero_address()
            if path[0] == "weth"
            else get_evm_token_address(dst_net, path[0])
        )
        receivingAssetId = get_evm_token_address(
            dst_net, path[-1])
    else:
        path_address = encode_path_for_uniswap_v2(dst_net, path)
        sendingAssetId = evm_zero_address(
        ) if path[0] == "weth" else path_address[0]
        receivingAssetId = evm_zero_address(
        ) if path[-1] == "weth" else path_address[-1]
    swap_contract = Contract.from_abi(
        router.value,
        sui_project.config["networks"][dst_net]["swap"][router.value]["router"],
        getattr(project.interface, router.value).abi)

    fromAmount = 0
    if func in [EvmSwapFunc.swapExactTokensForETH, EvmSwapFunc.swapExactTokensForAVAX,
                EvmSwapFunc.swapExactTokensForTokens]:
        callData = getattr(swap_contract, func.value).encode_input(
            fromAmount,
            min_amount,
            path_address,
            sui_project.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    elif func == EvmSwapFunc.exactInput:
        callData = getattr(swap_contract, func.value).encode_input([
            path_address,
            sui_project.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000),
            fromAmount,
            min_amount]
        )
    elif func in [EvmSwapFunc.swapExactETHForTokens, EvmSwapFunc.swapExactAVAXForTokens]:
        callData = getattr(swap_contract, func.value).encode_input(
            min_amount,
            path_address,
            sui_project.config["networks"][dst_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    else:
        raise ValueError("Not support")

    swap_data = SwapData(
        callTo=sui_project.config["networks"][dst_net]["swap"][router.value]["router"],
        approveTo=sui_project.config["networks"][dst_net]["swap"][router.value]["router"],
        sendingAssetId=sendingAssetId,
        receivingAssetId=receivingAssetId,
        fromAmount=0,
        callData=callData
    )
    out.append(swap_data)
    return out


def cross_swap(
        package: sui_brownie.SuiPackage,
        src_path: list,
        dst_path: list,
        receiver: str,
        input_amount: int,
        dst_gas_price: int = 0,
        dst_router: EvmSwapType = None,
        dst_func: EvmSwapFunc = None,
        dst_min_amount: int = 0,
        src_router: SuiSwapType = SuiSwapType.OmniswapMock
):
    dst_net = network.show_active()
    serde = get_serde_facet(dst_net)
    wormhole = get_wormhole_facet(dst_net)

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=100000000
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    # construct so data
    so_data = generate_so_data(
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
            src_router, src_path, input_amount)
        normal_src_swap_data = [d.format_to_contract() for d in src_swap_data]
        normal_src_swap_data = hex_str_to_vector_u8(
            str(serde.encodeNormalizedSwapData(normal_src_swap_data)))

    # construct dst data
    normal_dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_swap_data(
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
        x_type = y_type = z_type = m_type = ty_args[0]
    elif len(src_swap_data) == 1:
        ty_args = [src_swap_data[0].sendingAssetId] + \
                  [src_swap_data[0].receivingAssetId] * 3
        x_type = ty_args[0]
        y_type = z_type = m_type = ty_args[1]
    elif len(src_swap_data) == 2:
        ty_args = [src_swap_data[0].sendingAssetId, src_swap_data[1].sendingAssetId] + [
            src_swap_data[1].receivingAssetId] * 2
        x_type = ty_args[0]
        y_type = ty_args[1]
        z_type = m_type = ty_args[2]
    elif len(src_swap_data) == 3:
        ty_args = [src_swap_data[0].sendingAssetId,
                   src_swap_data[1].sendingAssetId,
                   src_swap_data[2].sendingAssetId,
                   ] + [src_swap_data[2].receivingAssetId]
        x_type = ty_args[0]
        y_type = ty_args[1]
        z_type = ty_args[2]
        m_type = ty_args[3]
    else:
        raise ValueError

    payload_length = len(normal_so_data) + len(normal_wormhole_data) + len(normal_dst_swap_data)

    is_native = src_path[0] == "SuiCoin"
    wormhole_fee = estimate_wormhole_fee(
        package, sui_project.config["networks"][dst_net]["wormhole"]["chainid"], dst_gas_price, input_amount, is_native,
        payload_length, 0)
    print(f"Wormhole fee: {wormhole_fee}")
    wormhole_data = generate_wormhole_data(
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=wormhole_fee
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    wormhole_state = sui_project.config["networks"]["wormhole_state"]
    token_bridge_state = sui_project.config["networks"]["token_bridge_state"]
    storage = package.wormhole_facet.Storage[-1]
    price_manager = package.so_fee_manager.PriceManager[-1]
    wormhole_fee = package.wormhole_facet.WormholeFee[-1]
    pool_xy = pool(x_type, y_type)
    pool_yz = pool(y_type, z_type)
    pool_zm = pool(z_type, m_type)
    coin_x = [sui_project[SuiObject.from_type(
        coin(f"0x{x_type}"))][-1]]
    coin_sui = sui_project.get_account_sui().keys()
    package.so_diamond.so_swap_via_wormhole(
        wormhole_state,
        token_bridge_state,
        storage,
        clock(),
        price_manager,
        wormhole_fee,
        pool_xy,
        pool_yz,
        pool_zm,
        normal_so_data,
        normal_src_swap_data,
        normal_wormhole_data,
        normal_wormhole_data,
        coin_x,
        coin_sui,
        type_argument=ty_args,
    )


def cross_swap_for_testnet(package):
    dst_gas_price = 0

    # gas: 17770
    cross_swap(package,
               src_path=["AptosCoin"],
               dst_path=["AptosCoin_WORMHOLE"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=100000,
               dst_gas_price=dst_gas_price
               )

    # gas: 31181
    cross_swap(package,
               src_path=["AptosCoin", "XBTC"],
               dst_path=["XBTC_WORMHOLE"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=10000000,
               dst_gas_price=dst_gas_price
               )

    # gas: 46160
    cross_swap(package,
               src_path=["AptosCoin",
                         "XBTC",
                         "USDT",
                         ],
               dst_path=["USDT_WORMHOLE"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=10000000,
               dst_gas_price=dst_gas_price
               )

    # gas: 313761
    cross_swap(package,
               src_path=["AptosCoin",
                         "XBTC",
                         "USDT",
                         "USDC"
                         ],
               dst_path=["USDC_WORMHOLE"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=10000000,
               dst_gas_price=dst_gas_price
               )

    # gas: 35389
    cross_swap(
        package,
        src_path=["AptosCoin"],
        dst_path=["AptosCoin_WORMHOLE", "USDT"],
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        input_amount=10000000,
        dst_gas_price=dst_gas_price,
        dst_router=EvmSwapType.IUniswapV2Router02,
        dst_func=EvmSwapFunc.swapExactTokensForTokens
    )


def main():
    src_net = "sui-testnet"
    dst_net = "bsc-test"

    # Prepare environment
    # load src net aptos package
    package = sui_brownie.SuiPackage(
        package_path=omniswap_sui_path
    )

    if "test" in src_net and "test" in dst_net:
        package_mock = sui_brownie.SuiPackage(
            package_path=omniswap_sui_path.joinpath("mocks"),
        )
        package_mock.setup.setup_pool(
            package_mock.faucet.Faucet[-1]
        )
        # gas: 9121
        # package_mock["setup::setup_omniswap_enviroment"]()
    # load dst net project
    change_network(dst_net)

    ####################################################
    if package.network in ["sui-testnet", "sui-devnet"]:
        cross_swap_for_testnet(package)
    else:
        dst_gas_price = 30 * 1e9
        print("estimate out:", get_amounts_out(package, ["AptosCoin", "USDC_ETH_WORMHOLE"],
                                               10000000))
        cross_swap(
            package,
            src_path=["AptosCoin", "USDC_ETH_WORMHOLE"],
            dst_path=["usdc_eth"],
            receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            input_amount=10000000,
            dst_gas_price=int(dst_gas_price),
            dst_router=EvmSwapType.IUniswapV2Router02,
            dst_func=EvmSwapFunc.swapExactTokensForTokens,
            src_router=SuiSwapType.OmniswapMock
        )
