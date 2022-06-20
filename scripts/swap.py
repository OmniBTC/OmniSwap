import time

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config, network

from scripts.helpful_scripts import get_account, change_network, zero_address, get_contract
from random import choice

usdc_decimal = 1e6
eth_decimal = 1e18


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

    def set_dst_min_amount(self, net: str, swapFuncName: str, min_amount: int):
        change_network(net)
        swap_info = config["networks"][net]["swap"][0]
        swap_contract = Contract.from_abi(
            swap_info[1], swap_info[0], getattr(interface, swap_info[1]).abi)
        (fromAmount, _, path, to, deadline) = getattr(swap_contract, swapFuncName).decode_input(
            self.callData
        )
        self.callData = getattr(swap_contract, swapFuncName).encode_input(
            fromAmount,
            min_amount,
            path,
            to,
            deadline
        )

    @staticmethod
    def get_token_address(net: str, token_name: str):
        if token_name == "eth":
            return zero_address()
        elif token_name == "usdc":
            return config["networks"][net]["usdc"]

    @property
    def path(self):
        if hasattr(self, "_path"):
            return self._path
        else:
            return []

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
        swap_contract = Contract.from_abi(
            swap_info[1], swap_info[0], getattr(interface, swap_info[1]).abi)
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
        swap_data = SwapData(callTo, approveTo, sendingAssetId,
                             receivingAssetId, fromAmount, callData)
        setattr(swap_data, "_path", path)
        return swap_data


def estimate_for_gas(dst_net: str, so_data, dst_swap_data: list):
    """estimate gas for sgReceive"""
    account = get_account()
    change_network(dst_net)
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    return proxy_diamond.sgReceiveForGas.estimate_gas(
        so_data,
        config["networks"][dst_net]["stargate_poolid"],
        dst_swap_data,
        {"from": account}
    )


def estimate_final_token_amount(
        src_net: str,
        amount: int,
        src_path: list,
        stargate_data,
        dst_net: str,
        dst_path: list):
    change_network(src_net)
    # Estimate source swap output
    if len(src_path):
        src_swap_info = config["networks"][src_net]["swap"][0]
        src_swap_contract = Contract.from_abi(src_swap_info[1], src_swap_info[0],
                                              getattr(interface, src_swap_info[1]).abi)
        src_amount_outs = src_swap_contract.getAmountsOut(amount, src_path)
        amount = src_amount_outs[-1]
    # Estimate stargate cross output
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    amount = proxy_diamond.estimateStargateFinalAmount(stargate_data, amount)
    change_network(dst_net)
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    # compute so fee
    so_fee = proxy_diamond.getSoFee(amount)
    print(f"so fee:{so_fee / usdc_decimal} for amount:{amount / usdc_decimal}.")
    amount = amount - so_fee
    # Estimate dst swap output
    if len(dst_path):
        dst_swap_info = config["networks"][dst_net]["swap"][0]
        dst_swap_contract = Contract.from_abi(dst_swap_info[1], dst_swap_info[0],
                                              getattr(interface, dst_swap_info[1]).abi)
        dst_amount_outs = dst_swap_contract.getAmountsOut(amount, dst_path)
        amount = dst_amount_outs[-1]
    return amount


def estimate_min_amount(dst_net: str, final_amount: int, slippage: float, dst_path: list):
    change_network(dst_net)
    print(f"slippage:{slippage * 100}%")
    dst_token_min_amount = int(final_amount * (1 - slippage))

    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    if len(dst_path):
        dst_swap_info = config["networks"][dst_net]["swap"][0]
        dst_swap_contract = Contract.from_abi(dst_swap_info[1], dst_swap_info[0],
                                              getattr(interface, dst_swap_info[1]).abi)
        dst_amount_ins = dst_swap_contract.getAmountsIn(dst_token_min_amount, dst_path)

        stargate_min_amount = proxy_diamond.getAmountBeforeSoFee(dst_amount_ins[0])
    else:
        stargate_min_amount = proxy_diamond.getAmountBeforeSoFee(dst_token_min_amount)

    return dst_token_min_amount, stargate_min_amount


def support_src_swap(net: str) -> str:
    if net in ["rinkeby", "bsc-test", "polygon-test", "ftm-test"]:
        func_name = "swapExactETHForTokens"
    elif net == "avax-test":
        func_name = "swapExactAVAXForTokens"
    else:
        raise ValueError
    return func_name


def support_dst_swap(net: str) -> str:
    if net in ["rinkeby", "bsc-test", "polygon-test", "ftm-test"]:
        func_name = "swapExactTokensForETH"
    elif net == "avax-test":
        func_name = "swapExactTokensForAVAX"
    else:
        raise ValueError
    return func_name


def swap(src_net: str, dst_net: str):
    """The source chain and destination chain are the diffrent"""
    account = get_account()

    # 1. src_net:usdc --> dst_net:usdc
    print(f"from:{src_net}:usdc -> to:{dst_net}:usdc...")
    # generate so data
    usdc_amount = int(100 * usdc_decimal)
    so_data = SoData. \
        create(account, src_net, dst_net, usdc_amount, "usdc", "usdc"). \
        format_to_contract()
    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate = StargateData.create(src_net, dst_net, dst_gas)
    stargate_data = stargate.format_to_contract()

    final_amount = estimate_final_token_amount(src_net, usdc_amount, [], stargate_data, dst_net, [])
    print("esimate final token:", final_amount / usdc_decimal, "\n")

    # set dst swap slippage
    (_, starget_min_amount) = estimate_min_amount(dst_net, final_amount, 0.005, [])
    # set stargate min amount
    stargate.minAmount = starget_min_amount
    stargate_data = stargate.format_to_contract()
    print(f"stargate min amount: {starget_min_amount / usdc_decimal}")

    # # call
    change_network(src_net)

    usdc = get_contract("usdc")
    so_diamond = SoDiamond[-1]
    usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_diamond.getStargateFee(
        so_data,
        stargate_data,
        []
    )
    print("stargate cross fee:", src_fee / eth_decimal)
    proxy_diamond.soSwapViaStargate(
        so_data,
        [],
        stargate_data,
        [],
        {'from': account, 'value': src_fee}
    )

    # 2. src_net:native_token --> dst_net:usdc
    print(f"from:{src_net}:native_token -> to:{dst_net}:usdc...")
    # generate so data
    eth_amount = int(2 * 1e-10 * eth_decimal)
    so_data = SoData. \
        create(account, src_net, dst_net, eth_amount, "eth", "usdc"). \
        format_to_contract()
    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, [])
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate = StargateData.create(src_net, dst_net, dst_gas)
    stargate_data = stargate.format_to_contract()

    func_name = support_src_swap(src_net)

    src_swap = SwapData.create(src_net, func_name, eth_amount, "eth", "usdc")
    src_swap_data = [src_swap.format_to_contract()]

    final_amount = estimate_final_token_amount(src_net, eth_amount, src_swap.path, stargate_data, dst_net, [])
    print("esimate final token:", final_amount / usdc_decimal, "\n")

    # set dst swap slippage
    (_, starget_min_amount) = estimate_min_amount(
        dst_net, final_amount, 0.005, [])
    # set stargate min amount
    stargate.minAmount = starget_min_amount
    stargate_data = stargate.format_to_contract()
    print(f"stargate min amount: {starget_min_amount / usdc_decimal}")

    # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_diamond.getStargateFee(
        so_data,
        stargate_data,
        []
    )
    print("stargate cross fee:", src_fee / eth_decimal)
    proxy_diamond.soSwapViaStargate(
        so_data,
        src_swap_data,
        stargate_data,
        [],
        {'from': account, 'value': int(eth_amount + src_fee)}
    )

    # 3. src_net:usdc --> dst_net:native_token
    print(f"from:{src_net}:usdc -> to:{dst_net}:native_token...")
    # generate so data
    usdc_amount = int(100 * usdc_decimal)
    so_data = SoData. \
        create(account, src_net, dst_net, usdc_amount, "usdc", "eth"). \
        format_to_contract()

    func_name = support_dst_swap(dst_net)

    # generate dst swap data
    # The fromAmount of dst swap fill in casually
    dst_swap = SwapData.create(dst_net, func_name, 0, "usdc", "eth")
    dst_swap_data = [dst_swap.format_to_contract()]

    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, dst_swap_data)
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate = StargateData.create(src_net, dst_net, dst_gas)
    stargate_data = stargate.format_to_contract()

    final_amount = estimate_final_token_amount(src_net, usdc_amount, [], stargate_data, dst_net,
                                               dst_swap.path)
    print("esimate final token:", final_amount / eth_decimal, "\n")

    # set dst swap slippage
    (dst_swap_min_amount, starget_min_amount) = estimate_min_amount(
        dst_net, final_amount, 0.005, dst_swap.path)
    # set stargate min amount
    stargate.minAmount = starget_min_amount
    stargate_data = stargate.format_to_contract()
    print(f"stargate min amount: {starget_min_amount / usdc_decimal}")
    # set dst swap min amount
    dst_swap.set_dst_min_amount(dst_net, func_name, dst_swap_min_amount)
    dst_swap_data = [dst_swap.format_to_contract()]
    print(
        f"dst swap min amount(min final token): {dst_swap_min_amount / eth_decimal}")

    # # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    usdc = get_contract("usdc")
    usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)

    # get stargate cross fee
    src_fee = proxy_diamond.getStargateFee(
        so_data,
        stargate_data,
        dst_swap_data
    )
    print("stargate cross fee:", src_fee / eth_decimal)

    proxy_diamond.soSwapViaStargate(
        so_data,
        [],
        stargate_data,
        dst_swap_data,
        {'from': account, 'value': src_fee}
    )

    # 4. src_net:native_token --> dst_net:native_token
    print(f"from:{src_net}:native_token -> to:{dst_net}:native_token...")
    # generate so data
    eth_amount = int(2 * 1e-10 * eth_decimal)
    so_data = SoData. \
        create(account, src_net, dst_net, eth_amount, "eth", "eth"). \
        format_to_contract()

    # generate destination swap data
    dst_func_name = support_dst_swap(dst_net)

    # generate dst swap data
    # The fromAmount of dst swap fill in casually
    dst_swap = SwapData.create(dst_net, dst_func_name, 0, "usdc", "eth")
    dst_swap_data = [dst_swap.format_to_contract()]

    # estimate gas for sgReceive
    dst_gas = estimate_for_gas(dst_net, so_data, dst_swap_data)
    print("dst gas for sgReceive:", dst_gas)
    # generate stargate data
    stargate = StargateData.create(src_net, dst_net, dst_gas)
    stargate_data = stargate.format_to_contract()

    # generate srouce swap data
    src_func_name = support_src_swap(src_net)

    src_swap = SwapData.create(
        src_net, src_func_name, eth_amount, "eth", "usdc")
    src_swap_data = [src_swap.format_to_contract()]

    final_amount = estimate_final_token_amount(src_net, eth_amount, src_swap.path, stargate_data, dst_net,
                                               dst_swap.path)
    print("esimate final token:", final_amount / eth_decimal, "\n")

    # set dst swap slippage
    (dst_swap_min_amount, starget_min_amount) = estimate_min_amount(
        dst_net, final_amount, 0.005, dst_swap.path)
    # set stargate min amount
    stargate.minAmount = starget_min_amount
    stargate_data = stargate.format_to_contract()
    print(f"stargate min amount: {starget_min_amount / usdc_decimal}")
    # set dst swap min amount
    dst_swap.set_dst_min_amount(dst_net, dst_func_name, dst_swap_min_amount)
    dst_swap_data = [dst_swap.format_to_contract()]
    print(
        f"dst swap min amount(min final token): {dst_swap_min_amount / eth_decimal}")

    # # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    # get stargate cross fee
    src_fee = proxy_diamond.getStargateFee(
        so_data,
        stargate_data,
        dst_swap_data
    )
    print("stargate cross fee:", src_fee / eth_decimal)
    proxy_diamond.soSwapViaStargate(
        so_data,
        src_swap_data,
        stargate_data,
        dst_swap_data,
        {'from': account, 'value': int(src_fee + eth_amount)}
    )


def single_swap():
    """The source chain and destination chain are the same"""
    account = get_account()
    src_net = network.show_active()
    dst_net = src_net
    eth_amount = int(2 * 1e-10 * eth_decimal)
    so_data = SoData. \
        create(account, src_net, dst_net, eth_amount, "eth", "usdc"). \
        format_to_contract()

    func_name = support_src_swap(src_net)

    src_swap = SwapData.create(src_net, func_name, eth_amount, "eth", "usdc")
    src_swap_data = [src_swap.format_to_contract()]

    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "GenericSwapFacet", so_diamond.address, GenericSwapFacet.abi)
    proxy_diamond.swapTokensGeneric(
        so_data,
        src_swap_data,
        {'from': account, 'value': int(eth_amount)}
    )
