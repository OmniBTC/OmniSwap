import json
import serde
from random import choice
from typing import List
from typing import (
    NewType,
    Union,
)

HexStr = NewType("HexStr", str)
Primitives = Union[bytes, int, bool]


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


def padding_hex_to_bytes(data: str, padding="right", length=32):
    if data[:2] == "0x":
        data = data[2:]
    padding_length = length * 2 - len(data)
    if padding == "right":
        return bytes.fromhex(data + "0" * padding_length)
    else:
        return bytes.fromhex("0" * padding_length + data)


def int_to_big_endian(value: int) -> bytes:
    return value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")


def big_endian_to_int(value: bytes) -> int:
    return int.from_bytes(value, "big")


def to_int(
    primitive: Primitives = None, hexstr: HexStr = None, text: str = None
) -> int:
    """
    Converts value to its integer representation.
    Values are converted this way:

     * primitive:

       * bytes, bytearrays: big-endian integer
       * bool: True => 1, False => 0
     * hexstr: interpret hex as integer
     * text: interpret as string of digits, like '12' => 12
    """
    if hexstr is not None:
        return int(hexstr, 16)
    elif text is not None:
        return int(text)
    elif isinstance(primitive, (bytes, bytearray)):
        return big_endian_to_int(primitive)
    elif isinstance(primitive, str):
        raise TypeError("Pass in strings with keyword hexstr or text")
    elif isinstance(primitive, (int, bool)):
        return int(primitive)
    else:
        raise TypeError(
            "Invalid type.  Expected one of int/bool/str/bytes/bytearray.  Got "
            "{0}".format(type(primitive))
        )


def judge_hex_str(data: str):
    if not data.startswith("0x"):
        return False
    if len(data) % 2 != 0:
        return False
    try:
        to_int(None, data, None)
        return True
    except:
        return False


def to_hex_str(data: str, with_prefix=True):
    if judge_hex_str(data):
        return data
    if with_prefix:
        return "0x" + bytes(data, "ascii").hex()
    else:
        return bytes(data, "ascii").hex()


def hex_str_to_vector_u8(data: str) -> List[int]:
    assert judge_hex_str(data)
    return list(bytearray.fromhex(data.replace("0x", "")))


class SoData:
    def __init__(
        self,
        transactionId: bytes,
        receiver: bytes,
        sourceChainId: int,
        sendingAssetId: bytes,
        destinationChainId: int,
        receivingAssetId: bytes,
        amount: int,
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

    def __eq__(self, other):
        if isinstance(other, SoData):
            return self.__dict__ == other.__dict__

        return False

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "transactionId": "0x" + self.transactionId.hex(),
            "receiver": "0x" + self.receiver.hex(),
            "sourceChainId": self.sourceChainId,
            "sendingAssetId": "0x" + self.sendingAssetId.hex(),
            "destinationChainId": self.destinationChainId,
            "receivingAssetId": "0x" + self.receivingAssetId.hex(),
            "amount": self.amount,
        }

    def encode_normalized(self):
        data = bytearray()
        serde.serialize_vector_with_length(data, self.transactionId)
        serde.serialize_vector_with_length(data, self.receiver)
        serde.serialize_u16(data, self.sourceChainId)
        serde.serialize_vector_with_length(data, self.sendingAssetId)
        serde.serialize_u16(data, self.destinationChainId)
        serde.serialize_vector_with_length(data, self.receivingAssetId)
        serde.serialize_u256(data, self.amount)

        return bytes(data)

    def encode_compact(self):
        data = bytearray()
        serde.serialize_vector_with_compact_length(data, self.transactionId)
        serde.serialize_vector_with_compact_length(data, self.receiver)
        serde.serialize_u16(data, self.sourceChainId)
        serde.serialize_vector_with_compact_length(data, self.sendingAssetId)
        serde.serialize_u16(data, self.destinationChainId)
        serde.serialize_vector_with_compact_length(data, self.receivingAssetId)
        serde.serialize_u64(data, self.amount)

        return bytes(data)

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 8 + serde.get_vector_length(data[index : index + 8])
        transactionId = serde.deserialize_vector_with_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 8 + serde.get_vector_length(data[index : index + 8])
        receiver = serde.deserialize_vector_with_length(data[index : index + next_len])
        index = index + next_len

        next_len = 2
        sourceChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 8 + serde.get_vector_length(data[index : index + 8])
        sendingAssetId = serde.deserialize_vector_with_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 2
        destinationChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 8 + serde.get_vector_length(data[index : index + 8])
        receivingAssetId = serde.deserialize_vector_with_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 32
        amount = serde.deserialize_u256(data[index : index + next_len])
        index = index + next_len

        assert index == data_len, "EINVALID_LENGTH"

        return SoData(
            transactionId,
            receiver,
            sourceChainId,
            sendingAssetId,
            destinationChainId,
            receivingAssetId,
            amount,
        )

    @classmethod
    def decode_compact(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
        transactionId = serde.deserialize_vector_with_compact_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
        receiver = serde.deserialize_vector_with_compact_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 2
        sourceChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
        sendingAssetId = serde.deserialize_vector_with_compact_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 2
        destinationChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
        receivingAssetId = serde.deserialize_vector_with_compact_length(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 8
        amount = serde.deserialize_u64(data[index : index + next_len])
        index = index + next_len

        assert index == data_len, "EINVALID_LENGTH"

        return SoData(
            transactionId,
            receiver,
            sourceChainId,
            sendingAssetId,
            destinationChainId,
            receivingAssetId,
            amount,
        )

    @classmethod
    def padding(cls, transactionId, receiver, receivingAssetId):
        return SoData(transactionId, receiver, 0, b"", 0, receivingAssetId, 0)

    def recipient(self):
        return self.receiver

    def receiving_asset(self):
        return self.receivingAssetId


class SwapData:
    def __init__(
        self,
        callTo: bytes,
        approveTo: bytes,
        sendingAssetId: bytes,
        receivingAssetId: bytes,
        fromAmount: int,
        callData: bytes,
        swapType: str = None,
        swapFuncName: str = None,
        swapPath: list = None,
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

    def __eq__(self, other):
        if isinstance(other, SwapData):
            return self.__dict__ == other.__dict__

        return False

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "callTo": "0x" + self.callTo.hex(),
            "approveTo": "0x" + self.approveTo.hex(),
            "sendingAssetId": "0x" + self.sendingAssetId.hex(),
            "receivingAssetId": "0x" + self.receivingAssetId.hex(),
            "fromAmount": self.fromAmount,
            "callData": "0x" + self.callData.hex(),
        }

    @classmethod
    def encode_normalized(cls, swap_data_list):
        data = bytearray()
        swap_len = len(swap_data_list)

        if swap_len > 0:
            serde.serialize_u64(data, swap_len)

        for d in swap_data_list:
            serde.serialize_vector_with_length(data, d.callTo)
            serde.serialize_vector_with_length(data, d.approveTo)
            serde.serialize_vector_with_length(data, d.sendingAssetId)
            serde.serialize_vector_with_length(data, d.receivingAssetId)
            serde.serialize_u256(data, d.fromAmount)
            serde.serialize_vector_with_length(data, d.callData)

        return bytes(data)

    @classmethod
    def encode_compact_src(cls, swap_data_list):
        data = bytearray()
        swap_len = len(swap_data_list)

        if swap_len > 0:
            serde.serialize_u8(data, swap_len)

        for d in swap_data_list:
            serde.serialize_vector_with_compact_length(data, d.callTo)
            # skip approveTo
            serde.serialize_vector_with_compact_length(data, d.sendingAssetId)
            serde.serialize_vector_with_compact_length(data, d.receivingAssetId)
            serde.serialize_u64(data, d.fromAmount)
            serde.serialize_vector_with_compact_length(data, d.callData)

        return bytes(data)

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0
        swap_data_list = []

        next_len = 8
        _swap_len = serde.deserialize_u64(data[index : index + next_len])
        index = index + next_len

        while index < data_len:
            next_len = 8 + serde.get_vector_length(data[index : index + 8])
            callTo = serde.deserialize_vector_with_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 8 + serde.get_vector_length(data[index : index + 8])
            approveTo = serde.deserialize_vector_with_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 8 + serde.get_vector_length(data[index : index + 8])
            sendingAssetId = serde.deserialize_vector_with_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 8 + serde.get_vector_length(data[index : index + 8])
            receivingAssetId = serde.deserialize_vector_with_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 32
            amount = serde.deserialize_u256(data[index : index + next_len])
            index = index + next_len

            next_len = 8 + serde.get_vector_length(data[index : index + 8])
            callData = serde.deserialize_vector_with_length(
                data[index : index + next_len]
            )
            index = index + next_len

            swap_data_list.append(
                SwapData(
                    callTo,
                    approveTo,
                    sendingAssetId,
                    receivingAssetId,
                    amount,
                    callData,
                )
            )

        assert index == data_len, "EINVALID_LENGTH"

        return swap_data_list

    @classmethod
    def decode_compact_src(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0
        swap_data_list = []

        next_len = 1
        _swap_len = serde.deserialize_u8(data[index : index + next_len])
        index = index + next_len

        while index < data_len:
            next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
            callTo = serde.deserialize_vector_with_compact_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
            sendingAssetId = serde.deserialize_vector_with_compact_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
            receivingAssetId = serde.deserialize_vector_with_compact_length(
                data[index : index + next_len]
            )
            index = index + next_len

            next_len = 8
            amount = serde.deserialize_u64(data[index : index + next_len])
            index = index + next_len

            next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
            callData = serde.deserialize_vector_with_compact_length(
                data[index : index + next_len]
            )
            index = index + next_len

            swap_data_list.append(
                SwapData(
                    callTo,
                    callTo,
                    sendingAssetId,
                    receivingAssetId,
                    amount,
                    callData,
                )
            )

        assert index == data_len, "EINVALID_LENGTH"

        return swap_data_list

    @classmethod
    def padding(cls, callTo, sendingAssetId, receivingAssetId, callData):
        return SwapData(callTo, callTo, sendingAssetId, receivingAssetId, 0, callData)

    def sending_asset(self):
        return self.sendingAssetId

    def receiving_asset(self):
        return self.receivingAssetId

    def pool_address(self):
        return self.callTo


class WormholeData:
    def __init__(
        self,
        dstWormholeChainId: int,
        dstMaxGasPriceInWeiForRelayer: int,
        wormholeFee: int,
        dstSoDiamond: bytes,
    ):
        self.dstWormholeChainId = dstWormholeChainId
        self.dstMaxGasPriceInWeiForRelayer = dstMaxGasPriceInWeiForRelayer
        self.wormholeFee = wormholeFee
        self.dstSoDiamond = dstSoDiamond

    def __eq__(self, other):
        if isinstance(other, WormholeData):
            return self.__dict__ == other.__dict__

        return False

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "dstWormholeChainId": self.dstWormholeChainId,
            "dstMaxGasPriceInWeiForRelayer": self.dstMaxGasPriceInWeiForRelayer,
            "wormholeFee": self.wormholeFee,
            "dstSoDiamond": "0x" + self.dstSoDiamond.hex(),
        }

    def encode_normalized(self):
        data = bytearray()

        serde.serialize_u16(data, self.dstWormholeChainId)
        serde.serialize_u256(data, self.dstMaxGasPriceInWeiForRelayer)
        serde.serialize_u256(data, self.wormholeFee)
        serde.serialize_vector_with_length(data, self.dstSoDiamond)

        return data

    def encode_compact(self):
        data = bytearray()

        serde.serialize_u16(data, self.dstWormholeChainId)
        serde.serialize_u64(data, self.dstMaxGasPriceInWeiForRelayer)
        serde.serialize_u64(data, self.wormholeFee)
        serde.serialize_vector_with_compact_length(data, self.dstSoDiamond)

        return data

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 2
        dstWormholeChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 32
        dstMaxGasPriceInWeiForRelayer = serde.deserialize_u256(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 32
        wormholeFee = serde.deserialize_u256(data[index : index + next_len])
        index = index + next_len

        next_len = 8 + serde.get_vector_length(data[index : index + 8])
        dstSoDiamond = serde.deserialize_vector_with_length(
            data[index : index + next_len]
        )
        index = index + next_len

        assert index == data_len, "EINVALID_LENGTH"

        return WormholeData(
            dstWormholeChainId, dstMaxGasPriceInWeiForRelayer, wormholeFee, dstSoDiamond
        )

    @classmethod
    def decode_compact(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 2
        dstWormholeChainId = serde.deserialize_u16(data[index : index + next_len])
        index = index + next_len

        next_len = 8
        dstMaxGasPriceInWeiForRelayer = serde.deserialize_u64(
            data[index : index + next_len]
        )
        index = index + next_len

        next_len = 8
        wormholeFee = serde.deserialize_u64(data[index : index + next_len])
        index = index + next_len

        next_len = 1 + serde.get_vector_compact_length(data[index : index + 1])
        dstSoDiamond = serde.deserialize_vector_with_compact_length(
            data[index : index + next_len]
        )
        index = index + next_len

        assert index == data_len, "EINVALID_LENGTH"

        return WormholeData(
            dstWormholeChainId, dstMaxGasPriceInWeiForRelayer, wormholeFee, dstSoDiamond
        )


def test_wormhole_data():
    wormhole_data = WormholeData(
        1, 10000, 2389, bytes.fromhex("2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af")
    )

    encode_data = wormhole_data.encode_normalized()
    assert len(encode_data) == 94, len(encode_data)

    expect_data = bytes.fromhex(
        "00010000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000095500000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af"
    )

    assert expect_data == encode_data, encode_data.hex()

    decode_wormhole_data = wormhole_data.decode_normalized(encode_data)
    assert wormhole_data == decode_wormhole_data

    compact_data = wormhole_data.encode_compact()
    assert len(compact_data) == 39, len(compact_data)

    decode_wormhole_data = wormhole_data.decode_compact(compact_data)
    assert wormhole_data == decode_wormhole_data


def test_so_data():
    so_data = SoData(
        bytes.fromhex(
            "4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed"
        ),
        bytes.fromhex("2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"),
        1,
        b"0x1::aptos_coin::AptosCoin",
        2,
        bytes.fromhex("957Eb0316f02ba4a9De3D308742eefd44a3c1719"),
        100000000,
    )

    encode_data = so_data.encode_normalized()
    expect_data = bytes.fromhex(
        "00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100"
    )

    assert expect_data == encode_data, encode_data.hex()
    assert len(encode_data) == 166, len(encode_data)

    decode_so_data = so_data.decode_normalized(encode_data)
    assert so_data == decode_so_data

    compact_data = so_data.encode_compact()
    assert len(compact_data) == 114, len(compact_data)

    decode_so_data = so_data.decode_compact(compact_data)
    assert so_data == decode_so_data


def test_swap_data():
    swap_data_list = [
        SwapData(
            bytes.fromhex(
                "4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81"
            ),
            bytes.fromhex(
                "4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81"
            ),
            b"0x1::aptos_coin::AptosCoin",
            b"0x1::omni_bridge::XBTC",
            8900000000,
            b"0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81::curves::Uncorrelated",
        ),
        SwapData(
            bytes.fromhex("957Eb0316f02ba4a9De3D308742eefd44a3c1719"),
            bytes.fromhex("957Eb0316f02ba4a9De3D308742eefd44a3c1719"),
            bytes.fromhex("2514895c72f50d8bd4b4f9b1110f0d6bd2c97526"),
            bytes.fromhex("143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7"),
            7700000000,
            bytes.fromhex("6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"),
        ),
    ]

    encode_data = SwapData.encode_normalized(swap_data_list)
    expect_data = bytes.fromhex(
        "000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7"
    )

    assert expect_data == encode_data, encode_data.hex()

    decode_swap_data_list = SwapData.decode_normalized(encode_data)
    assert swap_data_list == decode_swap_data_list

    swap_data_src = [
        SwapData(
            bytes.fromhex(
                "0e03685f8e909053e458121c66f5a76aedc7706aa11c82f8aa952a8f2b7879a9"
            ),
            bytes.fromhex(
                "0e03685f8e909053e458121c66f5a76aedc7706aa11c82f8aa952a8f2b7879a9"
            ),
            bytes.fromhex(
                "3b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
            ),
            bytes.fromhex(
                "10a72302b3fed346d77240c165c64c7aafa5012ada611aad6ddd14829c9bd02d"
            ),
            8900000000,
            b"Whirlpool,8900000000",
        ),
    ]

    encode_data = SwapData.encode_normalized(swap_data_src)
    assert len(encode_data) == 228, len(encode_data)
    decode_swap_data_src = SwapData.decode_normalized(encode_data)
    assert decode_swap_data_src == swap_data_src

    compact_data = SwapData.encode_compact_src(swap_data_src)
    assert len(compact_data) == 129, len(compact_data)
    decode_compact_swap_data_src = SwapData.decode_compact_src(compact_data)

    assert len(decode_compact_swap_data_src) == 1, len(decode_compact_swap_data_src)

    assert decode_compact_swap_data_src == decode_swap_data_src


if __name__ == "__main__":
    test_wormhole_data()
    test_so_data()
    test_swap_data()

    # print(
    #     list(
    #         padding_hex_to_bytes(
    #             "84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc", padding="left"
    #         )
    #     )
    # )
