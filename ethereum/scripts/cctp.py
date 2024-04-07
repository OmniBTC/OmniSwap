import json
import os
import time
from random import choice

import brownie
import ccxt
import requests
from brownie import Contract, web3, project
from brownie.project.main import Project
from retrying import retry

from helpful_scripts import (
    get_account,
    zero_address,
    combine_bytes,
    padding_to_bytes,
    Session,
    get_token_address,
    get_token_decimal,
    get_chain_id,
    get_swap_info,
    to_hex_str,
    get_account_address, get_cctp_domain_id, get_cctp_message_transmitter
)

uniswap_v3_fee_decimal = 1e6

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

src_session: Session = None
dst_session: Session = None

kucoin = ccxt.kucoin()
kucoin.load_markets()


def get_contract(contract_name: str, p: Project = None):
    return p[contract_name]


def get_contract_address(contract_name: str, p: Project = None):
    return get_contract(contract_name, p)[-1].address


def token_approve(
        token_name: str, aprrove_address: str, amount: int, p: Project = None
):
    token = Contract.from_abi(
        token_name.upper(), get_token_address(token_name), p.interface.IERC20.abi
    )
    token.approve(aprrove_address, amount, {"from": get_account()})


@retry
def get_token_price(token):
    if token == "eth":
        return float(kucoin.fetch_ticker("ETH/USDT")['close'])
    elif token == "bnb":
        return float(kucoin.fetch_ticker("BNB/USDT")['close'])
    elif token == "matic":
        return float(kucoin.fetch_ticker("MATIC/USDT")['close'])
    elif token == "avax":
        return float(kucoin.fetch_ticker("AVAX/USDT")['close'])
    elif token == "apt":
        return float(kucoin.fetch_ticker("APT/USDT")['close'])
    elif token == "sui":
        return float(kucoin.fetch_ticker("SUI/USDT")['close'])


def get_token_amount_decimal(token):
    if token in ['eth', 'matic', 'bnb', 'avax']:
        return 18
    elif token == 'apt':
        return 8
    elif token == 'sui':
        return 9


def get_network_token(network):
    if 'avax' in network:
        return 'avax'
    elif 'polygon' in network:
        return 'matic'
    else:
        return 'eth'


def get_fee_value(amount, token='sui'):
    price = get_token_price(token)
    decimal = get_token_amount_decimal(token)
    return price * amount / pow(10, decimal)


def get_fee_amount(value, token='sui'):
    price = get_token_price(token)
    decimal = get_token_amount_decimal(token)
    return int(value / price * pow(10, decimal))


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
                func=get_token_address, args=(sendingTokenName,)
            ),
            destinationChainId=dst_session.put_task(func=get_chain_id),
            receivingAssetId=dst_session.put_task(
                func=get_token_address, args=(receiveTokenName,)
            ),
            amount=amount,
        )


class CCTPData(View):
    def __init__(
            self,
            dst_domain,
            dst_diamond,
            cross_token
    ):
        self.dst_domain = dst_domain
        self.dst_diamond = dst_diamond
        self.cross_token = cross_token

    def format_to_contract(self):
        """Get the CCTP data passed into the contract interface"""
        return [
            self.dst_domain,
            padding_to_bytes(self.dst_diamond, padding='left', length=32),
            self.cross_token
        ]


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
            padding_to_bytes(
                web3.toHex(int(p[i] * uniswap_v3_fee_decimal)), padding="left", length=3
            )
            if (i + 1) % 2 == 0
            else get_token_address(p[i])
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
            f"  Swap estimate in: token {swapPath[0]}, amount {amountIn / get_token_decimal(swapPath[0])} "
            f"<- token {swapPath[-1]}, amount {amountOut / get_token_decimal(swapPath[-1])}"
        )
        return amountIn


def so_swap_via_cctp(so_data, src_swap_data, cctp_data, dst_swap_data, input_value, p: Project = None):
    account = get_account()
    proxy_diamond = Contract.from_abi(
        "CCTPFacet", p["SoDiamond"][-1].address, p["CCTPFacet"].abi
    )

    tx_receipt = proxy_diamond.soSwapViaCCTP(
        so_data.format_to_contract(),
        [] if src_swap_data is None else [src_swap_data.format_to_contract()],
        cctp_data.format_to_contract(),
        [] if dst_swap_data is None else [dst_swap_data.format_to_contract()],
        {"from": account, "value": int(input_value)},
    )
    return get_message_hash(tx_receipt.txid)


def estimate_receive_cctp_message_gas(so_data, cctp_data, dst_swap_data, p: Project = None):
    account = get_account()
    proxy_diamond = Contract.from_abi(
        "CCTPFacet", p["SoDiamond"][-1].address, p["CCTPFacet"].abi
    )

    data = so_data.format_to_contract()
    data[-1] = int(1e5)

    return proxy_diamond.estimateReceiveCCTPMessageGas(
        data,
        cctp_data.format_to_contract(),
        [] if dst_swap_data is None else [dst_swap_data.format_to_contract()],
        {
            "from": account,
        }
    )


def get_gas_price():
    return brownie.web3.eth.gas_price


def cross_swap_via_cctp(
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
        dst_swap_data = dst_session.put_task(
            SwapData.create,
            args=(
                destinationSwapType,
                destinationSwapFunc,
                inputAmount,
                destinationSwapPath,
            ),
            with_project=True,
        )
        print("DstSwapData:\n", src_swap_data)
    else:
        dst_swap_data = None

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

    dst_domain_id = dst_session.put_task(get_cctp_domain_id, with_project=False)
    cross_token = src_session.put_task(get_token_address, args=("usdc",), with_project=False)

    cctp_data = CCTPData(dst_domain_id, dst_diamond_address, cross_token)

    dst_gas = src_session.put_task(estimate_receive_cctp_message_gas, args=(so_data, cctp_data, dst_swap_data),
                                   with_project=True)

    print(f"Estimated gas: {dst_gas}")
    dst_gas_price = dst_session.put_task(get_gas_price, with_project=False)
    dst_fee_amount = dst_gas * int(dst_gas_price)
    dst_fee = get_fee_value(dst_fee_amount, get_network_token(dst_session.net))
    src_fee = get_fee_amount(dst_fee, get_network_token(src_session.net))

    input_value = input_eth_amount + src_fee

    print(f"Input value: {input_value}")

    messages = src_session.put_task(
        so_swap_via_cctp,
        args=(
            so_data,
            src_swap_data,
            cctp_data,
            dst_swap_data,
            input_value,
        ),
        with_project=True,
    )

    token_msg, token_msg_hash = messages[0]
    msg, msg_hash = messages[1]

    # complete cross swap
    # while True:
    #     try:
    #         token_attestation = get_cctp_attestation(src_session.net, token_msg_hash)
    #         attestation = get_cctp_attestation(src_session.net, msg_hash)
    #         if token_attestation == "PENDING" or attestation == "PENDING":
    #             continue
    #         dst_session.put_task(
    #             receive_cctp_message,
    #             args=(f'0x{token_msg}', token_attestation, f'0x{msg}', attestation),
    #             with_project=True
    #         )
    #         break
    #     except Exception as e:
    #         print(e)


def receive_cctp_message(token_message, token_attestation, message, attestation, p: Project = None):
    account = get_account()
    proxy_diamond = Contract.from_abi(
        "CCTPFacet", p["SoDiamond"][-1].address, p["CCTPFacet"].abi
    )
    proxy_diamond.receiveCCTPMessage(
        token_message,
        token_attestation,
        message,
        attestation,
        {"from": account,
         "gas_limit": int(100 * 1e4),
         "allow_revert": True,
         }
    )


def get_message_hash(tx_hash):
    events = brownie.chain.get_transaction(tx_hash).events
    p = project.get_loaded_projects()[-1]
    Contract.from_abi("MessageTransmitter",
                      get_cctp_message_transmitter(),
                      getattr(p.interface, "IMessageTransmitter").abi
                      )
    messages = []
    for event in dict(events).get("MessageSent", []):
        message = event["message"].hex()
        msg_hash = web3.keccak(hexstr=message)
        messages.append((message, msg_hash.hex()))
    # return [(message, message_hash)]
    return messages


@retry
def get_cctp_attestation(net, msg_hash):
    if 'test' in net:
        url = "https://iris-api-sandbox.circle.com/v1/attestations/"
    else:
        url = "https://iris-api.circle.com/v1/attestations/"

    url += msg_hash
    result = requests.get(url)
    if result.status_code == 200:
        return result.json()['attestation']
    else:
        raise ValueError(f"Get cctp attestation failed: {result.json()['status']}")


def main(src_net="avax-main", dst_net="arbitrum-main"):
    global src_session
    global dst_session
    src_session = Session(
        net=src_net, project_path=root_path, name=src_net, daemon=False
    )
    dst_session = Session(
        net=dst_net, project_path=root_path, name=dst_net, daemon=False
    )

    # without swap
    cross_swap_via_cctp(
        src_session=src_session,
        dst_session=dst_session,
        inputAmount=int(0.01 * 1e6),
        sourceTokenName="usdc",
        sourceSwapType=None,
        sourceSwapFunc=None,
        sourceSwapPath=None,
        destinationTokenName="usdc",
        destinationSwapType=None,
        destinationSwapFunc=None,
        destinationSwapPath=None,
    )

    # with src swap
    # cross_swap_via_cctp(
    #     src_session=src_session,
    #     dst_session=dst_session,
    #     inputAmount=int(0.001 * 1e6),
    #     sourceTokenName="test-usdc",
    #     sourceSwapType=SwapType.IUniswapV2Router02AVAX,
    #     sourceSwapFunc=SwapFunc.swapExactTokensForTokens,
    #     sourceSwapPath=("test-usdc", "usdc"),
    #     destinationTokenName="usdc",
    #     destinationSwapType=None,
    #     destinationSwapFunc=None,
    #     destinationSwapPath=None,
    # )

    # # with dst swap
    # cross_swap_via_cctp(
    #     src_session=src_session,
    #     dst_session=dst_session,
    #     inputAmount=int(0.001 * 1e6),
    #     sourceTokenName="usdc",
    #     sourceSwapType=None,
    #     sourceSwapFunc=None,
    #     sourceSwapPath=None,
    #     destinationTokenName="test-usdc",
    #     destinationSwapType=SwapType.IUniswapV2Router02AVAX,
    #     destinationSwapFunc=SwapFunc.swapExactTokensForTokens,
    #     destinationSwapPath=("usdc", "test-usdc"),
    # )

    src_session.terminate()
    dst_session.terminate()


if __name__ == "__main__":
    main()
