import functools
import json
from pprint import pprint
import time
from enum import Enum
from pathlib import Path
from typing import List

import requests
from brownie import network, Contract, project, config, SoDiamond, WormholeFacet

from scripts.helpful_scripts import (
    to_hex_str,
    get_token_address,
    zero_address,
    change_network,
    get_account,
    padding_to_bytes,
)
from scripts.swap import SwapType, SwapFunc, View, SwapData, SoData
import aptos_brownie

omniswap_ethereum_path = Path(__file__).parent.parent
omniswap_ethereum_project = project.load(
    str(omniswap_ethereum_path), raise_if_loaded=False
)

omniswap_aptos_path = Path(__file__).parent.parent.parent.joinpath("aptos")


@functools.lru_cache()
def get_aptos_token(package: aptos_brownie.AptosPackage):
    out = {"AptosCoin": {"address": "0x1::aptos_coin::AptosCoin", "decimal": 8}}
    if "token" not in package.network_config:
        return out
    for t, v in package.network_config["token"].items():
        out[t] = {
            "address": f"{v['address']}::{v['module']}::{t}",
            "decimal": v["decimal"],
        }
    return out


class WormholeData(View):
    """Constructing wormhole data"""

    def __init__(
        self,
        dstWormholeChainId,
        dstMaxGasPriceInWeiForRelayer,
        wormholeFee,
        dstSoDiamond,
    ):
        self.dstWormholeChainId = dstWormholeChainId
        self.dstMaxGasPriceInWeiForRelayer = dstMaxGasPriceInWeiForRelayer
        self.wormholeFee = wormholeFee
        self.dstSoDiamond = dstSoDiamond

    def format_to_contract(self):
        """Returns the data used to pass into the contract interface"""
        return [
            self.dstWormholeChainId,
            self.dstMaxGasPriceInWeiForRelayer,
            self.wormholeFee,
            to_hex_str(self.dstSoDiamond),
        ]


get_evm_token_address = get_token_address


def generate_so_data(
    package: aptos_brownie.AptosPackage,
    src_token: str,
    src_net: str,
    dst_token: str,
    receiver: str,
    amount: int,
) -> SoData:
    so_data = SoData(
        transactionId=SoData.generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=package.config["networks"][src_net]["omnibtc_chainid"],
        sendingAssetId=get_evm_token_address(src_token),
        destinationChainId=package.config["networks"][package.network][
            "omnibtc_chainid"
        ],
        receivingAssetId=get_aptos_token(package)[dst_token]["address"],
        amount=amount,
    )
    return so_data


def generate_wormhole_data(
    package: aptos_brownie.AptosPackage,
    dst_net: str,
    dst_gas_price: int,
    wormhole_fee: int,
    dst_so_diamond: str,
) -> WormholeData:
    wormhole_data = WormholeData(
        dstWormholeChainId=package.config["networks"][dst_net]["wormhole"]["chainid"],
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=wormhole_fee,
        dstSoDiamond=dst_so_diamond,
    )
    return wormhole_data


class LiquidswapCurve(Enum):
    Uncorrelated = "Uncorrelated"
    Stable = "Stable"


def get_liquidswap_curve(
    package: aptos_brownie.AptosPackage, curve_name: LiquidswapCurve
):
    assert curve_name.value in ["Uncorrelated", "Stable"]
    return f"{package.network_config['replace_address']['liquidswap']}::curves::{curve_name.value}"


def generate_dst_swap_data(
    package: aptos_brownie.AptosPackage,
    router: str,
    path: list,
    amount: int,
) -> List[SwapData]:
    out = []
    i = 0
    while i <= len(path) - 2:
        swap_data = SwapData(
            callTo=package.network_config["replace_address"][router],
            approveTo=package.network_config["replace_address"][router],
            sendingAssetId=get_aptos_token(package)[path[i]]["address"],
            receivingAssetId=get_aptos_token(package)[path[i + 2]]["address"],
            fromAmount=amount,
            callData=get_liquidswap_curve(package, path[i + 1]),
        )
        out.append(swap_data)
        i += 2
    return out


evm_zero_address = zero_address


def generate_src_swap_data(
    package: aptos_brownie.AptosPackage,
    src_net: str,
    router: str,
    func: str,
    input_amount: int,
    min_amount: int,
    path: list,
) -> List[SwapData]:
    """Evm only test one swap"""
    out = []
    if len(path) == 0:
        return out

    if router == SwapType.ISwapRouter:
        path_address = SwapData.encode_path_for_uniswap_v3(path)
        if func == "exactInput":
            if path[0] == "weth":
                sendingAssetId = evm_zero_address()
            else:
                sendingAssetId = get_evm_token_address(path[0])
            receivingAssetId = get_evm_token_address(path[-1])
        else:
            raise ValueError("Not support")
    else:
        path_address = SwapData.encode_path_for_uniswap_v2(path)
        if path[0] == "weth":
            sendingAssetId = evm_zero_address()
        else:
            sendingAssetId = get_evm_token_address(path[0])
        if path[-1] == "weth":
            receivingAssetId = evm_zero_address()
        else:
            receivingAssetId = get_evm_token_address(path[-1])

    swap_contract = Contract.from_abi(
        router,
        package.config["networks"][src_net]["swap"][router]["router"],
        getattr(omniswap_ethereum_project.interface, router).abi,
    )

    fromAmount = input_amount
    if func in [
        SwapFunc.swapExactTokensForETH,
        SwapFunc.swapExactTokensForAVAX,
        SwapFunc.swapExactTokensForTokens,
    ]:
        callData = getattr(swap_contract, func).encode_input(
            fromAmount,
            min_amount,
            path_address,
            package.config["networks"][src_net]["SoDiamond"],
            int(time.time() + 3000),
        )
    elif func == SwapFunc.exactInput:
        callData = getattr(swap_contract, func).encode_input(
            [
                path_address,
                package.config["networks"][src_net]["SoDiamond"],
                int(time.time() + 3000),
                fromAmount,
                min_amount,
            ]
        )
    elif func in [SwapFunc.swapExactETHForTokens, SwapFunc.swapExactAVAXForTokens]:
        callData = getattr(swap_contract, func).encode_input(
            min_amount,
            path_address,
            package.config["networks"][src_net]["SoDiamond"],
            int(time.time() + 3000),
        )
    else:
        raise ValueError("Not support")

    swap_data = SwapData(
        callTo=package.config["networks"][src_net]["swap"][router]["router"],
        approveTo=package.config["networks"][src_net]["swap"][router]["router"],
        sendingAssetId=sendingAssetId,
        receivingAssetId=receivingAssetId,
        fromAmount=input_amount,
        callData=callData,
    )
    out.append(swap_data)
    return out


@functools.lru_cache()
def get_token_bridge(net: str):
    contract_name = "TokenBridge"
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["wormhole"]["token_bridge"],
        omniswap_ethereum_project.interface.IWormholeBridge.abi,
    )


@functools.lru_cache()
def get_wormhole_facet():
    contract_name = "WormholeFacet"
    return Contract.from_abi(
        contract_name,
        omniswap_ethereum_project["SoDiamond"][-1].address,
        omniswap_ethereum_project["WormholeFacet"].abi,
    )


def create_wrapped_token():
    vaa = "0x010000000001007f8398176ce200b8898dbd670d553b4209940bd601701bd54d129a3a9661e30a14b31c26512571aafb036abbba5c963bc364f1fd316d9579261469073a1cd7b101634ff6be0000000000160000000000000000000000000000000000000000000000000000000000000001000000000000003600020847d1d277d811e4ae86632a9123234fbf09a3a5773d515d894fea6cf5fa9f3b00160855534443000000000000000000000000000000000000000000000000000000005553444300000000000000000000000000000000000000000000000000000000"
    get_token_bridge(network.show_active()).createWrapped(vaa, {"from": get_account()})
    vaa = "0x010000000001004799c1a6f6481806bab0d7476687ee460262ba6fb2a1c5ba1c215dc5ff0880b8072dde20edc3df3e32d1acdf754daed80f47d23a6bfb67930325052cee934f2800634ff6b8000000000016000000000000000000000000000000000000000000000000000000000000000100000000000000350002fe8192228f7991b052e121fc2c233a6779e56639a3d5d1fd2aba3d40dc11409900160855534454000000000000000000000000000000000000000000000000000000005553445400000000000000000000000000000000000000000000000000000000"
    get_token_bridge(network.show_active()).createWrapped(vaa, {"from": get_account()})
    vaa = "0x010000000001000d1fba22fbbd1f37c8c5f0e1be13fcccb5bfc6f890281fc5def58d9c71b9b1f37e276c68269f51c7552f66b91c27db3e0bd46a97a6f1a0018457b131928fae2a00634ff6b3000000000016000000000000000000000000000000000000000000000000000000000000000100000000000000340002f8976066a3be9afad831d08b2fabf2b959de224a5df7399f38a2efaa3782760100160858425443000000000000000000000000000000000000000000000000000000005842544300000000000000000000000000000000000000000000000000000000"
    get_token_bridge(network.show_active()).createWrapped(vaa, {"from": get_account()})


def complete_so_swap():
    wormhole_facet = get_wormhole_facet()
    vaa: str = "010000000001001e45398c9ce485bab45e3dd57a328bb8717586eddd6cb31a8b256a953ba117dc1aafc808f932332a27955e749700f8dbef6e4cc46cc39d7f1d920644707bacf601634fcd8a0000000000160000000000000000000000000000000000000000000000000000000000000001000000000000003300030000000000000000000000000000000000000000000000000000000000989680a867703f5395cb2965feb7ebff5cdf39b771fc6156085da3ae4147a00be91b380016000000000000000000000000ee05f9e2651ebc5dbc66ad54241c6ab24e361228000400000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a60000000000000020d7dae384d8cec5957e5a7e3d69736443b7d147aa462c29c9e1438ede01c731ac00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af7531000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e75320000000000000014f49e250aeb5abdf660d643583adfd0be41464efd000000000000000000000000000000000000000000000000000000000098968000000000000001a400000000000000010000000000000014d99d1c33f9fc3444f8101754abc46c52416550d10000000000000014d99d1c33f9fc3444f8101754abc46c52416550d100000000000000144a7bd5e135f421057f97bba8bceee5c18334f4540000000000000014f49e250aeb5abdf660d643583adfd0be41464efd0000000000000000000000000000000000000000000000000000000000000000000000000000010438ed17390000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000ee05f9e2651ebc5dbc66ad54241c6ab24e36122800000000000000000000000000000000000000000000000000000000634fd94100000000000000000000000000000000000000000000000000000000000000020000000000000000000000004a7bd5e135f421057f97bba8bceee5c18334f454000000000000000000000000f49e250aeb5abdf660d643583adfd0be41464efd"
    vaa = vaa if vaa.startswith("0x") else "0x" + vaa
    wormhole_facet.completeSoSwap(vaa, {"from": get_account()})


def cross_swap(
    package: aptos_brownie.AptosPackage,
    src_path: list,
    dst_path: list,
    receiver: str,
    dst_so_diamond: str,
    input_amount: int,
    dst_gas_price: int = 100 * 1e10,
    src_router: str = None,
    src_func: str = None,
    src_min_amount: int = 0,
):
    assert len(src_path) > 0
    assert len(dst_path) > 0
    src_net = network.show_active()
    dst_net = package.network
    wormhole = Contract.from_abi(
        "WormholeFacet",
        config["networks"][src_net]["SoDiamond"],
        omniswap_ethereum_project["WormholeFacet"].abi,
    )

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=0,
        dst_so_diamond=dst_so_diamond,
    )
    wormhole_data = wormhole_data.format_to_contract()

    # construct so data
    so_data = generate_so_data(
        package,
        src_token=src_path[0],
        src_net=src_net,
        dst_token=dst_path[-1],
        receiver=receiver,
        amount=input_amount,
    )
    so_data = so_data.format_to_contract()

    # construct src data
    dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_swap_data(
            package, "liquidswap", dst_path, input_amount
        )

        dst_swap_data = [d.format_to_contract() for d in dst_swap_data]

    # construct src data
    src_swap_data = []
    if len(src_path) > 1:
        src_swap_data = generate_src_swap_data(
            package,
            src_net,
            src_router,
            src_func,
            input_amount,
            src_min_amount,
            src_path,
        )
        src_swap_data = [d.format_to_contract() for d in src_swap_data]

    if src_path[0] != "eth":
        token_name = src_path[0]
        token = Contract.from_abi(
            token_name.upper(),
            get_token_address(token_name),
            omniswap_ethereum_project.interface.IERC20.abi,
        )
        token.approve(wormhole.address, so_data[-1], {"from": get_account()})

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )
    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, dst_swap_data
    )
    print(f"Relayer fee: {relayer_fee}")
    if src_path[0] != "eth":
        wormhole_fee = relayer_fee
    else:
        wormhole_fee = input_amount
    wormhole_data[2] = wormhole_fee

    wormhole.soSwapViaWormhole(
        so_data,
        src_swap_data,
        wormhole_data,
        dst_swap_data,
        {"from": get_account(), "value": wormhole_data[2]},
    )


def main():
    src_net = "bsc-test"
    dst_net = "aptos-testnet"
    print(f"src: {src_net}, dst: {dst_net}")
    assert dst_net in ["aptos-mainnet", "aptos-devnet", "aptos-testnet"]

    # Prepare environment
    # load src net aptos package
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path, network=dst_net
    )

    # load dst net project
    change_network(src_net)

    # aptos gas: 16131
    cross_swap(
        package,
        src_path=["AptosCoin_WORMHOLE"],
        dst_path=[
            "AptosCoin",
        ],
        receiver="0x8304621d9c0f6f20b3b5d1bcf44def4ac5c8bf7c11a1ce80b53778532396312b",
        dst_so_diamond=config["networks"][dst_net]["SoDiamond"],
        input_amount=int(100000),
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
    )

    # aptos gas: 29996
    cross_swap(
        package,
        src_path=["AptosCoin_WORMHOLE"],
        dst_path=["AptosCoin", LiquidswapCurve.Uncorrelated, "XBTC"],
        receiver="0x8304621d9c0f6f20b3b5d1bcf44def4ac5c8bf7c11a1ce80b53778532396312b",
        dst_so_diamond=config["networks"][dst_net]["SoDiamond"],
        input_amount=int(100000),
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
    )
    # aptos gas: 44854
    cross_swap(
        package,
        src_path=["AptosCoin_WORMHOLE"],
        dst_path=[
            "AptosCoin",
            LiquidswapCurve.Uncorrelated,
            "XBTC",
            LiquidswapCurve.Uncorrelated,
            "USDT",
        ],
        receiver="0x8304621d9c0f6f20b3b5d1bcf44def4ac5c8bf7c11a1ce80b53778532396312b",
        dst_so_diamond=config["networks"][dst_net]["SoDiamond"],
        input_amount=int(100000),
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
    )

    # aptos gas: 59295
    cross_swap(
        package,
        src_path=["AptosCoin_WORMHOLE"],
        dst_path=[
            "AptosCoin",
            LiquidswapCurve.Uncorrelated,
            "XBTC",
            LiquidswapCurve.Uncorrelated,
            "USDT",
            LiquidswapCurve.Uncorrelated,
            "XBTC",
        ],
        receiver="0x8304621d9c0f6f20b3b5d1bcf44def4ac5c8bf7c11a1ce80b53778532396312b",
        dst_so_diamond=config["networks"][dst_net]["SoDiamond"],
        input_amount=int(100000),
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
    )

    # aptos gas: 278545
    cross_swap(
        package,
        src_path=["AptosCoin_WORMHOLE"],
        dst_path=[
            "AptosCoin",
            LiquidswapCurve.Uncorrelated,
            "XBTC",
            LiquidswapCurve.Uncorrelated,
            "USDT",
            LiquidswapCurve.Stable,
            "USDC",
        ],
        receiver="0x8304621d9c0f6f20b3b5d1bcf44def4ac5c8bf7c11a1ce80b53778532396312b",
        dst_so_diamond=config["networks"][dst_net]["SoDiamond"],
        input_amount=int(100000),
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
    )
    ####################################################
