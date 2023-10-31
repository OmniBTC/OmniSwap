import sys
import json
from pathlib import Path
from enum import Enum
from random import choice
from base58 import b58decode
from brownie import (
    Contract,
    WormholeFacet,
    interface,
)
from scripts.helpful_scripts import (
    get_account,
    to_hex_str,
    change_network
)
from solders.pubkey import Pubkey

sys.path.append(Path(__file__).parent.parent.parent.joinpath("solana/scripts").as_posix())
from get_quote_config import get_test_usdc_quote_config,get_bsc_test_quote_config

class SolanaSwapType(Enum):
    Whirlpool = "Whirlpool"


def usdc_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi("", "0x51a3cc54eA30Da607974C5D07B8502599801AC08", interface.IERC20.abi)

    token.approve(aprrove_address, amount, {"from": get_account()})


def bsc_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi("", "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1", interface.IERC20.abi)

    token.approve(aprrove_address, amount, {"from": get_account()})

def attest_token_bsc():
    change_network("bsc-test")
    token_bridge = Contract.from_abi("", "0x9dcF9D205C9De35334D646BeE44b2D2859712A09", interface.IWormholeBridge.abi)
    token_bridge.attestToken(
        "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1",
        0,
        {"from": get_account()}
    )


class View:
    def __repr__(self):
        data = vars(self)
        for k in list(data.keys()):
            if not k.startswith("_"):
                continue
            del data[k]
        return json.dumps(data, sort_keys=True, indent=4, separators=(",", ":"))

    @staticmethod
    def from_dict(obj, data: dict):
        return obj(**data)
class SoData(View):
    def __init__(
            self,
            transactionId,
            receiver,
            sourceChainId,
            sendingAssetId,
            destinationChainId,
            receivingAssetId,
            amount,
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
        return [
            to_hex_str(self.transactionId),
            to_hex_str(self.receiver),
            self.sourceChainId if self.sourceChainId < 65535 else 0,
            to_hex_str(self.sendingAssetId),
            self.destinationChainId if self.destinationChainId < 65535 else 0,
            to_hex_str(self.receivingAssetId),
            self.amount,
        ]

    @staticmethod
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

    @classmethod
    def create_usdc(
            cls,
            receiver: str,
            amount: int,
    ):

        return SoData(
            transactionId=cls.generate_random_bytes32(),
            receiver=receiver,
            sourceChainId=4,
            sendingAssetId="0x51a3cc54eA30Da607974C5D07B8502599801AC08", # usdc-sol(by wormhole)
            destinationChainId=1,
            receivingAssetId="0x"+b58decode("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU").hex(), # usdc (on solana)
            amount=amount,
        )

    @classmethod
    def create_bsc(
            cls,
            receiver: str,
            amount: int,
    ):

        return SoData(
            transactionId=cls.generate_random_bytes32(),
            receiver=receiver,
            sourceChainId=4,
            sendingAssetId="0x8CE306D8A34C99b23d3054072ba7fc013684e8a1", # bsc token(test)
            destinationChainId=1,
            receivingAssetId="0x"+b58decode("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU").hex(), # usdc (on solana)
            amount=amount,
        )


class SwapData(View):
    def __init__(
            self,
            callTo,
            approveTo,
            sendingAssetId,
            receivingAssetId,
            fromAmount,
            callData,
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

    def format_to_contract(self):
        """Returns the data used to pass into the contract interface"""
        return [
            to_hex_str(self.callTo),
            to_hex_str(self.approveTo),
            to_hex_str(self.sendingAssetId, False),
            to_hex_str(self.receivingAssetId, False),
            self.fromAmount,
            to_hex_str(self.callData),
        ]


def cross_swap_wrapped_via_wormhole():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_usdc = 1000000 # decimals=6

    usdc_token_approve(one_usdc, so_diamond)

    so_data = SoData.create_usdc(
        receiver="0x"+b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_usdc
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []
    swap_data_dst = []
    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = "0x"+b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", so_diamond, WormholeFacet.abi
    )

    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, swap_data_dst
    )
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + input_eth_amount
    wormhole_data[2] = msg_value
    print(
        f"wormhole cross fee: {wormhole_fee / 1e18} ether\n"
        f"relayer fee: {relayer_fee / 1e18} ether\n"
        f"input eth: {input_eth_amount / 1e18} ether\n"
        f"msg value: {msg_value / 1e18} ether"
    )
    proxy_diamond.soSwapViaWormhole(
        so_data,
        swap_data_src,
        wormhole_data,
        swap_data_src,
        {"from": get_account(), "value": int(msg_value)},
    )


def complete_swap_via_wormhole():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", so_diamond, WormholeFacet.abi
    )

    vaa = bytes.fromhex("01000000000100dccfc5aef5b229a387d5464842e1b045b89d56558befc2a8ae1573838d88e59037f26305353912efb530d074a1ddb2427256d73d73074214b5bd100fe3f4dac300653f93b30000000000013b26409f8aaded3f5ddca184695aa6a0fa829b0c85caf84856324896d214ca980000000000006407200300000000000000000000000000000000000000000000000000000000056dc50b0000000000000000000000008ce306d8a34c99b23d3054072ba7fc013684e8a1000400000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc00043eb54bfb6f363a4b14879f4189fecd37bf35acfc86572f9879f620736ecf3228030186a0030aed98200cc750774ceb719d5663d6a5ee82a5575d89b2a7d197d21401a58c6adb1d077014caf084133cbdbe27490d3afb0da220a40c32e307148ce306d8a34c99b23d3054072ba7fc013684e8a1")

    proxy_diamond.completeSoSwap(vaa, {"from": get_account()})

def get_quote_test_usdc_pool(token_mint_in: str, ui_amount_in: str):
    quote_config = get_test_usdc_quote_config(token_mint_in, ui_amount_in)

    print("USDC amount_in: ", quote_config["amount_in"])
    print("TEST estimated_amount_out: ", quote_config["estimated_amount_out"])
    print("TEST min_amount_out: ", quote_config["min_amount_out"])

    return quote_config


def cross_swap_wrapped_via_wormhole_whirlpool():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_usdc = 1000000 # decimals=6
    # 1 USDC
    ui_amount = "1"

    usdc_token_approve(one_usdc, so_diamond)

    so_data = SoData.create_usdc(
        receiver="0x"+b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_usdc
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []

    # Swap USDC to TEST on solana
    # TEST is tokenA
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    # USDC is tokenB
    USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    sendingAssetId = bytes(Pubkey.from_string(USDC))
    receivingAssetId = bytes(Pubkey.from_string(TEST))
    quote_config = get_quote_test_usdc_pool(USDC, ui_amount)

    swap_data_dst = [
        SwapData(
            callTo="0x"+bytes(quote_config["whirlpool"]).hex(),
            approveTo="0x"+bytes(quote_config["whirlpool"]).hex(),
            sendingAssetId="0x"+sendingAssetId.hex(),
            receivingAssetId="0x"+receivingAssetId.hex(),
            fromAmount=quote_config["amount_in"],
            callData="0x"+bytes(
                f"Whirlpool,{quote_config['min_amount_out']}", "ascii"
            ).hex(),
        ).format_to_contract()
    ]
    print("swap_data_dst\n", swap_data_dst)

    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = "0x"+b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", so_diamond, WormholeFacet.abi
    )

    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, swap_data_dst
    )
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + input_eth_amount
    wormhole_data[2] = msg_value
    print(
        f"wormhole cross fee: {wormhole_fee / 1e18} ether\n"
        f"relayer fee: {relayer_fee / 1e18} ether\n"
        f"input eth: {input_eth_amount / 1e18} ether\n"
        f"msg value: {msg_value / 1e18} ether"
    )
    proxy_diamond.soSwapViaWormhole(
        so_data,
        swap_data_src,
        wormhole_data,
        swap_data_dst,
        {"from": get_account(), "value": int(msg_value)},
    )


def cross_swap_native_via_wormhole():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_bsc = 1_000_000_000_000_000_000 # decimals=18

    bsc_token_approve(one_bsc*100, so_diamond)

    so_data = SoData.create_bsc(
        receiver="0x"+b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_bsc*100
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []
    swap_data_dst = []
    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = "0x"+b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", so_diamond, WormholeFacet.abi
    )

    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, swap_data_dst
    )
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + input_eth_amount
    wormhole_data[2] = msg_value
    print(
        f"wormhole cross fee: {wormhole_fee / 1e18} ether\n"
        f"relayer fee: {relayer_fee / 1e18} ether\n"
        f"input eth: {input_eth_amount / 1e18} ether\n"
        f"msg value: {msg_value / 1e18} ether"
    )
    proxy_diamond.soSwapViaWormhole(
        so_data,
        swap_data_src,
        wormhole_data,
        swap_data_src,
        {"from": get_account(), "value": int(msg_value)},
    )


def cross_swap_native_via_wormhole_whirlpool():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_bsc = 1_000_000_000_000_000_000 # decimals=18
    # 1 BSC
    ui_amount = "1"

    bsc_token_approve(one_bsc, so_diamond)

    so_data = SoData.create_bsc(
        receiver="0x"+b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_bsc
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []

    # Swap USDC to TEST on solana
    # Wrapped BSC is tokenA, decimal=8
    BSC = "xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"
    # TEST is tokenB
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    sendingAssetId = bytes(Pubkey.from_string(BSC))
    receivingAssetId = bytes(Pubkey.from_string(TEST))
    quote_config = get_bsc_test_quote_config(BSC, ui_amount)

    swap_data_dst = [
        SwapData(
            callTo="0x"+bytes(quote_config["whirlpool"]).hex(),
            approveTo="0x"+bytes(quote_config["whirlpool"]).hex(),
            sendingAssetId="0x"+sendingAssetId.hex(),
            receivingAssetId="0x"+receivingAssetId.hex(),
            fromAmount=quote_config["amount_in"],
            callData="0x"+bytes(
                f"Whirlpool,{quote_config['min_amount_out']}", "ascii"
            ).hex(),
        ).format_to_contract()
    ]
    print("swap_data_dst\n", swap_data_dst)

    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = "0x"+b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", so_diamond, WormholeFacet.abi
    )

    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, swap_data_dst
    )
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + input_eth_amount
    wormhole_data[2] = msg_value
    print(
        f"wormhole cross fee: {wormhole_fee / 1e18} ether\n"
        f"relayer fee: {relayer_fee / 1e18} ether\n"
        f"input eth: {input_eth_amount / 1e18} ether\n"
        f"msg value: {msg_value / 1e18} ether"
    )
    proxy_diamond.soSwapViaWormhole(
        so_data,
        swap_data_src,
        wormhole_data,
        swap_data_dst,
        {"from": get_account(), "value": int(msg_value)},
    )



def main():
    # complete_swap_via_wormhole()
    # cross_swap_wrapped_via_wormhole()
    cross_swap_wrapped_via_wormhole_whirlpool()
    # cross_swap_native_via_wormhole_whirlpool()