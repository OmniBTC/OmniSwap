import base64
import functools
import time
from enum import Enum
from typing import List

import sui_brownie
from brownie import (
    Contract,
    network, web3, )
from brownie.project.main import Project
from sui_brownie import SuiObject

from ethereum.scripts.helpful_scripts import get_account
from scripts import deploy, cetus
from scripts import sui_project
from scripts.deploy import get_coin_metadata
from scripts.relayer.sui import get_signed_vaa_by_wormhole
from scripts.serde_sui import get_serde_facet, get_wormhole_facet, get_token_bridge
from scripts.struct_sui import SoData, change_network, hex_str_to_vector_u8, \
    omniswap_ethereum_project, generate_random_bytes32, \
    WormholeData, SwapData, padding_to_bytes


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


def get_dst_wrapped_address_for_sui(
        token_name="SUI",
        dst_net=network.show_active()
):
    token_address = get_coin_metadata(
        get_sui_token()[token_name]["address"])
    token_bridge = get_token_bridge(dst_net)
    wrapped_address = token_bridge.wrappedAsset(
        sui_project.network_config["wormhole"]["chainid"], token_address)
    is_wrapped = token_bridge.isWrappedAsset(wrapped_address)
    return token_address, wrapped_address, is_wrapped


def create_dst_wrapped_address(sequence: int, dst_net="bsc-test"):
    token_bridge = get_token_bridge(dst_net)
    vaa = get_signed_vaa_by_wormhole(sequence, "sui-testnet")
    vaa_bytes = "0x" + base64.b64decode(vaa['vaaBytes']).hex()
    print(vaa_bytes)
    token_bridge.createWrapped(vaa_bytes, {"from": get_account()})


def complete_dst_swap(sequence: int, dst_net="bsc-test"):
    wormhole_facet = get_wormhole_facet(dst_net)
    vaa = get_signed_vaa_by_wormhole(sequence, "sui-testnet")
    vaa_bytes = "0x" + base64.b64decode(vaa['vaaBytes']).hex()
    wormhole_facet.completeSoSwap(vaa_bytes, {"from": get_account()})


def complete_without_sui_swap(sequence: int, src_net="bsc-test"):
    omniswap = deploy.load_omniswap(True)
    vaa = get_signed_vaa_by_wormhole(sequence, src_net)
    vaa_bytes = "0x" + base64.b64decode(vaa['vaaBytes']).hex()
    storage = sui_project.network_config["objects"]["FacetStorage"]
    token_bridge_state = sui_project.network_config["objects"]["TokenBridgeState"]
    wormhole_state = sui_project.network_config["objects"]["WormholeState"]
    wormhole_fee = sui_project.network_config["objects"]["WormholeFee"]
    clock = sui_project.network_config["objects"]["Clock"]
    omniswap.wormhole_facet.complete_so_swap_without_swap(
        storage,
        token_bridge_state,
        wormhole_state,
        wormhole_fee,
        hex_str_to_vector_u8(vaa_bytes),
        clock,
        type_arguments=[cetus.usdc()]
    )


def complete_with_sui_cetus_swap(sequence: int, src_net="bsc-test"):
    omniswap = deploy.load_omniswap(True)
    vaa = get_signed_vaa_by_wormhole(sequence, src_net)
    vaa_bytes = "0x" + base64.b64decode(vaa['vaaBytes']).hex()
    storage = sui_project.network_config["objects"]["FacetStorage"]
    token_bridge_state = sui_project.network_config["objects"]["TokenBridgeState"]
    wormhole_state = sui_project.network_config["objects"]["WormholeState"]
    wormhole_fee = sui_project.network_config["objects"]["WormholeFee"]
    clock = sui_project.network_config["objects"]["Clock"]
    cetus_pool_id = sui_project.network_config["pools"]["Cetus-USDT-USDC"]['pool_id']
    omniswap.wormhole_facet.complete_so_swap_for_cetus_base_asset(
        storage,
        token_bridge_state,
        wormhole_state,
        wormhole_fee,
        cetus.global_config(),
        cetus_pool_id,
        hex_str_to_vector_u8(vaa_bytes),
        clock,
        type_arguments=[cetus.usdt(), cetus.usdc()]
    )


def attest_token(
        token_bridge: sui_brownie.SuiPackage,
        token_name="SUI",
        dst_net=network.show_active()
):
    token_address, wrapped_address, is_wrapped = get_dst_wrapped_address_for_sui(
        token_name, dst_net)
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
    if "tokens" not in sui_project.network_config:
        return {"SUI": {"address": "0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                        "decimal": 8, "name": "SUI",
                        }}

    return sui_project.network_config["tokens"]


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


def get_token_name(token: str):
    return token.split('::')[-1]


def pool(x_token, y_token):
    return f"Pool<OmniSwapMock, {get_token_name(x_token)}, {get_token_name(y_token)}>"


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
    assert len(data) == 32
    output = 0
    for i in range(32):
        output = (output << 8) + int(data[31 - i])
    return output


def parse_u64(data):
    assert len(data) == 8
    output = 0
    for i in range(8):
        output = (output << 8) + int(data[7 - i])
    return output


def estimate_wormhole_fee(
        omniswap: sui_brownie.SuiPackage,
        so_data: list,
        wormhole_data: list,
        swap_data_dst: list
):
    data = omniswap.wormhole_facet.estimate_relayer_fee.inspect(
        sui_project.network_config['objects']['FacetStorage'],
        sui_project.network_config['objects']['WormholeState'],
        sui_project.network_config['objects']['PriceManager'],
        so_data,
        wormhole_data,
        swap_data_dst
    )["results"][0]["returnValues"]
    src_fee = data[0][0]
    consume_value = data[1][0]
    dst_max_gas = data[2][0]
    return parse_u64(src_fee), parse_u64(consume_value), parse_u256(dst_max_gas)


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
        sourceChainId=sui_project.network_config["omnibtc_chainid"],
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
            callTo=sui_project.network_config['packages']['DeepBook'],
            approveTo=sui_project.network_config['packages']['DeepBook'],
            sendingAssetId=get_sui_token()[path[i]]["address"].replace("0x", ""),
            receivingAssetId=get_sui_token()[path[i + 1]]["address"].replace("0x", ""),
            fromAmount=amount,
            callData=f"{router.value},0",
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


@functools.lru_cache()
def get_deepbook_package_id():
    return sui_project.network_config["packages"]["DeepBook"]


@functools.lru_cache()
def get_cetus_package_id():
    return sui_project.network_config["packages"]["CetusClmm"]


def get_pool_arguments(
        pool_id,
        sending_asset_id,
        receiving_asset_id
):
    sui_type: str = sui_project.client.sui_getObject(pool_id, {
        "showType": True,
        "showOwner": True,
        "showPreviousTransaction": False,
        "showDisplay": False,
        "showContent": False,
        "showBcs": False,
        "showStorageRebate": False
    })["data"]["type"]
    origin_type = SuiObject.from_type(sui_type)
    if origin_type.package_id == get_deepbook_package_id():
        dex_name = SuiSwapType.DeepBook
    elif origin_type.package_id == get_cetus_package_id():
        dex_name = SuiSwapType.Cetus
    else:
        raise ValueError(origin_type.package_id)

    start_index = sui_type.find("<")
    end_index = sui_type.find(",")
    sui_type = SuiObject.from_type(sui_type[start_index:end_index].replace(" ", ""))

    if str(sui_type).replace("0x", "") == sending_asset_id.replace("0x", ""):
        ty_args = [sending_asset_id, receiving_asset_id]
        reverse = False
    else:
        ty_args = [receiving_asset_id, sending_asset_id]
        reverse = True
    return dex_name, ty_args, reverse


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
        src_router: SuiSwapType = SuiSwapType.OmniswapMock,
        src_pool_id=None
):
    dst_net = network.show_active()
    # ethereum facet
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

    (src_fee, wormhole_fee, dst_max_gas) = estimate_wormhole_fee(package, normal_so_data, normal_wormhole_data,
                                                                 normal_dst_swap_data)

    print(f"Wormhole fee: {wormhole_fee}, src_fee:{src_fee}, dst_max_gas:{dst_max_gas}")
    wormhole_data = generate_wormhole_data(
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=wormhole_fee
    )
    normal_wormhole_data = hex_str_to_vector_u8(
        str(wormhole.encodeNormalizedWormholeData(wormhole_data.format_to_contract())))

    wormhole_state = sui_project.network_config["objects"]["WormholeState"]
    token_bridge_state = sui_project.network_config["objects"]["TokenBridgeState"]
    storage = sui_project.network_config["objects"]["FacetStorage"]
    price_manager = sui_project.network_config["objects"]["PriceManager"]
    wormhole_fee_object = sui_project.network_config["objects"]["WormholeFee"]

    # input coin
    x_type = so_data.sendingAssetId
    x_type = x_type if '0x' == x_type[:2] else "0x" + x_type

    # split zero sui coin to pay bridge fee
    if src_path[0] == "SUI":
        result = sui_project.pay_sui([so_data.amount, wormhole_fee])
        coin_x = [result['objectChanges'][-1]['objectId']]
        coin_sui = [result['objectChanges'][-2]['objectId']]
    else:
        result = sui_project.client.suix_getCoins(sui_project.account.account_address, x_type, None, None)
        coin_x = [c["coinObjectId"] for c in result["data"]]
        result = sui_project.pay_sui([wormhole_fee])
        coin_sui = [result['objectChanges'][-1]['objectId']]

    if len(src_swap_data) == 0:
        package.wormhole_facet.so_swap_without_swap(
            wormhole_state,
            token_bridge_state,
            storage,
            clock(),
            price_manager,
            wormhole_fee_object,
            normal_so_data,
            normal_src_swap_data,
            normal_wormhole_data,
            normal_dst_swap_data,
            coin_x,
            coin_sui,
            type_arguments=[x_type],
            gas_budget=1000000000
        )
    elif len(src_swap_data) == 1:
        y_type = src_swap_data[0].receivingAssetId
        y_type = y_type if '0x' == y_type[:2] else "0x" + y_type
        dex_name, ty_args, reverse = get_pool_arguments(
            src_pool_id, x_type, y_type
        )
        if not reverse:
            # x coin is base asset
            if src_router == SuiSwapType.Cetus:
                package.wormhole_facet.so_swap_for_cetus_quote_asset(
                    wormhole_state,
                    token_bridge_state,
                    storage,
                    clock(),
                    price_manager,
                    wormhole_fee_object,
                    cetus.global_config(),
                    src_pool_id,
                    normal_so_data,
                    normal_src_swap_data,
                    normal_wormhole_data,
                    normal_dst_swap_data,
                    coin_x,
                    coin_sui,
                    type_arguments=ty_args,
                    gas_budget=1000000000
                )
            else:
                package.wormhole_facet.so_swap_for_deepbook_quote_asset(
                    wormhole_state,
                    token_bridge_state,
                    storage,
                    clock(),
                    price_manager,
                    wormhole_fee_object,
                    src_pool_id,
                    normal_so_data,
                    normal_src_swap_data,
                    normal_wormhole_data,
                    normal_dst_swap_data,
                    coin_x,
                    coin_sui,
                    type_arguments=ty_args,
                    gas_budget=1000000000
                )
        else:
            # x coin is quote asset
            if src_router == SuiSwapType.Cetus:
                package.wormhole_facet.so_swap_for_cetus_base_asset(
                    wormhole_state,
                    token_bridge_state,
                    storage,
                    clock(),
                    price_manager,
                    wormhole_fee_object,
                    cetus.global_config(),
                    src_pool_id,
                    normal_so_data,
                    normal_src_swap_data,
                    normal_wormhole_data,
                    normal_dst_swap_data,
                    coin_x,
                    coin_sui,
                    type_arguments=ty_args,
                    gas_budget=1000000000
                )
            else:
                package.wormhole_facet.so_swap_for_deepbook_base_asset(
                    wormhole_state,
                    token_bridge_state,
                    storage,
                    clock(),
                    price_manager,
                    wormhole_fee_object,
                    src_pool_id,
                    normal_so_data,
                    normal_src_swap_data,
                    normal_wormhole_data,
                    normal_dst_swap_data,
                    coin_x,
                    coin_sui,
                    type_arguments=ty_args,
                    gas_budget=1000000000
                )
    else:
        raise ValueError


def claim_faucet(coin_type):
    test_coins = deploy.load_test_coins(is_from_config=True)
    test_coins.faucet.claim(
        test_coins.faucet.Faucet[-1],
        type_arguments=[coin_type],
    )


def cross_swap_for_testnet(package):
    dst_gas_price = 4 * 1e9
    cross_swap(package,
               src_path=["Cetus-USDT", "Cetus-USDC"],
               dst_path=["sui-usdc"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=1000000,
               dst_gas_price=dst_gas_price,
               src_router=SuiSwapType.Cetus,
               src_pool_id=sui_project.network_config["pools"]["Cetus-USDT-USDC"]["pool_id"]
               )


def bcross_swap_for_mainnet(package):
    dst_gas_price = 4 * 1e9
    cross_swap(package,
               src_path=["SUI", "Wormhole-USDC"],
               dst_path=["USDC_ETH_WORMHOLE"],
               receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
               input_amount=1000000,
               dst_gas_price=dst_gas_price,
               src_router=SuiSwapType.Cetus,
               src_pool_id=sui_project.network_config["pools"]["Wormhole-USDC-SUI"]["pool_id"]
               )


def main():
    # Prepare environment
    # load src net aptos package
    omniswap = deploy.load_omniswap(is_from_config=True)

    ####################################################
    if sui_project.network in ["sui-testnet", "sui-devnet"]:
        dst_net = "bsc-test"
        # load dst net project
        change_network(dst_net)
        cross_swap_for_testnet(omniswap)
    else:
        dst_net = "polygon-main"
        # load dst net project
        change_network(dst_net)
        cross_swap_for_mainnet(omniswap)


if __name__ == '__main__':
    main()
