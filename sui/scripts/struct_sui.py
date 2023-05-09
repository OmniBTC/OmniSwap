import json
from pathlib import Path
from random import choice
from typing import List

from brownie import web3, network, project

omniswap_ethereum_path = Path(__file__).parent.parent.parent.joinpath("ethereum")
omniswap_ethereum_project = project.load(str(omniswap_ethereum_path), raise_if_loaded=False)
omniswap_ethereum_project.load_config()

omniswap_sui_path = Path(__file__).parent.parent


def generate_random_bytes32():
    """Produce random transactions iD for tracking transactions on both chains

    Returns:
        result: 32 bytes hex
    """
    chars = [str(i) for i in range(10)] + ["a", "b", "c", "d", "e"]
    result = "0x"
    for _ in range(64):
        result += choice(chars)
    return result


def decode_hex_to_ascii(data: str):
    data = str(data).replace("0x", "")
    return str(bytearray.fromhex(data).decode(encoding="ascii"))


def padding_to_bytes(data: str, padding="right", length=32):
    if data[:2] == "0x":
        data = data[2:]
    padding_length = length * 2 - len(data)
    if padding == "right":
        return "0x" + data + "0" * padding_length
    else:
        return "0x" + "0" * padding_length + data


def change_network(dst_net):
    if network.show_active() == dst_net:
        return
    if network.is_connected():
        network.disconnect()
    network.connect(dst_net)


def judge_hex_str(data: str):
    if not data.startswith("0x"):
        return False
    if len(data) % 2 != 0:
        return False
    try:
        web3.toInt(hexstr=data)
        return True
    except:
        return False


def to_hex_str(data: str, with_prefix=True):
    if judge_hex_str(data):
        return data
    if with_prefix:
        return "0x" + bytes(data, 'ascii').hex()
    else:
        return bytes(data, 'ascii').hex()


def hex_str_to_vector_u8(data: str) -> List[int]:
    assert judge_hex_str(data)
    return list(bytearray.fromhex(data.replace("0x", "")))


class View:
    def __repr__(self):
        data = vars(self)
        for k in list(data.keys()):
            if not k.startswith("_"):
                continue
            del data[k]
        return json.dumps(data, sort_keys=True, indent=4, separators=(',', ':'))

    @staticmethod
    def from_dict(obj, data: dict):
        return obj(**data)


class SoData(View):

    def __init__(self,
                 transactionId,
                 receiver,
                 sourceChainId,
                 sendingAssetId,
                 destinationChainId,
                 receivingAssetId,
                 amount
                 ):
        # unique identification id
        self.transactionId = transactionId
        # token receiving account
        self.receiver = receiver
        # source chain id
        self.sourceChainId = sourceChainId
        # The starting token address of the source chain
        self.sendingAssetId = sendingAssetId
        # destination chain id
        self.destinationChainId = destinationChainId
        # The final token address of the destination chain
        self.receivingAssetId = receivingAssetId
        # User enters amount
        self.amount = amount

    def format_to_contract(self):
        """Get the SoData needed for the contract interface

        Returns:
            SoData: Information for recording and tracking cross-chain transactions
        """
        return [to_hex_str(self.transactionId),
                to_hex_str(self.receiver),
                self.sourceChainId,
                to_hex_str(self.sendingAssetId),
                self.destinationChainId,
                to_hex_str(self.receivingAssetId),
                self.amount]


class SwapData(View):
    """Constructing data for calling UniswapLike"""

    def __init__(self,
                 callTo,
                 approveTo,
                 sendingAssetId,
                 receivingAssetId,
                 fromAmount,
                 callData,
                 swapType: str = None,
                 swapFuncName: str = None,
                 swapPath: list = None,
                 swapEncodePath: list = None
                 ):
        # The swap address
        self.callTo = callTo
        # The swap address
        self.approveTo = approveTo
        # The swap start token address
        self.sendingAssetId = sendingAssetId
        # The swap final token address
        self.receivingAssetId = receivingAssetId
        # The swap start token amount
        self.fromAmount = fromAmount
        # The swap callData
        self.callData = callData
        self.swapType = swapType
        self.swapFuncName = swapFuncName
        self.swapPath = swapPath
        self.swapEncodePath = swapEncodePath

    def format_to_contract(self):
        """Returns the data used to pass into the contract interface"""
        return [to_hex_str(self.callTo),
                to_hex_str(self.approveTo),
                to_hex_str(self.sendingAssetId, with_prefix=False),
                to_hex_str(self.receivingAssetId, with_prefix=False),
                self.fromAmount,
                to_hex_str(self.callData)]


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
