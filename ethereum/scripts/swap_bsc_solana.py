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
from scripts.helpful_scripts import get_account, to_hex_str, change_network
from solders.pubkey import Pubkey

sys.path.append(
    Path(__file__).parent.parent.parent.joinpath("solana/scripts").as_posix()
)
from get_quote_config import get_whirlpool_quote_config


class SolanaSwapType(Enum):
    Whirlpool = "Whirlpool"


def usdc_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi(
        "", "0x51a3cc54eA30Da607974C5D07B8502599801AC08", interface.IERC20.abi
    )

    token.approve(aprrove_address, amount, {"from": get_account()})


def bsc_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi(
        "", "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1", interface.IERC20.abi
    )

    token.approve(aprrove_address, amount, {"from": get_account()})


def wsol_token_approve(amount: int, aprrove_address: str):
    token = Contract.from_abi(
        "", "0x30f19eBba919954FDc020B8A20aEF13ab5e02Af0", interface.IERC20.abi
    )

    token.approve(aprrove_address, amount, {"from": get_account()})


def attest_token_bsc():
    change_network("bsc-test")
    token_bridge = Contract.from_abi(
        "", "0x9dcF9D205C9De35334D646BeE44b2D2859712A09", interface.IWormholeBridge.abi
    )
    token_bridge.attestToken(
        "0x8CE306D8A34C99b23d3054072ba7fc013684e8a1", 0, {"from": get_account()}
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
        receiving_token: str,
        receiver: str,
        amount: int,
    ):
        return SoData(
            transactionId=cls.generate_random_bytes32(),
            receiver=receiver,
            sourceChainId=4,
            sendingAssetId="0x51a3cc54eA30Da607974C5D07B8502599801AC08",  # usdc-sol(by wormhole)
            destinationChainId=1,
            receivingAssetId=receiving_token,
            amount=amount,
        )

    @classmethod
    def create_wsol(
        cls,
        receiving_token: str,
        receiver: str,
        amount: int,
    ):
        return SoData(
            transactionId=cls.generate_random_bytes32(),
            receiver=receiver,
            sourceChainId=4,
            sendingAssetId="0x30f19eBba919954FDc020B8A20aEF13ab5e02Af0",  # wsol
            destinationChainId=1,
            receivingAssetId=receiving_token,
            amount=amount,
        )

    @classmethod
    def create_bsc(
        cls,
        receiving_token: str,
        receiver: str,
        amount: int,
    ):
        return SoData(
            transactionId=cls.generate_random_bytes32(),
            receiver=receiver,
            sourceChainId=4,
            sendingAssetId="0x8CE306D8A34C99b23d3054072ba7fc013684e8a1",  # bsc token(test)
            destinationChainId=1,
            receivingAssetId=receiving_token,
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
    one_usdc = 1000000  # decimals=6

    usdc_token_approve(one_usdc, so_diamond)

    so_data = SoData.create_usdc(
        receiving_token="0x"
        + b58decode("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU").hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_usdc,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []
    swap_data_dst = []
    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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


def fix_config(quote_config):
    return {
        "whirlpool_program": Pubkey.from_string(quote_config["whirlpool_program"]),
        "whirlpool": Pubkey.from_string(quote_config["whirlpool"]),
        "token_mint_a": Pubkey.from_string(quote_config["token_mint_a"]),
        "token_mint_b": Pubkey.from_string(quote_config["token_mint_b"]),
        "token_owner_account_a": Pubkey.from_string(
            quote_config["token_owner_account_a"]
        ),
        "token_owner_account_b": Pubkey.from_string(
            quote_config["token_owner_account_b"]
        ),
        "token_vault_a": Pubkey.from_string(quote_config["token_vault_a"]),
        "token_vault_b": Pubkey.from_string(quote_config["token_vault_b"]),
        "tick_array_0": Pubkey.from_string(quote_config["tick_array_0"]),
        "tick_array_1": Pubkey.from_string(quote_config["tick_array_1"]),
        "tick_array_2": Pubkey.from_string(quote_config["tick_array_2"]),
        "oracle": Pubkey.from_string(quote_config["oracle"]),
        "is_a_to_b": quote_config["is_a_to_b"],
        "amount_in": int(quote_config["amount_in"]),
        "estimated_amount_out": int(quote_config["estimated_amount_out"]),
        "min_amount_out": int(quote_config["min_amount_out"]),
    }


def complete_swap_via_wormhole():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

    vaa = bytes.fromhex(
        "0100000000010010308ad8336be558813df5cf5e18061b32038cfa03038c0dbce2c7bf16658e1b445fb0e13121003a5313a80de61991007d4f75cf5ea9304c57629b5feb9210b50065535fc40000000000013b26409f8aaded3f5ddca184695aa6a0fa829b0c85caf84856324896d214ca980000000000006475200300000000000000000000000000000000000000000000000000000000000fe9050000000000000000000000008ce306d8a34c99b23d3054072ba7fc013684e8a1000400000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc00043636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843030186a0030aed9820e33ce38ac6a04c1522ebeced0638b14d9b48d7bdb9128ddad911ac23289353c514caf084133cbdbe27490d3afb0da220a40c32e307148ce306d8a34c99b23d3054072ba7fc013684e8a1"
    )

    proxy_diamond.completeSoSwap(vaa, {"from": get_account()})


def cross_swap_wrapped_wsol():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    wsol_amount = 10_000_000  # decimals=9

    wsol_token_approve(wsol_amount, so_diamond)

    so_data = SoData.create_wsol(
        receiving_token="0x" + bytes([0] * 32).hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=wsol_amount,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []
    swap_data_dst = []
    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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


def cross_swap_wrapped_usdc_test_whirlpool():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_usdc = 100000  # decimals=6
    # 1 USDC
    ui_amount = "0.1"

    usdc_token_approve(one_usdc, so_diamond)

    so_data = SoData.create_usdc(
        receiving_token="0x"
        + b58decode("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS").hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_usdc,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []

    # Swap USDC to TEST on solana
    # TEST is tokenA
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    # USDC is tokenB
    USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    TEST_USDC_POOL = "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV"

    sendingAssetId = bytes(Pubkey.from_string(USDC))
    receivingAssetId = bytes(Pubkey.from_string(TEST))
    quote_config = get_whirlpool_quote_config(TEST_USDC_POOL, USDC, ui_amount)

    swap_data_dst = [
        SwapData(
            callTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            approveTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            sendingAssetId="0x" + sendingAssetId.hex(),
            receivingAssetId="0x" + receivingAssetId.hex(),
            fromAmount=quote_config["amount_in"],
            callData="0x"
            + bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii").hex(),
        ).format_to_contract()
    ]
    print("swap_data_dst\n", swap_data_dst)

    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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


def cross_swap_wrapped_usdc_wsol_whirlpool():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    usdc_amount = 100000  # decimals=6
    # 1 USDC
    ui_amount = "0.1"

    usdc_token_approve(usdc_amount, so_diamond)

    # USDC -> WSOL -> SOL

    so_data = SoData.create_usdc(
        receiving_token="0x" + bytes([0] * 32).hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=usdc_amount,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []

    SOL_USDC_POOL = "3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd"
    # tokenA
    WSOL = "So11111111111111111111111111111111111111112"
    # tokenB
    USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

    sendingAssetId = bytes(Pubkey.from_string(USDC))
    receivingAssetId = bytes(Pubkey.from_string(WSOL))
    quote_config = get_whirlpool_quote_config(SOL_USDC_POOL, USDC, ui_amount)

    swap_data_dst = [
        SwapData(
            callTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            approveTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            sendingAssetId="0x" + sendingAssetId.hex(),
            receivingAssetId="0x" + receivingAssetId.hex(),
            fromAmount=quote_config["amount_in"],
            callData="0x"
            + bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii").hex(),
        ).format_to_contract()
    ]
    print("swap_data_dst\n", swap_data_dst)

    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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


def cross_swap_native_bsc():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_bsc = 1_000_000_000_000_000_000  # decimals=18

    bsc_token_approve(one_bsc * 100, so_diamond)

    so_data = SoData.create_bsc(
        receiving_token="0x"
        + b58decode("xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz").hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_bsc * 100,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []
    swap_data_dst = []
    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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


def cross_swap_native_bsc_wsol_whirlpool():
    change_network("bsc-test")
    so_diamond = "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    one_bsc = 10_000_000_000_000_000_000  # decimals=18
    # 1 BSC
    ui_amount = "10"

    bsc_token_approve(one_bsc, so_diamond)

    so_data = SoData.create_bsc(
        receiving_token="0x" + bytes([0] * 32).hex(),
        receiver="0x" + b58decode("4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9").hex(),
        amount=one_bsc,
    )
    print("SoData\n", so_data)
    so_data = so_data.format_to_contract()

    swap_data_src = []

    # Swap USDC to TEST on solana
    # Wrapped BSC is tokenA, decimal=8
    BSC = "xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"
    # TEST is tokenB
    TEST = "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"
    BSC_TEST_POOL = "AxoxjuJnpvTeqmwwjJLnuMuYLGNP1kg3orMjSuj3KBmc"
    WSOL = "So11111111111111111111111111111111111111112"
    WSOL_BSC_POOL = "6TLSV3E9aTNzJtY4DejLdhGb4wkTfM65gA3cwMESFrpY"

    sendingAssetId = bytes(Pubkey.from_string(BSC))
    receivingAssetId = bytes(Pubkey.from_string(WSOL))
    quote_config = get_whirlpool_quote_config(WSOL_BSC_POOL, BSC, ui_amount)

    swap_data_dst = [
        SwapData(
            callTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            approveTo="0x" + bytes(quote_config["whirlpool"]).hex(),
            sendingAssetId="0x" + sendingAssetId.hex(),
            receivingAssetId="0x" + receivingAssetId.hex(),
            fromAmount=quote_config["amount_in"],
            callData="0x"
            + bytes(f"Whirlpool,{quote_config['min_amount_out']}", "ascii").hex(),
        ).format_to_contract()
    ]
    print("swap_data_dst\n", swap_data_dst)

    input_eth_amount = 0
    dstMaxGasPriceInWeiForRelayer = 1
    dst_diamond_address = (
        "0x" + b58decode("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY").hex()
    )
    wormhole_data = [1, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    proxy_diamond = Contract.from_abi("WormholeFacet", so_diamond, WormholeFacet.abi)

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
    complete_swap_via_wormhole()
    # cross_swap_wrapped_wsol()
    # cross_swap_wrapped_usdc_test_whirlpool()
    # cross_swap_wrapped_usdc_wsol_whirlpool()
    # cross_swap_native_bsc()
    # cross_swap_native_bsc_wsol_whirlpool()
