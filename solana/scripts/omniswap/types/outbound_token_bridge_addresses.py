from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class OutboundTokenBridgeAddressesJSON(typing.TypedDict):
    config: str
    authority_signer: str
    custody_signer: str
    emitter: str
    sequence: str
    wormhole_bridge: str
    wormhole_fee_collector: str


@dataclass
class OutboundTokenBridgeAddresses:
    layout: typing.ClassVar = borsh.CStruct(
        "config" / BorshPubkey,
        "authority_signer" / BorshPubkey,
        "custody_signer" / BorshPubkey,
        "emitter" / BorshPubkey,
        "sequence" / BorshPubkey,
        "wormhole_bridge" / BorshPubkey,
        "wormhole_fee_collector" / BorshPubkey,
    )
    config: Pubkey
    authority_signer: Pubkey
    custody_signer: Pubkey
    emitter: Pubkey
    sequence: Pubkey
    wormhole_bridge: Pubkey
    wormhole_fee_collector: Pubkey

    @classmethod
    def from_decoded(cls, obj: Container) -> "OutboundTokenBridgeAddresses":
        return cls(
            config=obj.config,
            authority_signer=obj.authority_signer,
            custody_signer=obj.custody_signer,
            emitter=obj.emitter,
            sequence=obj.sequence,
            wormhole_bridge=obj.wormhole_bridge,
            wormhole_fee_collector=obj.wormhole_fee_collector,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "config": self.config,
            "authority_signer": self.authority_signer,
            "custody_signer": self.custody_signer,
            "emitter": self.emitter,
            "sequence": self.sequence,
            "wormhole_bridge": self.wormhole_bridge,
            "wormhole_fee_collector": self.wormhole_fee_collector,
        }

    def to_json(self) -> OutboundTokenBridgeAddressesJSON:
        return {
            "config": str(self.config),
            "authority_signer": str(self.authority_signer),
            "custody_signer": str(self.custody_signer),
            "emitter": str(self.emitter),
            "sequence": str(self.sequence),
            "wormhole_bridge": str(self.wormhole_bridge),
            "wormhole_fee_collector": str(self.wormhole_fee_collector),
        }

    @classmethod
    def from_json(
        cls, obj: OutboundTokenBridgeAddressesJSON
    ) -> "OutboundTokenBridgeAddresses":
        return cls(
            config=Pubkey.from_string(obj["config"]),
            authority_signer=Pubkey.from_string(obj["authority_signer"]),
            custody_signer=Pubkey.from_string(obj["custody_signer"]),
            emitter=Pubkey.from_string(obj["emitter"]),
            sequence=Pubkey.from_string(obj["sequence"]),
            wormhole_bridge=Pubkey.from_string(obj["wormhole_bridge"]),
            wormhole_fee_collector=Pubkey.from_string(obj["wormhole_fee_collector"]),
        )
