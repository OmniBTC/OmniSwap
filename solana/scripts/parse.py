import json
from typing import Union
from eth_utils import keccak
from base58 import b58encode
from cross import SoData, SwapData
import serde as omniswap_serde


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
                    "signature": bytes(signed_vaa[start + 1 : start + 66]),
                }
            )

        body = signed_vaa[sig_start + sig_length * num_signers :]

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

    def bridge_token(self):
        if self.parsed_transfer_payload.without_swap():
            return self.parsed_transfer_payload.so_data.receiving_asset()
        else:
            return self.parsed_transfer_payload.swap_data_list[0].sending_asset()

    def dst_token(self):
        return self.parsed_transfer_payload.so_data.receiving_asset()

    def first_swap_pool(self):
        if len(self.parsed_transfer_payload.swap_data_list) > 0:
            return self.parsed_transfer_payload.swap_data_list[0].pool_address()
        else:
            return None


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

    def without_swap(self):
        return len(self.swap_data_list) == 0

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

        next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
        index = index + 1
        dst_max_gas_price = omniswap_serde.deserialize_u256_with_hex_str(
            payload[index : index + next_len]
        )
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
        index = index + 1
        dst_max_gas = omniswap_serde.deserialize_u256_with_hex_str(
            payload[index : index + next_len]
        )
        index = index + next_len

        # SoData
        next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
        index = index + 1
        so_transaction_id = payload[index : index + next_len]
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
        index = index + 1
        so_receiver = payload[index : index + next_len]
        index = index + next_len

        next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
        index = index + 1
        so_receiving_asset_id = payload[index : index + next_len]
        index = index + next_len

        so_data = SoData.padding(so_transaction_id, so_receiver, so_receiving_asset_id)

        # Skip len
        if index < data_len:
            next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
            index = index + 1
            index = index + next_len

        # SwapData
        swap_data_list = []
        while index < data_len:
            next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
            index = index + 1
            swap_call_to = payload[index : index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
            index = index + 1
            swap_sending_asset_id = payload[index : index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u8(payload[index : index + 1])
            index = index + 1
            swap_receiving_asset_id = payload[index : index + next_len]
            index = index + next_len

            next_len = omniswap_serde.deserialize_u16(payload[index : index + 2])
            index = index + 2
            swap_call_data = payload[index : index + next_len]
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


if __name__ == "__main__":
    parsed_vaa, parsed_transfer, parsed_transfer_payload = parseTransferWithPayloadVaa(
        "0x01000000000100a27a9ee47f5cc670f2f959e3a993fe393940dcfc55d7ecf36f75734e27f31d6c6045d835cf9d81b418383bc2a61ce3e1d8aa2ae0b9fccabe88917fa2b66d621901652212a80000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09000000000000136b0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea700017ef1dcda48c0b739dfd4da982c187838573cc044d8ded9fe382b84ceb6fa6b53000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20d5006ba1ae36806c379a926d648b5e0783e966eddde87b8920717a7e819436982038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
    )

    print(f"parsed_vaa: {parsed_vaa}")
    print(f"parsed_transfer: {parsed_transfer}")
    print(f"parsed_transfer_payload: {parsed_transfer_payload}")
