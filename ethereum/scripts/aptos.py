import functools
import time
from enum import Enum
from pathlib import Path
from typing import List

from brownie import network, Contract, project

from scripts.helpful_scripts import to_hex_str, get_token_address, zero_address, change_network, \
    get_account
from scripts.swap import SwapType, SwapFunc, View, SwapData, SoData
from scripts.utils import aptos_brownie

omniswap_ethereum_path = Path(__file__).parent.parent
omniswap_ethereum_project = project.load(str(omniswap_ethereum_path), raise_if_loaded=False)

omniswap_aptos_path = Path(__file__).parent.parent.parent.joinpath("aptos")


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


class WormholeData(View):
    """Constructing wormhole data"""

    def __init__(self,
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
        return [self.dstWormholeChainId,
                self.dstMaxGasPriceInWeiForRelayer,
                self.wormholeFee,
                to_hex_str(self.dstSoDiamond)]


get_evm_token_address = get_token_address


def generate_so_data(
        package: aptos_brownie.AptosPackage,
        src_token: str,
        src_net: str,
        dst_token: str,
        receiver: str,
        amount: int
) -> SoData:
    so_data = SoData(
        transactionId=SoData.generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=package.config["networks"][src_net]["omnibtc_chainid"],
        sendingAssetId=get_evm_token_address(src_token),
        destinationChainId=package.config["networks"][package.network]["omnibtc_chainid"],
        receivingAssetId=get_aptos_token(package)[dst_token]["address"],
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
        dstSoDiamond=omniswap_ethereum_project["SoDiamond"][-1].address
    )
    return wormhole_data


class LiquidswapCurve(Enum):
    Uncorrelated = "Uncorrelated"
    Stable = "Stable"


def get_liquidswap_curve(package: aptos_brownie.AptosPackage, curve_name: LiquidswapCurve):
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
            callData=get_liquidswap_curve(package, path[i + 1])
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
        path: list
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
        getattr(omniswap_ethereum_project.interface, router).abi)

    fromAmount = input_amount
    if func in [SwapFunc.swapExactTokensForETH, SwapFunc.swapExactTokensForAVAX,
                SwapFunc.swapExactTokensForTokens]:
        callData = getattr(swap_contract, func).encode_input(
            fromAmount,
            min_amount,
            path_address,
            package.config["networks"][src_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    elif func == SwapFunc.exactInput:
        callData = getattr(swap_contract, func).encode_input([
            path_address,
            package.config["networks"][src_net]["SoDiamond"],
            int(time.time() + 3000),
            fromAmount,
            min_amount]
        )
    elif func in [SwapFunc.swapExactETHForTokens, SwapFunc.swapExactAVAXForTokens]:
        callData = getattr(swap_contract, func).encode_input(
            min_amount,
            path_address,
            package.config["networks"][src_net]["SoDiamond"],
            int(time.time() + 3000)
        )
    else:
        raise ValueError("Not support")

    swap_data = SwapData(
        callTo=package.config["networks"][src_net]["swap"][router]["router"],
        approveTo=package.config["networks"][src_net]["swap"][router]["router"],
        sendingAssetId=sendingAssetId,
        receivingAssetId=receivingAssetId,
        fromAmount=input_amount,
        callData=callData
    )
    out.append(swap_data)
    return out


def cross_swap(
        package: aptos_brownie.AptosPackage,
        src_path: list,
        dst_path: list,
        receiver: str,
        input_amount: int,
        dst_gas_price: int = 0,
        src_router: str = None,
        src_func: str = None,
        src_min_amount: int = 0
):
    assert len(src_path) > 0
    assert len(dst_path) > 0
    src_net = network.show_active()
    dst_net = package.network
    wormhole = Contract.from_abi(
        "WormholeFacet",
        omniswap_ethereum_project["SoDiamond"][-1].address,
        omniswap_ethereum_project["WormholeFacet"].abi
    )

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        package,
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=10000000
    )
    print("wormhole_data", wormhole_data)
    wormhole_data = wormhole_data.format_to_contract()

    # construct so data
    so_data = generate_so_data(
        package,
        src_token=src_path[0],
        src_net=src_net,
        dst_token=dst_path[-1],
        receiver=receiver,
        amount=input_amount)
    print("so_data", so_data)
    so_data = so_data.format_to_contract()

    # construct src data
    dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_swap_data(package, "liquidswap", dst_path, input_amount)
        print("dst_swap_data", dst_swap_data)

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
            src_path
        )
        print("src_swap_data", src_swap_data)
        src_swap_data = [d.format_to_contract() for d in src_swap_data]

    if src_path[0] != "eth":
        token_name = src_path[0]
        token = Contract.from_abi(token_name.upper(),
                                  get_token_address(token_name),
                                  omniswap_ethereum_project.interface.IERC20.abi
                                  )
        token.approve(wormhole.address, so_data[-1], {"from": get_account()})

    wormhole.soSwapViaWormhole(
        so_data,
        src_swap_data,
        wormhole_data,
        dst_swap_data,
        {"from": get_account(), "value": wormhole_data[2]}
    )


def main():
    src_net = "bsc-test"
    dst_net = "aptos-testnet"
    assert dst_net in ["aptos-mainnet", "aptos-devnet", "aptos-testnet"]

    # Prepare environment
    # load src net aptos package
    package = aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=dst_net
    )

    # load dst net project
    change_network(src_net)

    cross_swap(
        package,
        src_path=["usdt", "USDT_WORMHOLE"],
        dst_path=[
            "USDT",
            LiquidswapCurve.Uncorrelated,
            "XBTC",
            LiquidswapCurve.Uncorrelated,
            "AptosCoin",
        ],
        receiver="0x5b21da730075862b85ef9f681d1dad66e4b6ab2588b29161164ffb84ec8aebc3",
        input_amount=10000000,
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens
    )
    ####################################################
