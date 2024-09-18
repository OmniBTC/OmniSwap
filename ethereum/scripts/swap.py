import json
import os
import time
from random import choice

from brownie import Contract, web3, network
from brownie.network import priority_fee, max_fee, gas_price
from brownie.project.main import Project
from scripts.helpful_scripts import (
    get_account,
    get_corebridge_core_chain_id,
    get_wormhole_chainid,
    zero_address,
    combine_bytes,
    padding_to_bytes,
    Session,
    get_token_address,
    get_token_decimal,
    get_chain_id,
    get_stargate_pool_id,
    get_stargate_chain_id,
    get_corebridge_chain_id,
    get_account_address,
    get_swap_info,
    to_hex_str,
)

uniswap_v3_fee_decimal = 1e6

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

src_session: Session = None
dst_session: Session = None

# if "core" in network.show_active():
#     # need to use the old fee calculation model
#     priority_fee(None)
#     max_fee(None)
#     gas_price("30 gwei")


def get_contract(contract_name: str, p: Project = None):
    return p[contract_name]


def get_contract_address(contract_name: str, p: Project = None):
    return get_contract(contract_name, p)[-1].address


def get_dst_chainid(p: Project = None):
    return get_wormhole_chainid()


def token_approve(
    token_name: str, aprrove_address: str, amount: int, p: Project = None
):
    token = Contract.from_abi(
        token_name.upper(), get_token_address(token_name), p.interface.IERC20.abi
    )
    token.approve(aprrove_address, amount, {"from": get_account()})


def soSwapViaWormhole(
    so_data,
    src_swap_data,
    wormhole_data,
    dst_swap_data,
    input_eth_amount: int,
    p: Project = None,
):
    so_data = so_data.format_to_contract()
    if src_swap_data is None:
        src_swap_data = []
    else:
        src_swap_data = [src_swap_data.format_to_contract()]

    if dst_swap_data is None:
        dst_swap_data = []
    else:
        dst_swap_data = [dst_swap_data.format_to_contract()]
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", p["SoDiamond"][-1].address, p["WormholeFacet"].abi
    )

    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, dst_swap_data
    )
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + input_eth_amount
    wormhole_data[2] = msg_value
    print(
        f"wormhole cross fee: {wormhole_fee / get_token_decimal('eth')} ether\n"
        f"relayer fee: {relayer_fee / get_token_decimal('eth')} ether\n"
        f"input eth: {input_eth_amount / get_token_decimal('eth')} ether\n"
        f"msg value: {msg_value / get_token_decimal('eth')} ether"
    )
    proxy_diamond.soSwapViaWormhole(
        so_data,
        src_swap_data,
        wormhole_data,
        dst_swap_data,
        {"from": get_account(), "value": int(msg_value)},
    )


def soSwapViaStargate(
    so_data,
    src_swap_data,
    stargate_data,
    dst_swap_data,
    input_eth_amount: int,
    p: Project = None,
):
    so_data = so_data.format_to_contract()
    if src_swap_data is None:
        src_swap_data = []
    else:
        src_swap_data = [src_swap_data.format_to_contract()]
    stargate_data = stargate_data.format_to_contract()
    if dst_swap_data is None:
        dst_swap_data = []
    else:
        dst_swap_data = [dst_swap_data.format_to_contract()]
    proxy_diamond = Contract.from_abi(
        "StargateFacet", p["SoDiamond"][-1].address, p["StargateFacet"].abi
    )

    stargate_cross_fee = proxy_diamond.getStargateFee(
        so_data, stargate_data, dst_swap_data
    )

    try:
        basic_fee = proxy_diamond.getStargateBasicFee()
    except:
        basic_fee = 0

    print(
        f"stargate cross fee: {stargate_cross_fee / get_token_decimal('eth')}, basic_fee:{basic_fee} "
        f"input eth: {input_eth_amount / get_token_decimal('eth')}"
    )
    proxy_diamond.soSwapViaStargate(
        so_data,
        src_swap_data,
        stargate_data,
        dst_swap_data,
        {
            "from": get_account(),
            "value": int(stargate_cross_fee + input_eth_amount + basic_fee),
            # "gas_limit": 1000000,
            # "allow_revert": True
        },
    )


def soSwapViaCoreBridge(
    so_data,
    src_swap_data,
    corebridge_data,
    input_eth_amount: int,
    p: Project = None,
):
    proxy_diamond = Contract.from_abi(
        "CoreBridgeFacet", p["SoDiamond"][-1].address, p["CoreBridgeFacet"].abi
    )

    if src_swap_data is None:
        src_swap_data = []
    else:
        src_swap_data = [src_swap_data.format_to_contract()]

    so_data = so_data.format_to_contract()
    print(so_data)
    print(corebridge_data)

    corebridge_cross_fee = proxy_diamond.getCoreBridgeFee(corebridge_data[1])

    try:
        basic_fee = proxy_diamond.getCoreBridgeBasicFee()
    except:
        basic_fee = 0

    print(
        f"corebridge cross fee: {corebridge_cross_fee / get_token_decimal('eth')}, basic_fee:{basic_fee} "
        f"input eth: {input_eth_amount / get_token_decimal('eth')}"
    )
    proxy_diamond.soSwapViaCoreBridge(
        so_data,
        src_swap_data,
        corebridge_data,
        {
            "from": get_account(),
            "value": int(corebridge_cross_fee + input_eth_amount + basic_fee),
            "gas_price": "30 gwei",
            # "gas_limit": 1000000,
            # "allow_revert": True
        },
    )


def swapTokensGeneric(so_data, src_swap_data, input_eth_amount: int, p: Project = None):
    so_data = so_data.format_to_contract()
    src_swap_data = [src_swap_data.format_to_contract()]
    proxy_diamond = Contract.from_abi(
        "GenericSwapFacet", p["SoDiamond"][-1].address, p["GenericSwapFacet"].abi
    )
    proxy_diamond.swapTokensGeneric(
        so_data, src_swap_data, {"from": get_account(), "value": int(input_eth_amount)}
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
            self.transactionId,
            self.receiver,
            self.sourceChainId if self.sourceChainId < 65535 else 0,
            self.sendingAssetId,
            self.destinationChainId if self.destinationChainId < 65535 else 0,
            self.receivingAssetId,
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
    def create(
        cls,
        src_session,
        dst_session,
        receiver: str,
        amount: int,
        sendingTokenName: str,
        receiveTokenName: str,
    ):
        """Create SoData class

        Args:
            receiver (str): The final recipient of the target token
            amount (int): Amount of tokens sent
            sendingTokenName (str): The name of the token sent on the source chain side, like usdt etc.
            receiveTokenName (str): The name of the token  to the target link, like usdt etc.

        Returns:
            SoData: SoData class
        """
        transactionId = cls.generate_random_bytes32()
        return SoData(
            transactionId=transactionId,
            receiver=receiver,
            sourceChainId=src_session.put_task(func=get_chain_id),
            sendingAssetId=src_session.put_task(
                func=get_token_address, args=(sendingTokenName,)
            ),
            destinationChainId=dst_session.put_task(func=get_chain_id),
            receivingAssetId=dst_session.put_task(
                func=get_token_address, args=(receiveTokenName,)
            ),
            amount=amount,
        )


class StargateData(View):
    def __init__(
        self,
        srcStargatePoolId,
        dstStargateChainId,
        dstStargatePoolId,
        minAmount,
        dstGasForSgReceive,
        dstSoDiamond,
        srcStargateToken,
        srcStargateTokenDecimal,
        dstStargateToken,
        dstStargateTokenDecimal,
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
        self.srcStargateToken = srcStargateToken
        self.srcStargateTokenDecimal = srcStargateTokenDecimal
        self.dstStargateToken = dstStargateToken
        self.dstStargateTokenDecimal = dstStargateTokenDecimal

    def format_to_contract(self):
        """Get the Stargate data passed into the contract interface"""
        return [
            self.srcStargatePoolId,
            self.dstStargateChainId,
            self.dstStargatePoolId,
            self.minAmount,
            self.dstGasForSgReceive,
            to_hex_str(self.dstSoDiamond),
        ]

    @classmethod
    def create(
        cls,
        src_session,
        dst_session,
        dstGasForSgReceive: int,
        srcStargateToken: str,
        dstStargateToken: str,
    ):
        """Create StargateData class

        Args:
            dstGasForSgReceive (int): The gas needed to call sgReceive in the target chain
            srcStargateToken (str): Name of the Token in the Stargate pool on the source chain side
            dstStargateToken (str): Name of the token in the target chain Stargate pool

        Returns:
            StargateData: StargateData class
        """
        return StargateData(
            srcStargatePoolId=src_session.put_task(
                func=get_stargate_pool_id, args=(srcStargateToken,)
            ),
            dstStargateChainId=dst_session.put_task(func=get_stargate_chain_id),
            dstStargatePoolId=dst_session.put_task(
                func=get_stargate_pool_id, args=(dstStargateToken,)
            ),
            minAmount=0,
            dstGasForSgReceive=dstGasForSgReceive,
            dstSoDiamond=dst_session.put_task(
                get_contract_address, args=("SoDiamond",), with_project=True
            ),
            srcStargateToken=srcStargateToken,
            srcStargateTokenDecimal=src_session.put_task(
                func=get_token_decimal, args=(srcStargateToken,)
            ),
            dstStargateToken=dstStargateToken,
            dstStargateTokenDecimal=dst_session.put_task(
                func=get_token_decimal, args=(dstStargateToken,)
            ),
        )

    @staticmethod
    def estimate_stargate_final_amount(stargate_data, amount, p: Project = None):
        """Estimated amount of tokens to be acquired from Stargate in the target chain

        Args:
            stargate_data (_type_): StargateData class
            amount (_type_): Amount of tokens sent to Stargate in the source chain
            p (Project, optional): Load brownie project config. Defaults to None.

        Returns:
            final_amount: Amount of tokens after processing decimal
        """
        proxy_diamond = Contract.from_abi(
            "StargateFacet", p["SoDiamond"][-1].address, p["StargateFacet"].abi
        )
        final_amount = proxy_diamond.estimateStargateFinalAmount(
            stargate_data.format_to_contract(), amount
        )
        print(
            f"  Stargate cross: token {stargate_data.srcStargateToken}, "
            f"amount:{amount / stargate_data.srcStargateTokenDecimal} -> token {stargate_data.dstStargateToken}, "
            f"amount {final_amount / stargate_data.srcStargateTokenDecimal}"
        )
        return final_amount

    @staticmethod
    def estimate_so_fee(amount, p: Project = None):
        """Get the processing fee of the target chain Diamond

        Args:
            amount (_type_): Amount of tokens acquired from Stargate in the target chain
            p (Project, optional): Load brownie project config. Defaults to None.

        Returns:
            so_fee: Fees charged by Diamond
        """
        proxy_diamond = Contract.from_abi(
            "StargateFacet", p["SoDiamond"][-1].address, p["StargateFacet"].abi
        )
        so_fee = proxy_diamond.getStargateSoFee(amount)
        print(f"  So fee rate: {so_fee / amount}")
        return so_fee

    @staticmethod
    def estimate_before_so_fee(amount, p: Project = None):
        """The minimum number of tokens should be obtained from Stargate in the target chain

        It is mainly used to calculate the slippage of the target chain stargate.

        Args:
            amount (_type_): Amount of Swap input tokens on the target chain after slippage calculation
            p (Project, optional): Load brownie project config. Defaults to None.

        Returns:
            before_so_fee: stargate minamount
        """
        proxy_diamond = Contract.from_abi(
            "StargateFacet", p["SoDiamond"][-1].address, p["StargateFacet"].abi
        )
        before_so_fee = proxy_diamond.getAmountBeforeSoFee(amount)
        print(f"  Before so fee rate: {1 - amount / before_so_fee}")
        return before_so_fee


class SwapType:
    """Interfaces that may be called"""

    IUniswapV2Router02 = "IUniswapV2Router02"
    IUniswapV2Router02AVAX = "IUniswapV2Router02AVAX"
    ISwapRouter = "ISwapRouter"


class SwapFunc:
    """Swap functions that may be called"""

    swapExactETHForTokens = "swapExactETHForTokens"
    swapExactAVAXForTokens = "swapExactAVAXForTokens"
    swapExactTokensForETH = "swapExactTokensForETH"
    swapExactTokensForAVAX = "swapExactTokensForAVAX"
    swapExactTokensForTokens = "swapExactTokensForTokens"
    exactInput = "exactInput"


class SwapData(View):
    """Constructing data for calling UniswapLike"""

    def __init__(
        self,
        callTo,
        approveTo,
        sendingAssetId,
        receivingAssetId,
        fromAmount,
        callData,
        swapType: str = None,
        swapFuncName: str = None,
        swapPath: list = None,
        swapEncodePath: list = None,
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
        return [
            to_hex_str(self.callTo),
            to_hex_str(self.approveTo),
            to_hex_str(self.sendingAssetId, False),
            to_hex_str(self.receivingAssetId, False),
            self.fromAmount,
            to_hex_str(self.callData),
        ]

    @classmethod
    def create(
        cls,
        swapType: str,
        swapFuncName: str,
        fromAmount: int,
        swapPath: list,
        p: Project = None,
    ):
        """Create SwapData class

        Args:
            swapType (str): Calling the uniswap interface type
            swapFuncName (str): Calling a specific function name
            fromAmount (int): Input amount for Swap
            swapPath (list): Token path for Swap
            p (Project, optional): Load brownie project config. Defaults to None.

        Raises:
            ValueError: Not support swapFuncName

        Returns:
            swap_data: SwapData class
        """
        if swapFuncName not in vars(SwapFunc):
            raise ValueError("Not support")
        swap_info = None
        for v in get_swap_info():
            if swapType in v:
                swap_info = v[swapType]
        swap_contract = Contract.from_abi(
            swapType, swap_info["router"], getattr(p.interface, swapType).abi
        )
        callTo = swap_contract.address
        approveTo = swap_contract.address
        minAmount = 0

        if swapType == SwapType.ISwapRouter:
            path = cls.encode_path_for_uniswap_v3(swapPath)
            if swapFuncName == "exactInput":
                if swapPath[0] == "weth":
                    sendingAssetId = zero_address()
                else:
                    sendingAssetId = get_token_address(swapPath[0])
                receivingAssetId = get_token_address(swapPath[-1])
            else:
                raise ValueError("Not support")
        else:
            path = cls.encode_path_for_uniswap_v2(swapPath)
            if swapPath[0] == "weth":
                sendingAssetId = zero_address()
            else:
                sendingAssetId = path[0]
            if swapPath[-1] == "weth":
                receivingAssetId = zero_address()
            else:
                receivingAssetId = path[-1]

        if swapFuncName in [
            SwapFunc.swapExactTokensForETH,
            SwapFunc.swapExactTokensForAVAX,
            SwapFunc.swapExactTokensForTokens,
        ]:
            callData = getattr(swap_contract, swapFuncName).encode_input(
                fromAmount,
                minAmount,
                path,
                p["SoDiamond"][-1].address,
                int(time.time() + 3000),
            )
        elif swapFuncName == SwapFunc.exactInput:
            callData = getattr(swap_contract, swapFuncName).encode_input(
                [
                    path,
                    p["SoDiamond"][-1].address,
                    int(time.time() + 3000),
                    fromAmount,
                    minAmount,
                ]
            )
        elif swapFuncName in [
            SwapFunc.swapExactETHForTokens,
            SwapFunc.swapExactAVAXForTokens,
        ]:
            callData = getattr(swap_contract, swapFuncName).encode_input(
                minAmount, path, p["SoDiamond"][-1].address, int(time.time() + 3000)
            )
        else:
            raise ValueError("Not support")
        swap_data = SwapData(
            callTo,
            approveTo,
            sendingAssetId,
            receivingAssetId,
            fromAmount,
            callData,
            swapType,
            swapFuncName,
            swapPath,
            path,
        )
        return swap_data

    @staticmethod
    def reset_min_amount(
        callData: str,
        swapType: str,
        swapFuncName: str,
        minAmount: int,
        p: Project = None,
    ):
        """Resetting the min amount of dst swap based on the results of the overall slippage calculation

        Args:
            callData (str): Calldata for target chain execution swap
            swapType (str): Calling the uniswap interface type
            swapFuncName (str): Calling a specific function name
            minAmount (int): Min amount
            p (Project, optional): Load brownie project config. Defaults to None.

        Raises:
            ValueError: not support swapType

        Returns:
            callData: Calldata after setting min amount
        """
        swap_info = None
        for v in get_swap_info():
            if swapType in v:
                swap_info = v[swapType]
        swap_contract = Contract.from_abi(
            swapType, swap_info["router"], getattr(p.interface, swapType).abi
        )
        if swapType == SwapType.ISwapRouter and swapFuncName == "exactInput":
            [params] = getattr(swap_contract, swapFuncName).decode_input(callData)
            params[4] = minAmount
            return getattr(swap_contract, swapFuncName).encode_input(params)
        elif swapType.startswith("IUniswapV2") and swapFuncName.startswith(
            "swapExactTokens"
        ):
            (fromAmount, _, path, to, deadline) = getattr(
                swap_contract, swapFuncName
            ).decode_input(callData)
            return getattr(swap_contract, swapFuncName).encode_input(
                fromAmount, minAmount, path, to, deadline
            )
        elif swapType.startswith("IUniswapV2") and (
            swapFuncName.startswith("swapExactETH")
            or swapFuncName.startswith("swapExactAVAX")
        ):
            (_, path, to, deadline) = getattr(swap_contract, swapFuncName).decode_input(
                callData
            )
            return getattr(swap_contract, swapFuncName).encode_input(
                minAmount, path, to, deadline
            )
        else:
            raise ValueError("Not support")

    @classmethod
    def encode_path_for_uniswap_v3_revert(cls, swapPath):
        return cls.encode_path_for_uniswap_v3(swapPath[::-1])

    @staticmethod
    def encode_path_for_uniswap_v2(p: list):
        return [get_token_address(v) for v in p]

    @staticmethod
    def encode_path_for_uniswap_v3(p: list):
        """
        :param p: [token, fee, token, fee, token...]
        :return:
        """
        assert len(p) > 0
        assert (len(p) - 3) % 2 == 0, "p length not right"
        p = [
            (
                padding_to_bytes(
                    web3.toHex(int(p[i] * uniswap_v3_fee_decimal)),
                    padding="left",
                    length=3,
                )
                if (i + 1) % 2 == 0
                else get_token_address(p[i])
            )
            for i in range(len(p))
        ]
        return combine_bytes(p)

    @classmethod
    def estimate_out(cls, amountIn: int, swapType: str, swapPath, p: Project = None):
        """Estimate uniswap final output amount

        Args:
            amountIn (int): swap input amount
            swapType (str): uniswap interface type
            swapPath (_type_): swap token path
            p (Project, optional): Load brownie project config. Defaults to None.

        Raises:
            ValueError: not support swapType

        Returns:
            amountOut: final output amount
        """
        account = get_account()
        swap_info = None
        for v in get_swap_info():
            if swapType in v:
                swap_info = v[swapType]
        if swapType == "ISwapRouter":
            swap_contract = Contract.from_abi(
                "IQuoter", swap_info["quoter"], getattr(p.interface, "IQuoter").abi
            )
            amountOut = swap_contract.quoteExactInput.call(
                cls.encode_path_for_uniswap_v3(swapPath), amountIn, {"from": account}
            )
        elif swapType.startswith("IUniswapV2"):
            swap_contract = Contract.from_abi(
                swapType, swap_info["router"], getattr(p.interface, swapType).abi
            )
            amountOuts = swap_contract.getAmountsOut(
                amountIn, cls.encode_path_for_uniswap_v2(swapPath)
            )
            amountOut = amountOuts[-1]
        else:
            raise ValueError("Not support")
        print(
            f"  Swap estimate out: token {swapPath[0]}, amount {amountIn / get_token_decimal(swapPath[0])} "
            f"-> token {swapPath[-1]}, amount {amountOut / get_token_decimal(swapPath[-1])}"
        )
        return amountOut

    @classmethod
    def estimate_in(cls, amountOut: int, swapType: str, swapPath, p: Project = None):
        """Estimate uniswap input amount based on output amount

        Args:
            amountOut (int): uniswap output amount
            swapType (str): uniswap interface type
            swapPath (_type_): swap token path
            p (Project, optional): load brownie project config. Defaults to None.

        Raises:
            ValueError: not support swapType

        Returns:
            amountIn: input amount
        """
        account = get_account()
        swap_info = None
        for v in get_swap_info():
            if swapType in v:
                swap_info = v[swapType]
        if swapType == "ISwapRouter":
            swap_contract = Contract.from_abi(
                "IQuoter", swap_info["quoter"], getattr(p.interface, "IQuoter").abi
            )
            amountIn = swap_contract.quoteExactOutput.call(
                cls.encode_path_for_uniswap_v3_revert(swapPath),
                amountOut,
                {"from": account},
            )
        elif swapType.startswith("IUniswapV2"):
            swap_contract = Contract.from_abi(
                swapType, swap_info["router"], getattr(p.interface, swapType).abi
            )
            amountIns = swap_contract.getAmountsIn(
                amountOut, cls.encode_path_for_uniswap_v2(swapPath)
            )
            amountIn = amountIns[0]
        else:
            raise ValueError("Not support")
        print(
            f"  Swap estimate in: token {swapPath[0]}, amount {amountIn / get_token_decimal(swapPath[0])} "
            f"<- token {swapPath[-1]}, amount {amountOut / get_token_decimal(swapPath[-1])}"
        )
        return amountIn


class WormholeData(View):
    def __init__(
        self,
        dstWormholeChainId: int,
        dstMaxGasPriceInWeiForRelayer: int,
        wormholeFee: int,
        dstSoDiamond: str,
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


def estimate_for_gas(
    so_data: SoData,
    stargate_cross_token: str,
    dst_swap_data: SwapData,
    p: Project = None,
):
    """estimate gas for sgReceive"""
    account = get_account()
    proxy_diamond = Contract.from_abi(
        "StargateFacet", p["SoDiamond"][-1].address, p["StargateFacet"].abi
    )
    return proxy_diamond.sgReceiveForGas.estimate_gas(
        so_data.format_to_contract(),
        get_stargate_pool_id(stargate_cross_token),
        [dst_swap_data.format_to_contract()] if dst_swap_data is not None else [],
        {"from": account},
    )


def estimate_final_token_amount(
    src_session,
    dst_session,
    amount: int,
    src_swap_data: SwapData,
    stargate_data,
    dst_swap_data: SwapData,
):
    """Estimate source swap output"""
    print("Estimate final token amount:")
    if src_swap_data is not None:
        amount = src_session.put_task(
            SwapData.estimate_out,
            args=(amount, src_swap_data.swapType, src_swap_data.swapPath),
            with_project=True,
        )

    amount = src_session.put_task(
        StargateData.estimate_stargate_final_amount,
        args=(stargate_data, amount),
        with_project=True,
    )
    so_fee = dst_session.put_task(
        StargateData.estimate_so_fee, args=(amount,), with_project=True
    )
    amount = amount - so_fee
    if dst_swap_data is not None:
        amount = dst_session.put_task(
            SwapData.estimate_out,
            args=(amount, dst_swap_data.swapType, dst_swap_data.swapPath),
            with_project=True,
        )
    return amount


def estimate_min_amount(
    dst_session, final_amount: int, slippage: float, dst_swap_data: SwapData
):
    print(f"Estimate min amount: slippage {slippage * 100}%")
    expect_min_amount = int(final_amount * (1 - slippage))
    if dst_swap_data is not None:
        dst_swap_min_amount = expect_min_amount
        stargate_min_amount = dst_session.put_task(
            SwapData.estimate_in,
            args=(
                expect_min_amount,
                dst_swap_data.swapType,
                # note revert!
                dst_swap_data.swapPath,
            ),
            with_project=True,
        )
        stargate_min_amount = dst_session.put_task(
            StargateData.estimate_before_so_fee,
            args=(stargate_min_amount,),
            with_project=True,
        )
    else:
        dst_swap_min_amount = None
        stargate_min_amount = dst_session.put_task(
            StargateData.estimate_before_so_fee,
            args=(expect_min_amount,),
            with_project=True,
        )
    return dst_swap_min_amount, stargate_min_amount


def cross_swap_via_wormhole(
    src_session,
    dst_session,
    inputAmount,
    sourceTokenName,
    sourceSwapType,
    sourceSwapFunc,
    sourceSwapPath,
    destinationTokenName,
    destinationSwapType,
    destinationSwapFunc,
    destinationSwapPath,
):
    print(
        f"{'-' * 100}\nSwap from: network {src_session.net}, token: {sourceTokenName}\n"
        f"{dst_session.net}, token: {destinationTokenName}"
    )
    src_diamond_address = src_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    dst_diamond_address = dst_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    print(
        f"Source diamond address: {src_diamond_address}. Destination diamond address: {dst_diamond_address}"
    )
    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=inputAmount,
        sendingTokenName=sourceTokenName,
        receiveTokenName=destinationTokenName,
    )
    print("SoData\n", so_data)

    if sourceSwapType is not None:
        src_swap_data = src_session.put_task(
            SwapData.create,
            args=(sourceSwapType, sourceSwapFunc, inputAmount, sourceSwapPath),
            with_project=True,
        )
        print("SourceSwapData:\n", src_swap_data)
    else:
        src_swap_data = None

    if destinationSwapType is not None:
        dst_swap_data: SwapData = dst_session.put_task(
            SwapData.create,
            args=(
                destinationSwapType,
                destinationSwapFunc,
                inputAmount,
                destinationSwapPath,
            ),
            with_project=True,
        )
    else:
        dst_swap_data: SwapData = None

    dst_chainid = dst_session.put_task(get_dst_chainid, with_project=True)

    dstMaxGasPriceInWeiForRelayer = 25000000000  # todo: get gas price
    wormhole_data = [dst_chainid, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]

    if dst_swap_data is not None:
        dst_swap_data.callData = dst_session.put_task(
            SwapData.reset_min_amount,
            args=(
                dst_swap_data.callData,
                dst_swap_data.swapType,
                dst_swap_data.swapFuncName,
                0,  # todo: slipage cal
            ),
            with_project=True,
        )
        print("DestinationSwapData:\n", dst_swap_data)

    if sourceTokenName != "eth":
        src_session.put_task(
            token_approve,
            args=(
                sourceTokenName,
                src_session.put_task(
                    get_contract_address, args=("SoDiamond",), with_project=True
                ),
                inputAmount,
            ),
            with_project=True,
        )
        input_eth_amount = 0
    else:
        input_eth_amount = inputAmount
    src_session.put_task(
        soSwapViaWormhole,
        args=(so_data, src_swap_data, wormhole_data, dst_swap_data, input_eth_amount),
        with_project=True,
    )


def cross_swap_via_corebridge(
    src_session,
    dst_session,
    inputAmount,
    sourceTokenName,  # corebridge
    destinationTokenName,  # corebridge
    sourceSwapType,
    sourceSwapFunc,
    sourceSwapPath,
    bridgeTokenName,
):
    print(
        f"{'-' * 100}\nSwap from: network {src_session.net}, token {sourceTokenName} "
        f"-> corebridge {sourceTokenName} -> {bridgeTokenName} to: network "
        f"{dst_session.net}, token: {destinationTokenName}"
    )
    src_diamond_address = src_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    dst_diamond_address = dst_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    print(
        f"Source diamond address: {src_diamond_address}. Destination diamond address: {dst_diamond_address}"
    )
    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=inputAmount,
        sendingTokenName=sourceTokenName,
        receiveTokenName=destinationTokenName,
    )
    print("SoData\n", so_data)

    if sourceSwapType is not None:
        src_swap_data = src_session.put_task(
            SwapData.create,
            args=(sourceSwapType, sourceSwapFunc, inputAmount, sourceSwapPath),
            with_project=True,
        )
        print("SourceSwapData:\n", src_swap_data)
    else:
        src_swap_data = None
    bridge_token = src_session.put_task(func=get_token_address, args=(bridgeTokenName,))

    remote_chain_id = get_corebridge_core_chain_id(dst_session.net)
    corebridge_data = [bridge_token, remote_chain_id, get_account_address(), False]

    if sourceTokenName != "eth":
        src_session.put_task(
            token_approve,
            args=(
                sourceTokenName,
                src_session.put_task(
                    get_contract_address, args=("SoDiamond",), with_project=True
                ),
                inputAmount,
            ),
            with_project=True,
        )
        input_eth_amount = 0
    else:
        input_eth_amount = inputAmount
    src_session.put_task(
        soSwapViaCoreBridge,
        args=(so_data, src_swap_data, corebridge_data, input_eth_amount),
        with_project=True,
    )


def cross_swap_via_stargate(
    src_session,
    dst_session,
    inputAmount,
    sourceTokenName,  # stargate
    destinationTokenName,  # stargate
    sourceSwapType,
    sourceSwapFunc,
    sourceSwapPath,
    sourceStargateToken,
    destinationStargateToken,
    destinationSwapType,
    destinationSwapFunc,
    destinationSwapPath,
    slippage,
):
    print(
        f"{'-' * 100}\nSwap from: network {src_session.net}, token {sourceTokenName} "
        f"-> stragate {sourceStargateToken} -> {destinationStargateToken} to: network "
        f"{dst_session.net}, token: {destinationTokenName}"
    )
    src_diamond_address = src_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    dst_diamond_address = dst_session.put_task(
        get_contract_address, args=("SoDiamond",), with_project=True
    )
    print(
        f"Source diamond address: {src_diamond_address}. Destination diamond address: {dst_diamond_address}"
    )
    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=inputAmount,
        sendingTokenName=sourceTokenName,
        receiveTokenName=destinationTokenName,
    )
    print("SoData\n", so_data)

    if sourceSwapType is not None:
        src_swap_data = src_session.put_task(
            SwapData.create,
            args=(sourceSwapType, sourceSwapFunc, inputAmount, sourceSwapPath),
            with_project=True,
        )
        print("SourceSwapData:\n", src_swap_data)
    else:
        src_swap_data = None

    if destinationSwapType is not None:
        dst_swap_data: SwapData = dst_session.put_task(
            SwapData.create,
            args=(
                destinationSwapType,
                destinationSwapFunc,
                inputAmount,
                destinationSwapPath,
            ),
            with_project=True,
        )
    else:
        dst_swap_data: SwapData = None

    dst_gas_for_sgReceive = dst_session.put_task(
        estimate_for_gas,
        args=(so_data, destinationStargateToken, dst_swap_data),
        with_project=True,
    )

    stargate_data = StargateData.create(
        src_session,
        dst_session,
        dst_gas_for_sgReceive,
        sourceStargateToken,
        destinationStargateToken,
    )

    final_amount = estimate_final_token_amount(
        src_session,
        dst_session,
        inputAmount,
        src_swap_data,
        stargate_data,
        dst_swap_data,
    )

    dst_swap_min_amount, stargate_min_amount = estimate_min_amount(
        dst_session, final_amount, slippage, dst_swap_data
    )

    stargate_data.minAmount = stargate_min_amount
    print("StargateData:\n", stargate_data)

    if dst_swap_data is not None:
        dst_swap_data.callData = dst_session.put_task(
            SwapData.reset_min_amount,
            args=(
                dst_swap_data.callData,
                dst_swap_data.swapType,
                dst_swap_data.swapFuncName,
                dst_swap_min_amount,
            ),
            with_project=True,
        )
        print("DestinationSwapData:\n", dst_swap_data)

    if sourceTokenName != "eth":
        src_session.put_task(
            token_approve,
            args=(
                sourceTokenName,
                src_session.put_task(
                    get_contract_address, args=("SoDiamond",), with_project=True
                ),
                inputAmount,
            ),
            with_project=True,
        )
        input_eth_amount = 0
    else:
        input_eth_amount = inputAmount
    src_session.put_task(
        soSwapViaStargate,
        args=(so_data, src_swap_data, stargate_data, dst_swap_data, input_eth_amount),
        with_project=True,
    )


def single_swap(
    src_session,
    dst_session,
    inputAmount,
    sendingTokenName,
    receiveTokenName,
    sourceSwapType,
    sourceSwapFunc,
    sourceSwapPath,
):
    print(
        f"{'-' * 100}\nnetwork {src_session.net}, single swap: token {sendingTokenName} -> {receiveTokenName}"
    )
    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=inputAmount,
        sendingTokenName=sendingTokenName,
        receiveTokenName=receiveTokenName,
    )
    print("SoData\n", so_data)
    src_swap_data = src_session.put_task(
        SwapData.create,
        args=(sourceSwapType, sourceSwapFunc, inputAmount, sourceSwapPath),
        with_project=True,
    )
    print("SourceSwapData:\n", src_swap_data)
    if sendingTokenName != "eth":
        src_session.put_task(
            token_approve,
            args=(
                sendingTokenName,
                src_session.put_task(
                    get_contract_address, args=("SoDiamond",), with_project=True
                ),
                inputAmount,
            ),
            with_project=True,
        )
        input_eth_amount = 0
    else:
        input_eth_amount = inputAmount
    src_session.put_task(
        swapTokensGeneric,
        args=(so_data, src_swap_data, input_eth_amount),
        with_project=True,
    )


def main(src_net="core-main", dst_net="bsc-main", bridge="corebridge"):
    global src_session
    global dst_session
    src_session = Session(
        net=src_net, project_path=root_path, name=src_net, daemon=False
    )
    dst_session = Session(
        net=dst_net, project_path=root_path, name=dst_net, daemon=False
    )

    if bridge == "stargate":
        # stargate swap
        cross_swap_via_stargate(
            src_session=src_session,
            dst_session=dst_session,
            inputAmount=int(
                1e-4 * src_session.put_task(get_token_decimal, args=("eth",))
            ),
            sourceTokenName="eth",  # stargate
            destinationTokenName="usdc",  # stargate
            sourceSwapType=SwapType.IUniswapV2Router02,
            sourceSwapFunc=SwapFunc.swapExactETHForTokens,
            sourceSwapPath=("weth", "usdt"),
            sourceStargateToken="usdt",
            destinationStargateToken="usdc",
            destinationSwapType=None,
            destinationSwapFunc=None,
            destinationSwapPath=("usdc", "usdc"),
            slippage=0.001,
        )

        # cross_swap_via_stargate(src_session=src_session,
        #                         dst_session=dst_session,
        #                         inputAmount=int(
        #                             1 * src_session.put_task(get_token_decimal, args=("usdc",))),
        #                         sourceTokenName="usdc",  # stargate
        #                         destinationTokenName="usdc",  # stargate
        #                         sourceSwapType=SwapType.IUniswapV2Router02AVAX,
        #                         sourceSwapFunc=SwapFunc.swapExactTokensForAVAX,
        #                         sourceSwapPath=("usdc", "weth"),
        #                         sourceStargateToken="weth",
        #                         destinationStargateToken="weth",
        #                         destinationSwapType=SwapType.IUniswapV2Router02,
        #                         destinationSwapFunc=SwapFunc.swapExactETHForTokens,
        #                         destinationSwapPath=("weth", "usdt"),
        #                         slippage=0.01)

    elif bridge == "corebridge":
        cross_swap_via_corebridge(
            src_session=src_session,
            dst_session=dst_session,
            inputAmount=int(
                1 * src_session.put_task(get_token_decimal, args=("usdt",))
            ),
            sourceTokenName="usdt",
            destinationTokenName="usdt",
            sourceSwapType=None,
            sourceSwapFunc=None,
            sourceSwapPath=(),
            bridgeTokenName="usdt",
        )

    elif bridge == "wormhole":
        # wormhole swap
        cross_swap_via_wormhole(
            src_session=src_session,
            dst_session=dst_session,
            inputAmount=int(
                1e-3 * src_session.put_task(get_token_decimal, args=("bsc-usdt",))
            ),
            sourceTokenName="bsc-usdt",
            sourceSwapType=SwapType.IUniswapV2Router02,
            sourceSwapFunc=SwapFunc.swapExactTokensForTokens,
            sourceSwapPath=("bsc-usdt", "usdc"),
            destinationTokenName="polygon-usdc",
            destinationSwapType=SwapType.IUniswapV2Router02,
            destinationSwapFunc=SwapFunc.swapExactTokensForTokens,
            destinationSwapPath=("polygon-usdc", "usdt", "avax-usdc"),
        )
    elif bridge == "swap":
        # single swap
        src_session = Session(
            net=src_net, project_path=root_path, name=src_net, daemon=False
        )
        dst_session = src_session
        single_swap(
            src_session=src_session,
            dst_session=dst_session,
            inputAmount=int(
                0.01 * src_session.put_task(get_token_decimal, args=("usdt",))
            ),
            sendingTokenName="usdt",
            receiveTokenName="eth",
            sourceSwapType=SwapType.IUniswapV2Router02,
            sourceSwapFunc=SwapFunc.swapExactTokensForETH,
            sourceSwapPath=("usdt", "weth"),
        )

        # dst_session = Session(
        #     net=dst_net, project_path=root_path, name=dst_net, daemon=False)
        # src_session = dst_session
        # single_swap(
        #     src_session=src_session,
        #     dst_session=dst_session,
        #     inputAmount=int(
        #         100 * src_session.put_task(get_token_decimal, args=("usdc",))),
        #     sendingTokenName="usdc",
        #     receiveTokenName="eth",
        #     sourceSwapType=SwapType.ISwapRouter,
        #     sourceSwapFunc=SwapFunc.exactInput,
        #     sourceSwapPath=("usdc", 0.005, "weth")
        # )

    src_session.terminate()
    dst_session.terminate()


if __name__ == "__main__":
    main()
