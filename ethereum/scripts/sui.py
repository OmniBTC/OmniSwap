import functools
import time
from enum import Enum
from pathlib import Path
from typing import List

from brownie import network, Contract, project, config
from sui_brownie import sui_brownie

from helpful_scripts import (
    to_hex_str,
    get_token_address,
    zero_address,
    change_network,
    get_account,
)
from scripts import sui_project
from scripts.deploy import load_omniswap
from scripts.struct_sui import generate_random_bytes32
from scripts.wormhole import get_evm_token
from swap import SwapType, SwapFunc, View, SwapData, SoData

omniswap_ethereum_path = Path(__file__).parent.parent
omniswap_ethereum_project = project.load(
    str(omniswap_ethereum_path), raise_if_loaded=False
)
omniswap_ethereum_project.load_config()

omniswap_aptos_path = Path(__file__).parent.parent.parent.joinpath("aptos")


class SuiSwapType(Enum):
    OmniswapMock = "OmniswapMock"
    DeepBook = "DeepBook"
    Cetus = "Cetus"
    DeepBookV2 = "DeepBookV2"


@functools.lru_cache()
def get_sui_token():
    if "tokens" not in sui_project.network_config:
        return {
            "SUI": {
                "address": "0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                "decimal": 8,
                "name": "SUI",
            }
        }

    return sui_project.network_config["tokens"]


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
    src_net: str, src_token: str, dst_token: str, receiver: str, amount: int
) -> SoData:
    return SoData(
        transactionId=generate_random_bytes32(),
        receiver=receiver,
        sourceChainId=sui_project.config["networks"][src_net]["omnibtc_chainid"],
        sendingAssetId=get_evm_token(src_net)[src_token]["address"],
        destinationChainId=sui_project.network_config["omnibtc_chainid"],
        receivingAssetId=get_sui_token()[dst_token]["address"],
        amount=amount,
    )


def generate_wormhole_data(
    dst_net: str,
    dst_gas_price: int,
    wormhole_fee: int,
    dst_so_diamond: str,
) -> WormholeData:
    return WormholeData(
        dstWormholeChainId=sui_project.config["networks"][dst_net]["wormhole"][
            "chainid"
        ],
        dstMaxGasPriceInWeiForRelayer=dst_gas_price,
        wormholeFee=wormhole_fee,
        dstSoDiamond=dst_so_diamond,
    )


def generate_dst_swap_data(
    router: SuiSwapType,
    path: list,
    amount: int,
    dst_pool_ids: list,
) -> List[SwapData]:
    out = []
    i = 0

    while i < len(path) - 1:
        swap_data = SwapData(
            callTo=dst_pool_ids[i],
            approveTo=dst_pool_ids[i],
            sendingAssetId=get_sui_token()[path[i]]["address"].replace("0x", ""),
            receivingAssetId=get_sui_token()[path[i + 1]]["address"].replace("0x", ""),
            fromAmount=amount,
            callData=f"{router.value},0",
        )
        out.append(swap_data)
        i += 1
    return out


evm_zero_address = zero_address


def generate_src_swap_data(
    package: sui_brownie.SuiPackage,
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
def get_wormhole_facet(net: str):
    change_network(net)
    contract_name = "WormholeFacet"
    return Contract.from_abi(
        contract_name,
        sui_project.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project["WormholeFacet"].abi,
    )


def cross_swap(
    package: sui_brownie.SuiPackage,
    src_path: list,
    dst_path: list,
    dst_pool_ids: list,
    receiver: str,
    dst_so_diamond: str,
    input_amount: int,
    dst_gas_price: int = 1000 * 1e9,
    src_router: str = None,
    src_func: str = None,
    src_min_amount: int = 0,
    dst_swap_type: SuiSwapType = SuiSwapType.Cetus,
):
    src_net = network.show_active()
    dst_net = sui_project.network

    wormhole = get_wormhole_facet(src_net)

    # construct wormhole data
    wormhole_data = generate_wormhole_data(
        dst_net=dst_net,
        dst_gas_price=dst_gas_price,
        wormhole_fee=0,
        dst_so_diamond=dst_so_diamond,
    )
    wormhole_data = wormhole_data.format_to_contract()

    # construct so data
    so_data = generate_so_data(
        src_net,
        src_token=src_path[0],
        dst_token=dst_path[-1],
        receiver=receiver,
        amount=input_amount,
    )
    print(so_data)
    so_data = so_data.format_to_contract()

    # construct src data
    dst_swap_data = []
    if len(dst_path) > 1:
        dst_swap_data = generate_dst_swap_data(
            dst_swap_type, dst_path, input_amount, dst_pool_ids
        )
        print(dst_swap_data)
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

    relayer_fee = wormhole.estimateRelayerFee(so_data, wormhole_data, dst_swap_data)
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


def cross_for_testnet():
    src_net = "bsc-test"
    dst_net = "sui-testnet"
    print(f"src: {src_net}, dst: {dst_net}")

    # Prepare environment
    # load src net aptos package
    omniswap = load_omniswap(is_from_config=True)

    # load dst net project
    change_network(src_net)

    # cross_swap(
    #     omniswap,
    #     src_path=["sui-usdc"],
    #     dst_path=["Cetus-USDC"],
    #     receiver="0xa65b84b73c857082b680a148b7b25327306d93cc7862bae0edfa7628b0342392",
    #     dst_so_diamond=sui_project.config["networks"][dst_net]["SoDiamond"],
    #     input_amount=100000,
    #     src_router=SwapType.IUniswapV2Router02,
    #     src_func=SwapFunc.swapExactTokensForTokens,
    #     dst_swap_type=SuiSwapType.Cetus
    # )

    cross_swap(
        omniswap,
        src_path=["sui-usdc"],
        dst_path=["Cetus-USDC", "Cetus-USDT", "Cetus-USDC"],
        receiver="0xa65b84b73c857082b680a148b7b25327306d93cc7862bae0edfa7628b0342392",
        dst_so_diamond=sui_project.network_config["SoDiamond"],
        input_amount=100000,
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
        dst_swap_type=SuiSwapType.Cetus,
        dst_pool_ids=[
            sui_project.network_config["pools"]["Cetus-USDT-USDC"]["pool_id"],
            sui_project.network_config["pools"]["Cetus-USDT-USDC"]["pool_id"],
        ],
    )


def cross_for_mainnet():
    src_net = "bsc-main"
    change_network(src_net)
    dst_net = sui_project.network
    print(f"src: {src_net}, dst: {dst_net}")

    # Prepare environment
    # load src net aptos package
    omniswap = load_omniswap(is_from_config=True)

    # cross_swap(
    #     omniswap,
    #     src_path=["sui-usdc"],
    #     dst_path=["Cetus-USDC"],
    #     receiver="0xa65b84b73c857082b680a148b7b25327306d93cc7862bae0edfa7628b0342392",
    #     dst_so_diamond=sui_project.config["networks"][dst_net]["SoDiamond"],
    #     input_amount=100000,
    #     src_router=SwapType.IUniswapV2Router02,
    #     src_func=SwapFunc.swapExactTokensForTokens,
    #     dst_swap_type=SuiSwapType.Cetus
    # )

    cross_swap(
        omniswap,
        src_path=["USDC_ETH_WORMHOLE"],
        dst_path=["Wormhole-USDC", "SUI"],
        receiver="0x65859958bd62e30aa0571f9712962f59098d1eb29f73b091d9d71317d8e67497",
        dst_so_diamond=sui_project.config["networks"][dst_net]["SoDiamond"],
        input_amount=100000,
        src_router=SwapType.IUniswapV2Router02,
        src_func=SwapFunc.swapExactTokensForTokens,
        dst_swap_type=SuiSwapType.DeepBookV2,
        dst_pool_ids=[sui_project.network_config["pools"]["DeepBook-SUI-USDC-V2"]["pool_id"]
                      ],
    )

    # cross_swap(
    #     omniswap,
    #     src_path=["USDC_ETH_WORMHOLE"],
    #     dst_path=["Wormhole-USDC", "SUI", "Wormhole-USDC"],
    #     receiver="0x65859958bd62e30aa0571f9712962f59098d1eb29f73b091d9d71317d8e67497",
    #     dst_so_diamond=sui_project.config["networks"][dst_net]["SoDiamond"],
    #     input_amount=100000,
    #     src_router=SwapType.IUniswapV2Router02,
    #     src_func=SwapFunc.swapExactTokensForTokens,
    #     dst_swap_type=SuiSwapType.DeepBookV2,
    #     dst_pool_ids=[sui_project.network_config["pools"]["DeepBook-SUI-USDC-V2"]["pool_id"],
    #                   sui_project.network_config["pools"]["DeepBook-SUI-USDC-V2"]["pool_id"]
    #                   ],
    # )


if __name__ == "__main__":
    cross_for_mainnet()
