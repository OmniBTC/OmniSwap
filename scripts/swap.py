import time

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config

from scripts.helpful_scripts import get_account, change_network, zero_address, get_contract
from random import choice


class SoData:
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
        return [self.transactionId,
                self.receiver,
                self.sourceChainId,
                self.sendingAssetId,
                self.destinationChainId,
                self.receivingAssetId,
                self.amount]

    @staticmethod
    def generate_random_bytes32():
        chars = [str(i) for i in range(10)] + ["a", "b", "c", "d", "e"]
        result = "0x"
        for _ in range(64):
            result += choice(chars)
        return result

    @staticmethod
    def get_token_address(net: str, token_name: str):
        if token_name == "eth":
            return zero_address()
        elif token_name == "usdc":
            return config["networks"][net]["usdc"]

    @classmethod
    def create(cls, receiver: str, src_net: str, dst_net: str, amount: int,
               sendingTokenName: str, receiveTokenName: str):
        transactionId = cls.generate_random_bytes32()
        return SoData(
            transactionId=transactionId,
            receiver=receiver,
            sourceChainId=config["networks"][src_net]["chainid"],
            sendingAssetId=cls.get_token_address(src_net, sendingTokenName),
            destinationChainId=config["networks"][dst_net]["chainid"],
            receivingAssetId=cls.get_token_address(dst_net, receiveTokenName),
            amount=amount
        )


class StargateData:
    def __init__(self,
                 srcStargatePoolId,
                 dstStargateChainId,
                 dstStargatePoolId,
                 minAmount,
                 dstGasForSgReceive,
                 dstSoDiamond
                 ):
        # The stargate pool id of the source chain
        self.srcStargatePoolId = srcStargatePoolId
        # The stargate chain id of the destination chain
        self.dstStargateChainId = dstStargateChainId
        # The stargate pool id of the destination chain
        self.dstStargatePoolId = dstStargatePoolId
        # The stargate min amount
        self.minAmount = minAmount
        # destination gas for sgReceive
        self.dstGasForSgReceive = dstGasForSgReceive
        # destination SoDiamond address
        self.dstSoDiamond = dstSoDiamond

    def format_to_contract(self):
        return [self.srcStargatePoolId,
                self.dstStargateChainId,
                self.dstStargatePoolId,
                self.minAmount,
                self.dstGasForSgReceive,
                self.dstSoDiamond]

    @classmethod
    def create(cls, src_net: str, dst_net: str, dstGasForSgReceive: int):
        change_network(dst_net)
        return StargateData(
            srcStargatePoolId=config["networks"][src_net]["stargate_poolid"],
            dstStargateChainId=config["networks"][dst_net]["stargate_chainid"],
            dstStargatePoolId=config["networks"][dst_net]["stargate_poolid"],
            minAmount=0,
            dstGasForSgReceive=dstGasForSgReceive,
            dstSoDiamond=SoDiamond[-1].address
        )


class SwapData:
    def __init__(self,
                 callTo,
                 approveTo,
                 sendingAssetId,
                 receivingAssetId,
                 fromAmount,
                 callData
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
        return [self.callTo,
                self.approveTo,
                self.sendingAssetId,
                self.receivingAssetId,
                self.fromAmount,
                self.callData]

    @staticmethod
    def get_token_address(net: str, token_name: str):
        if token_name == "eth":
            return zero_address()
        elif token_name == "usdc":
            return config["networks"][net]["usdc"]

    @classmethod
    def create(cls, net: str, swapFuncName: str, fromAmount: int, sendingTokenName: str,
               receiveTokenName: str):
        support_swap_funcs = ["swapExactETHForTokens", "swapExactAVAXForTokens", "swapExactTokensForETH",
                              "swapExactTokensForAVAX", "swapExactTokensForTokens"]
        support_token_name = ["eth", "usdc"]
        if swapFuncName not in support_swap_funcs:
            raise ValueError("swapFuncName not support!")
        if sendingTokenName not in support_token_name:
            raise ValueError("sendingTokenName not support!")
        if receiveTokenName not in support_token_name:
            raise ValueError("receiveTokenName not support!")
        change_network(net)
        so_diamond = SoDiamond[-1]
        swap_info = config["networks"][net]["swap"][0]
        swap_contract = Contract.from_abi(swap_info[1], swap_info[0], getattr(interface, swap_info[1]).abi)
        callTo = swap_contract.address
        approveTo = swap_contract.address
        sendingAssetId = cls.get_token_address(net, sendingTokenName)
        receivingAssetId = cls.get_token_address(net, receiveTokenName)
        # Uniformly set to 0 for easy testing
        minAmount = 0
        path = []
        if sendingAssetId == zero_address():
            path.append(config["networks"][net]["weth"])
        else:
            path.append(sendingAssetId)
        if receivingAssetId == zero_address():
            path.append(config["networks"][net]["weth"])
        else:
            path.append(receivingAssetId)
        if swapFuncName in ["swapExactTokensForETH", "swapExactTokensForAVAX", "swapExactTokensForTokens"]:
            callData = getattr(swap_contract, swapFuncName).encode_input(
                fromAmount,
                minAmount,
                path,
                so_diamond.address,
                int(time.time() + 3000)
            )
        else:
            callData = getattr(swap_contract, swapFuncName).encode_input(
                minAmount,
                path,
                so_diamond.address,
                int(time.time() + 3000)
            )
        return SwapData(callTo, approveTo, sendingAssetId, receivingAssetId, fromAmount, callData)


def estimate_for_gas(dst_net: str, so_data, dst_swap_data: list):
    """estimate gas for sgReceive"""
    account = get_account()
    change_network(dst_net)
    so_diamond = SoDiamond[-1]
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    return proxy_stargate.sgReceiveForGas.estimate_gas(
        so_data,
        config["networks"][dst_net]["stargate_poolid"],
        dst_swap_data,
        {"from": account}
    )


def swap(src_net: str, dst_net: str):
    account = get_account()

    # 1. src_net:usdc --> dst_net:usdc
    print(f"from:{src_net}:usdc -> to:{dst_net}:usdc...")
    # generate so data
    usdc_amount = int(100 * 1e6)
    so_data = SoData. \
        create(account, src_net, dst_net, usdc_amount, "usdc", "usdc"). \
        format_to_contract()
    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate_data = StargateData.create(src_net, dst_net, dst_gas).format_to_contract()
    # # call
    change_network(src_net)

    usdc = get_contract("usdc")
    so_diamond = SoDiamond[-1]
    usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_stargate.getStargateFee(
        so_data,
        stargate_data,
        []
    )
    print("stargate cross fee:", src_fee)
    proxy_stargate.soSwapViaStargate(
        so_data,
        [],
        stargate_data,
        [],
        {'from': account, 'value': src_fee}
    )

    # 2. src_net:native_token --> dst_net:usdc
    print(f"from:{src_net}:native_token -> to:{dst_net}:usdc...")
    # generate so data
    eth_amount = int(2 * 1e-10 * 1e18)
    so_data = SoData. \
        create(account, src_net, dst_net, eth_amount, "eth", "usdc"). \
        format_to_contract()
    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate_data = StargateData.create(src_net, dst_net, dst_gas).format_to_contract()
    if src_net == "rinkeby":
        func_name = "swapExactETHForTokens"
    elif src_net == "avax-test":
        func_name = "swapExactAVAXForTokens"
    else:
        raise ValueError
    src_swap_data = [SwapData.create(src_net, func_name, eth_amount, "eth", "usdc").format_to_contract()]

    # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_stargate.getStargateFee(
        so_data,
        stargate_data,
        []
    )
    print("stargate cross fee:", src_fee)
    proxy_stargate.soSwapViaStargate(
        so_data,
        src_swap_data,
        stargate_data,
        [],
        {'from': account, 'value': int(eth_amount + src_fee)}
    )

    # 3. src_net:usdc --> dst_net:native_token
    print(f"from:{src_net}:usdc -> to:{dst_net}:native_token...")
    # generate so data
    usdc_amount = int(100 * 1e6)
    so_data = SoData. \
        create(account, src_net, dst_net, usdc_amount, "usdc", "eth"). \
        format_to_contract()

    if dst_net == "rinkeby":
        func_name = "swapExactTokensForETH"
    elif dst_net == "avax-test":
        func_name = "swapExactTokensForAVAX"
    else:
        raise ValueError
    # generate dst swap data
    # The fromAmount of dst swap fill in casually
    dst_swap_data = [SwapData.create(dst_net, func_name, 0, "usdc", "eth").format_to_contract()]

    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate_data = StargateData.create(src_net, dst_net, dst_gas).format_to_contract()

    # # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    usdc = get_contract("usdc")
    usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_stargate.getStargateFee(
        so_data,
        stargate_data,
        dst_swap_data
    )
    print("stargate cross fee:", src_fee)
    proxy_stargate.soSwapViaStargate(
        so_data,
        [],
        stargate_data,
        dst_swap_data,
        {'from': account, 'value': src_fee}
    )

    # 4. src_net:native_token --> dst_net:native_token
    print(f"from:{src_net}:native_token -> to:{dst_net}:native_token...")
    # generate so data
    eth_amount = int(2 * 1e-10 * 1e18)
    so_data = SoData. \
        create(account, src_net, dst_net, eth_amount, "eth", "eth"). \
        format_to_contract()

    # generate destination swap data
    if dst_net == "rinkeby":
        func_name = "swapExactTokensForETH"
    elif dst_net == "avax-test":
        func_name = "swapExactTokensForAVAX"
    else:
        raise ValueError
    # generate dst swap data
    # The fromAmount of dst swap fill in casually
    dst_swap_data = [SwapData.create(dst_net, func_name, 0, "usdc", "eth").format_to_contract()]

    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate_data = StargateData.create(src_net, dst_net, dst_gas).format_to_contract()

    # generate srouce swap data
    if src_net == "rinkeby":
        func_name = "swapExactETHForTokens"
    elif src_net == "avax-test":
        func_name = "swapExactAVAXForTokens"
    else:
        raise ValueError
    src_swap_data = [SwapData.create(src_net, func_name, eth_amount, "eth", "usdc").format_to_contract()]
    # # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_stargate.getStargateFee(
        so_data,
        stargate_data,
        dst_swap_data
    )
    print("stargate cross fee:", src_fee)
    proxy_stargate.soSwapViaStargate(
        so_data,
        src_swap_data,
        stargate_data,
        dst_swap_data,
        {'from': account, 'value': int(src_fee + eth_amount)}
    )


def main():
    swap("rinkeby", "avax-test")
