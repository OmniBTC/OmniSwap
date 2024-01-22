import json
import os
import time
import urllib
from random import choice

import requests
from brownie import Contract, web3
from brownie.project.main import Project

from scripts.helpful_scripts import (
    get_account,
    zero_address,
    combine_bytes,
    padding_to_bytes,
    Session,
    get_bridge_token_address,
    get_bridge_token_decimal,
    get_chain_id,
    get_celer_chain_id,
    get_account_address,
    get_swap_info,
    to_hex_str,
)

from scripts.celer_tx_status import get_celer_transfer_status

uniswap_v3_fee_decimal = 1e6

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

src_session: Session = None
dst_session: Session = None


def get_contract(contract_name: str, p: Project = None):
    return p[contract_name]


def get_contract_address(contract_name: str, p: Project = None):
    return get_contract(contract_name, p)[-1].address


def token_approve(
    token_name: str, aprrove_address: str, amount: int, p: Project = None
):
    token = Contract.from_abi(
        token_name.upper(),
        get_bridge_token_address("celer", token_name),
        p.interface.IERC20.abi,
    )
    token.approve(aprrove_address, amount, {"from": get_account()})


def soSwapViaCeler(
    so_data,
    src_swap_data,
    celer_data,
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
        "CelerFacet", p["SoDiamond"][-1].address, p["CelerFacet"].abi
    )

    dst_max_gas_price = celer_data.dstMaxGasPriceInWeiForExecutor
    (
        src_message_fee,
        dst_executor_gas,
        src_executor_fee,
    ) = proxy_diamond.estCelerMessageFeeAndExecutorFee(
        celer_data.dstCelerChainId, dst_max_gas_price, so_data, dst_swap_data, False
    )

    estimate_cost = src_message_fee + src_executor_fee + input_eth_amount

    celer_data.update_estimate_cost(estimate_cost)
    celer_data = celer_data.format_to_contract()

    print(
        f"dst_max_gas_price: {dst_max_gas_price}\n"
        f"dst_executor_gas: {dst_executor_gas}\n"
        f"src_executor_fee: {src_executor_fee / get_bridge_token_decimal('celer','eth')}\n"
        f"src_message_fee: {src_message_fee / get_bridge_token_decimal('celer','eth')}\n"
        f"estimate_cost: {estimate_cost / get_bridge_token_decimal('celer','eth')}\n"
        f"input eth: {input_eth_amount / get_bridge_token_decimal('celer','eth')}\n"
    )

    print(f"CelerData: {celer_data}\n")
    tx = proxy_diamond.soSwapViaCeler(
        so_data,
        src_swap_data,
        celer_data,
        dst_swap_data,
        {"from": get_account(), "value": int(estimate_cost)},
    )

    print(tx.info())

    # Contract.from_abi("ICelerBridge", bridge_address, interface.ICelerBridge.abi)
    celer_transfer_id = tx.events["Send"]["transferId"].hex()
    print("celer transferId: ", celer_transfer_id)

    print("wait 30s for celer gateway")
    time.sleep(30)

    get_celer_transfer_status(celer_transfer_id)


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
                func=get_bridge_token_address,
                args=(
                    "celer",
                    sendingTokenName,
                ),
            ),
            destinationChainId=dst_session.put_task(func=get_chain_id),
            receivingAssetId=dst_session.put_task(
                func=get_bridge_token_address,
                args=(
                    "celer",
                    receiveTokenName,
                ),
            ),
            amount=amount,
        )


class CelerData(View):
    def __init__(
        self,
        sender,
        maxSlippage,
        dstCelerChainId,
        dstSoDiamond,
        srcBridgeToken,
        srcBridgeTokenDecimal,
        estimateCost,
        dstBridgeToken,
        dstBridgeTokenDecimal,
        dstMaxGasPriceInWeiForExecutor,
    ):
        # slippage tolerance, 10000 -> 1%
        self.sender = sender
        self.maxSlippage = maxSlippage
        # destination chain id
        self.dstCelerChainId = dstCelerChainId
        # destination SoDiamond address
        self.dstSoDiamond = dstSoDiamond
        self.srcBridgeToken = srcBridgeToken
        self.srcBridgeTokenDecimal = srcBridgeTokenDecimal
        self.estimateCost = estimateCost
        self.dstBridgeToken = dstBridgeToken
        self.dstBridgeTokenDecimal = dstBridgeTokenDecimal
        self.dstMaxGasPriceInWeiForExecutor = dstMaxGasPriceInWeiForExecutor

    def update_estimate_cost(self, estimateCost):
        self.estimateCost = estimateCost

    def format_to_contract(self):
        """Get the Celer data passed into the contract interface"""
        return [
            to_hex_str(self.sender),
            self.maxSlippage,
            self.dstCelerChainId,
            self.srcBridgeToken,
            self.dstMaxGasPriceInWeiForExecutor,
            self.estimateCost,
            self.dstSoDiamond,
        ]

    @classmethod
    def create(
        cls,
        src_session,
        dst_session,
        max_slippage: int,
        srcBridgeToken: str,
        estimateCost: int,
        dstBridgeToken: str,
        dstMaxGasPriceInWeiForExecutor: int,
    ):
        """Create CelerData class

        Args:
            maxSlippage (int): The celer slippage on the target chain
            srcBridgeToken (str): Name of the bridge token on the source chain
            estimateCost (int): The estimateCost = message fee(for SGN) + executor fee(for executor) + native_gas(optional)
            dstBridgeToken (str): Name of the receive token on the target chain
            dstMaxGasPriceInWeiForExecutor (int): The max gas price on destination chain

        Returns:
            CelerData: CelerData class
        """
        return CelerData(
            sender=src_session.put_task(get_account_address),
            maxSlippage=max_slippage,
            dstCelerChainId=dst_session.put_task(func=get_celer_chain_id),
            dstSoDiamond=dst_session.put_task(
                get_contract_address, args=("SoDiamond",), with_project=True
            ),
            srcBridgeToken=src_session.put_task(
                func=get_bridge_token_address,
                args=(
                    "celer",
                    srcBridgeToken,
                ),
            ),
            srcBridgeTokenDecimal=src_session.put_task(
                func=get_bridge_token_decimal,
                args=(
                    "celer",
                    srcBridgeToken,
                ),
            ),
            estimateCost=estimateCost,
            dstBridgeToken=dst_session.put_task(
                func=get_bridge_token_address,
                args=(
                    "celer",
                    dstBridgeToken,
                ),
            ),
            dstBridgeTokenDecimal=dst_session.put_task(
                func=get_bridge_token_decimal,
                args=(
                    "celer",
                    dstBridgeToken,
                ),
            ),
            dstMaxGasPriceInWeiForExecutor=dstMaxGasPriceInWeiForExecutor,
        )

    @staticmethod
    def estimate_so_fee(amount, p: Project = None):
        """Get the processing fee of the target chain Diamond

        Args:
            amount (_type_): Amount of tokens acquired from Celer in the target chain
            p (Project, optional): Load brownie project config. Defaults to None.

        Returns:
            so_fee: Fees charged by Diamond
        """
        proxy_diamond = Contract.from_abi(
            "CelerFacet", p["SoDiamond"][-1].address, p["CelerFacet"].abi
        )
        so_fee = proxy_diamond.getCelerSoFee(amount)
        print(f"  So fee rate: {so_fee / amount}")
        return so_fee


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
            to_hex_str(self.sendingAssetId),
            to_hex_str(self.receivingAssetId),
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
        swap_info = get_swap_info()[swapType]
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
                    sendingAssetId = get_bridge_token_address("celer", swapPath[0])
                receivingAssetId = get_bridge_token_address("celer", swapPath[-1])
            else:
                raise ValueError("Not support")
        else:
            path = cls.encode_path_for_uniswap_v2(swapPath)
            sendingAssetId = path[0]
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
        swap_info = get_swap_info()[swapType]
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
        return [get_bridge_token_address("celer", v) for v in p]

    @staticmethod
    def encode_path_for_uniswap_v3(p: list):
        """
        :param p: [token, fee, token, fee, token...]
        :return:
        """
        assert len(p) > 0
        assert (len(p) - 3) % 2 == 0, "p length not right"
        p = [
            padding_to_bytes(
                web3.toHex(int(p[i] * uniswap_v3_fee_decimal)), padding="left", length=3
            )
            if (i + 1) % 2 == 0
            else get_bridge_token_address("celer", p[i])
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
        swap_info = get_swap_info()[swapType]
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
            f"  Swap estimate out: token {swapPath[0]}, amount {amountIn / get_bridge_token_decimal('celer',swapPath[0])} "
            f"-> token {swapPath[-1]}, amount {amountOut / get_bridge_token_decimal('celer',swapPath[-1])}"
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
        swap_info = get_swap_info()[swapType]
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
            f"  Swap estimate in: token {swapPath[0]}, amount {amountIn / get_bridge_token_decimal('celer',swapPath[0])} "
            f"<- token {swapPath[-1]}, amount {amountOut / get_bridge_token_decimal('celer',swapPath[-1])}"
        )
        return amountIn


def celer_estimate_amount(
    amount: int, slippage_tolerance=10000  # 1%, follow maxSlippage
):
    src_chain_id = 5
    dst_chain_id = 43113
    token_symbol = "USDC"
    test_base_url = "https://cbridge-v2-test.celer.network/v2/estimateAmt"
    # main_base_url = "https://cbridge-prod2.celer.app/v2/estimateAmt"

    params = {
        "src_chain_id": src_chain_id,
        "dst_chain_id": dst_chain_id,
        "token_symbol": token_symbol,
        "usr_addr": 0x0,
        "slippage_tolerance": slippage_tolerance,
        "amt": amount,
        "is_pegged": "false",
    }

    url = test_base_url + "?" + urllib.parse.urlencode(params)

    print(f"\n  {url}\n")

    response = requests.get(url)
    data = json.loads(response.text)

    estimated_amount = int(data["estimated_receive_amt"])
    max_slippage = int(data["max_slippage"])

    return estimated_amount, max_slippage


def celer_estimate_final_token_amount(
    src_session,
    dst_session,
    amount: int,
    slippage_tolerance,
    src_swap_data: SwapData,
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

    amount, max_slippage = src_session.put_task(
        celer_estimate_amount, args=(amount, slippage_tolerance), with_project=False
    )
    so_fee = dst_session.put_task(
        CelerData.estimate_so_fee, args=(amount,), with_project=True
    )
    amount = amount - so_fee

    if dst_swap_data is not None:
        amount = dst_session.put_task(
            SwapData.estimate_out,
            args=(amount, dst_swap_data.swapType, dst_swap_data.swapPath),
            with_project=True,
        )

    print(f"Final amount: {amount}, so fee: {so_fee}")

    return amount, max_slippage


def cross_swap_via_celer(
    src_session,
    dst_session,
    inputAmount,
    sourceTokenName,  # celer
    destinationTokenName,  # celer
    sourceSwapType,
    sourceSwapFunc,
    sourceSwapPath,
    sourceBridgeToken,
    destinationBridgeToken,
    destinationSwapType,
    destinationSwapFunc,
    destinationSwapPath,
    slippage: float,
):
    print(
        f"{'-' * 100}\nSwap: {sourceTokenName}({src_session.net}) "
        f"-> {sourceBridgeToken}({src_session.net}) -> {destinationBridgeToken}({dst_session.net}) "
        f"-> {destinationTokenName}({dst_session.net})\n"
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

    final_amount, max_slippage = celer_estimate_final_token_amount(
        src_session,
        dst_session,
        inputAmount,
        int(slippage * 1000000),
        src_swap_data,
        dst_swap_data,
    )

    dstMaxGasPriceInWeiForExecutor = 25000000000  # todo: get gas price

    celer_data = CelerData.create(
        src_session,
        dst_session,
        max_slippage,  # set max_slippage=1 for refund token tests
        sourceBridgeToken,
        0,
        destinationBridgeToken,
        dstMaxGasPriceInWeiForExecutor,
    )

    dst_swap_min_amount = int(final_amount * (1 - slippage))

    print("CelerData:\n", celer_data)

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
        soSwapViaCeler,
        args=(so_data, src_swap_data, celer_data, dst_swap_data, input_eth_amount),
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


def main(src_net="goerli", dst_net="avax-test", bridge="celer"):
    global src_session
    global dst_session
    src_session = Session(
        net=src_net, project_path=root_path, name=src_net, daemon=False
    )
    dst_session = Session(
        net=dst_net, project_path=root_path, name=dst_net, daemon=False
    )

    if bridge == "celer":
        # celer swap
        cross_swap_via_celer(
            src_session=src_session,
            dst_session=dst_session,
            inputAmount=int(
                # 0.01 * src_session.put_task(get_bridge_token_decimal, args=("celer","weth",))
                10
                * src_session.put_task(
                    get_bridge_token_decimal,
                    args=(
                        "celer",
                        "usdc",
                    ),
                )
            ),
            # sourceTokenName="weth",
            sourceTokenName="usdc",
            destinationTokenName="usdc",
            # sourceSwapType=SwapType.IUniswapV2Router02,
            sourceSwapType=None,
            sourceSwapFunc=SwapFunc.swapExactTokensForTokens,
            sourceSwapPath=("weth", "usdc"),
            sourceBridgeToken="usdc",
            destinationBridgeToken="usdc",
            destinationSwapType=None,
            destinationSwapFunc=SwapFunc.swapExactTokensForTokens,
            destinationSwapPath=("usdc", "weth"),
            slippage=0.01,
        )

    else:
        # single swap
        single_swap(
            src_session=src_session,
            dst_session=src_session,
            inputAmount=int(
                0.001
                * src_session.put_task(
                    get_bridge_token_decimal,
                    args=(
                        "celer",
                        "weth",
                    ),
                )
            ),
            sendingTokenName="weth",
            receiveTokenName="usdc",
            sourceSwapType=SwapType.IUniswapV2Router02,
            sourceSwapFunc=SwapFunc.swapExactTokensForTokens,
            sourceSwapPath=("weth", "usdc"),
        )

    src_session.terminate()
    dst_session.terminate()


if __name__ == "__main__":
    main()
