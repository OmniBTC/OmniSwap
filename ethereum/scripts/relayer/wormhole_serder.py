import json
from typing import Union

from base58 import b58encode

from scripts.relayer import omniswap_serde
from eth_utils import keccak


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
        omniswap_serde.serialize_vector_with_length(data, self.transactionId)
        omniswap_serde.serialize_vector_with_length(data, self.receiver)
        omniswap_serde.serialize_u16(data, self.sourceChainId)
        omniswap_serde.serialize_vector_with_length(data, self.sendingAssetId)
        omniswap_serde.serialize_u16(data, self.destinationChainId)
        omniswap_serde.serialize_vector_with_length(data, self.receivingAssetId)
        omniswap_serde.serialize_u256(data, self.amount)

        return bytes(data)

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
        transactionId = omniswap_serde.deserialize_vector_with_length(
            data[index: index + next_len]
        )
        index = index + next_len

        next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
        receiver = omniswap_serde.deserialize_vector_with_length(data[index: index + next_len])
        index = index + next_len

        next_len = 2
        sourceChainId = omniswap_serde.deserialize_u16(data[index: index + next_len])
        index = index + next_len

        next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
        sendingAssetId = omniswap_serde.deserialize_vector_with_length(
            data[index: index + next_len]
        )
        index = index + next_len

        next_len = 2
        destinationChainId = omniswap_serde.deserialize_u16(data[index: index + next_len])
        index = index + next_len

        next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
        receivingAssetId = omniswap_serde.deserialize_vector_with_length(
            data[index: index + next_len]
        )
        index = index + next_len

        next_len = 32
        amount = omniswap_serde.deserialize_u256(data[index: index + next_len])
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
            omniswap_serde.serialize_u64(data, swap_len)

        for d in swap_data_list:
            omniswap_serde.serialize_vector_with_length(data, d.callTo)
            omniswap_serde.serialize_vector_with_length(data, d.approveTo)
            omniswap_serde.serialize_vector_with_length(data, d.sendingAssetId)
            omniswap_serde.serialize_vector_with_length(data, d.receivingAssetId)
            omniswap_serde.serialize_u256(data, d.fromAmount)
            omniswap_serde.serialize_vector_with_length(data, d.callData)

        return bytes(data)

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0
        swap_data_list = []

        next_len = 8
        _swap_len = omniswap_serde.deserialize_u64(data[index: index + next_len])
        index = index + next_len

        while index < data_len:
            next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
            callTo = omniswap_serde.deserialize_vector_with_length(
                data[index: index + next_len]
            )
            index = index + next_len

            next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
            approveTo = omniswap_serde.deserialize_vector_with_length(
                data[index: index + next_len]
            )
            index = index + next_len

            next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
            sendingAssetId = omniswap_serde.deserialize_vector_with_length(
                data[index: index + next_len]
            )
            index = index + next_len

            next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
            receivingAssetId = omniswap_serde.deserialize_vector_with_length(
                data[index: index + next_len]
            )
            index = index + next_len

            next_len = 32
            amount = omniswap_serde.deserialize_u256(data[index: index + next_len])
            index = index + next_len

            next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
            callData = omniswap_serde.deserialize_vector_with_length(
                data[index: index + next_len]
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
    def padding(cls, callTo, sendingAssetId, receivingAssetId, callData):
        return SwapData(callTo, callTo, sendingAssetId, receivingAssetId, 0, callData)


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

        omniswap_serde.serialize_u16(data, self.dstWormholeChainId)
        omniswap_serde.serialize_u256(data, self.dstMaxGasPriceInWeiForRelayer)
        omniswap_serde.serialize_u256(data, self.wormholeFee)
        omniswap_serde.serialize_vector_with_length(data, self.dstSoDiamond)

        return data

    @classmethod
    def decode_normalized(cls, data: bytes):
        data_len = len(data)
        assert data_len > 0, "EINVALID_LENGTH"

        index = 0

        next_len = 2
        dstWormholeChainId = omniswap_serde.deserialize_u16(data[index: index + next_len])
        index = index + next_len

        next_len = 32
        dstMaxGasPriceInWeiForRelayer = omniswap_serde.deserialize_u256(
            data[index: index + next_len]
        )
        index = index + next_len

        next_len = 32
        wormholeFee = omniswap_serde.deserialize_u256(data[index: index + next_len])
        index = index + next_len

        next_len = 8 + omniswap_serde.get_vector_length(data[index: index + 8])
        dstSoDiamond = omniswap_serde.deserialize_vector_with_length(
            data[index: index + next_len]
        )
        index = index + next_len

        assert index == data_len, "EINVALID_LENGTH"

        return WormholeData(
            dstWormholeChainId, dstMaxGasPriceInWeiForRelayer, wormholeFee, dstSoDiamond
        )


class ParsedVaa:
    def __init__(
            self,
            version,
            guardian_set_index,
            guardian_signatures,
            timestamp,
            nonce,
            emitter_chain,
            emitter_address,
            sequence,
            consistency_level,
            payload,
            hash,
    ):
        self.version = version
        self.guardian_set_index = guardian_set_index
        self.guardian_signatures = guardian_signatures
        self.timestamp = timestamp
        self.nonce = nonce
        self.emitter_chain = emitter_chain
        self.emitter_address = emitter_address
        self.sequence = sequence
        self.consistency_level = consistency_level
        self.payload = payload
        self.hash = hash

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "version": self.version,
            "guardianSetIndex": self.guardian_set_index,
            "guardianSignatures": [
                {"index": g["index"], "signature": "0x" + g["signature"].hex()}
                for g in self.guardian_signatures
            ],
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "emitterChain": self.emitter_chain,
            "emitterAddress": "0x" + self.emitter_address.hex(),
            "sequence": self.sequence,
            "consistencyLevel": self.consistency_level,
            "payload": "0x" + self.payload.hex(),
            "hash": "0x" + self.hash.hex(),
        }

    @classmethod
    def parse(cls, vaa: Union[bytes, str]):
        if isinstance(vaa, str):
            signed_vaa = bytearray(bytes.fromhex(vaa.replace("0x", "")))
        else:
            signed_vaa = bytearray(vaa)

        sig_start = 6
        num_signers = signed_vaa[5]
        sig_length = 66

        guardian_signatures = []
        for i in range(num_signers):
            start = sig_start + i * sig_length
            guardian_signatures.append(
                {
                    "index": signed_vaa[start],
                    "signature": bytes(signed_vaa[start + 1: start + 66]),
                }
            )

        body = signed_vaa[sig_start + sig_length * num_signers:]

        return ParsedVaa(
            signed_vaa[0],
            int.from_bytes(signed_vaa[1:5], byteorder="big"),
            guardian_signatures,
            int.from_bytes(body[0:4], byteorder="big"),
            int.from_bytes(body[4:8], byteorder="big"),
            int.from_bytes(body[8:10], byteorder="big"),
            bytes(body[10:42]),
            int.from_bytes(body[42:50], byteorder="big"),
            body[50],
            bytes(body[51:]),
            keccak(body),
        )


class ParsedTransfer:
    Transfer = 1
    AttestMeta = 2
    TransferWithPayload = 3

    def __init__(
            self,
            payload_type,
            amount,
            token_address,
            token_chain,
            redeemer,
            redeemer_chain,
            fee,
            from_emitter,
            transfer_payload,
    ):
        self.payload_type = payload_type
        self.amount = amount
        self.token_address = token_address
        self.token_chain = token_chain
        self.redeemer = redeemer
        self.redeemer_chain = redeemer_chain
        self.fee = fee
        self.from_emitter = from_emitter
        self.transfer_payload = transfer_payload

        self.parsed_transfer_payload = ParsedTransferPayload.parse(
            self.transfer_payload
        )

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "payloadType": self.payload_type,
            "amount": self.amount,
            "tokenAddress": b58encode(self.token_address).decode("utf-8")
            if self.token_chain == 1
            else "0x" + self.token_address.hex(),
            "tokenChain": self.token_chain,
            "redeemer": b58encode(self.redeemer).decode("utf-8")
            if self.redeemer_chain == 1
            else "0x" + self.redeemer.hex(),
            "redeemerChain": self.redeemer_chain,
            "fee": self.fee,
            "fromEmitter": "0x" + self.from_emitter.hex(),
            "TransferPayload": "0x" + self.transfer_payload.hex(),
            "recipient": b58encode(self.recipient()).decode()
            if self.redeemer_chain == 1
            else "0x" + self.recipient().hex(),
        }

    @classmethod
    def parse(cls, payload: Union[bytes, str]):
        if isinstance(payload, str):
            payload = bytes.fromhex(payload.replace("0x", ""))

        payload_type = payload[0]
        if payload_type not in (cls.Transfer, cls.TransferWithPayload):
            raise ValueError("not token bridge transfer VAA")

        amount_bytes = payload[1:33]
        amount = int.from_bytes(amount_bytes, byteorder="big")

        token_address = payload[33:65]

        token_chain_bytes = payload[65:67]
        token_chain = int.from_bytes(token_chain_bytes, byteorder="big")

        redeemer = payload[67:99]

        redeemer_chain_bytes = payload[99:101]
        redeemer_chain = int.from_bytes(redeemer_chain_bytes, byteorder="big")

        if payload_type == cls.Transfer:
            fee_bytes = payload[101:133]
            fee = int.from_bytes(fee_bytes, byteorder="big")
        else:
            fee = None

        if payload_type == cls.TransferWithPayload:
            from_emitter = payload[101:133]
        else:
            from_emitter = None

        transfer_payload = payload[133:]

        return ParsedTransfer(
            payload_type,
            amount,
            token_address,
            token_chain,
            redeemer,
            redeemer_chain,
            fee,
            from_emitter,
            transfer_payload,
        )

    def recipient(self):
        recipient = self.parsed_transfer_payload.so_data.recipient()

        return recipient


class ParsedTransferPayload:
    # CrossData
    # 1. dst_max_gas_price INTER_DELIMITER
    # 2. dst_max_gas INTER_DELIMITER
    # 3. transactionId(SoData) INTER_DELIMITER
    # 4. receiver(SoData) INTER_DELIMITER
    # 5. receivingAssetId(SoData) INTER_DELIMITER
    # 6. swapDataLength(u8) INTER_DELIMITER
    # 7. callTo(SwapData) INTER_DELIMITER
    # 8. sendingAssetId(SwapData) INTER_DELIMITER
    # 9. receivingAssetId(SwapData) INTER_DELIMITER
    # 10. callData(SwapData)
    def __init__(self, dst_max_gas_price, dst_max_gas, so_data, swap_data_list):
        self.dst_max_gas_price = dst_max_gas_price
        self.dst_max_gas = dst_max_gas
        self.so_data = so_data
        self.swap_data_list = swap_data_list

    def __str__(self):
        return json.dumps(self.format_json(), indent=2)

    def format_json(self):
        return {
            "dst_max_gas_price": self.dst_max_gas_price,
            "dst_max_gas": self.dst_max_gas,
            "so_data": self.so_data.format_json(),
            "swap_data_list": [
                swap_data.format_json() for swap_data in self.swap_data_list
            ],
        }

    @classmethod
    def parse(cls, payload: Union[bytes, str]):
        if isinstance(payload, str):
            payload = bytes.fromhex(payload.replace("0x", ""))

        data_len = len(payload)
        assert data_len > 0, "empty payload"

        index = 0

        next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
        index = index + 1
        dst_max_gas_price = omniswap_serde.deserialize_u256_with_hex_str(
            payload[index: index + next_len]
        )
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
        index = index + 1
        dst_max_gas = omniswap_serde.deserialize_u256_with_hex_str(
            payload[index: index + next_len]
        )
        index = index + next_len

        # SoData
        next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
        index = index + 1
        so_transaction_id = payload[index: index + next_len]
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
        index = index + 1
        so_receiver = payload[index: index + next_len]
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
        index = index + 1
        so_receiving_asset_id = payload[index: index + next_len]
        index = index + next_len

        so_data = SoData.padding(so_transaction_id, so_receiver, so_receiving_asset_id)

        # Skip len
        if index < data_len:
            next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
            index = index + 1
            index = index + next_len

        # SwapData
        swap_data_list = []
        while index < data_len:
            next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
            index = index + 1
            swap_call_to = payload[index: index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
            index = index + 1
            swap_sending_asset_id = payload[index: index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u8(payload[index: index + 1])
            index = index + 1
            swap_receiving_asset_id = payload[index: index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u16(payload[index: index + 2])
            index = index + 2
            swap_call_data = payload[index: index + next_len]
            index = index + next_len

            swap_data_list.append(
                SwapData.padding(
                    swap_call_to,
                    swap_sending_asset_id,
                    swap_receiving_asset_id,
                    swap_call_data,
                )
            )

        return ParsedTransferPayload(
            dst_max_gas_price, dst_max_gas, so_data, swap_data_list
        )


def parseTransferWithPayloadVaa(vaa: Union[bytes, str]):
    parsed_vaa = ParsedVaa.parse(vaa)
    parsed_transfer = ParsedTransfer.parse(parsed_vaa.payload)
    parsed_transfer_payload = ParsedTransferPayload.parse(
        parsed_transfer.transfer_payload
    )

    return parsed_vaa, parsed_transfer, parsed_transfer_payload
