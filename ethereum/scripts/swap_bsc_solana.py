
import json
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

def usdc_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi("", "0x51a3cc54eA30Da607974C5D07B8502599801AC08", interface.IERC20.abi)

    token.approve(aprrove_address, amount, {"from": get_account()})

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


def cross_swap_via_wormhole():
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
    dst_diamond_address = "0x"+b58decode("9YYGvVLZJ9XmKM2A1RNv1Dx3oUnHWgtXWt8V3HU5MtXU").hex()
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

    vaa = bytes.fromhex("01000000000100656d4338732440c51182272253c21215355e5aaad361b1d8f0c3a5be26779ca27e50d410162c816ef22dbcc04f59ccf6e03fec35b7fc2c7e13e696d0648737b1016522b5880000000000013b26409f8aaded3f5ddca184695aa6a0fa829b0c85caf84856324896d214ca9800000000000063a3200300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc00047ef1dcda48c0b739dfd4da982c187838573cc044d8ded9fe382b84ceb6fa6b53030186a0010020529cde8179944a09935bc0c58773ad50b39dc0b698457bc8c9e732e2b63c6da314caf084133cbdbe27490d3afb0da220a40c32e3071451a3cc54ea30da607974c5d07b8502599801ac08")

    proxy_diamond.completeSoSwap(vaa, {"from": get_account()})

def main():
    complete_swap_via_wormhole()
