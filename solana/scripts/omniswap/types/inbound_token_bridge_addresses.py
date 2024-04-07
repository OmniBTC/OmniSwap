from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class InboundTokenBridgeAddressesJSON(typing.TypedDict):
    config: str
    custody_signer: str
    mint_authority: str


@dataclass
class InboundTokenBridgeAddresses:
    layout: typing.ClassVar = borsh.CStruct(
        "config" / BorshPubkey,
        "custody_signer" / BorshPubkey,
        "mint_authority" / BorshPubkey,
    )
    config: Pubkey
    custody_signer: Pubkey
    mint_authority: Pubkey

    @classmethod
    def from_decoded(cls, obj: Container) -> "InboundTokenBridgeAddresses":
        return cls(
            config=obj.config,
            custody_signer=obj.custody_signer,
            mint_authority=obj.mint_authority,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "config": self.config,
            "custody_signer": self.custody_signer,
            "mint_authority": self.mint_authority,
        }

    def to_json(self) -> InboundTokenBridgeAddressesJSON:
        return {
            "config": str(self.config),
            "custody_signer": str(self.custody_signer),
            "mint_authority": str(self.mint_authority),
        }

    @classmethod
    def from_json(
        cls, obj: InboundTokenBridgeAddressesJSON
    ) -> "InboundTokenBridgeAddresses":
        return cls(
            config=Pubkey.from_string(obj["config"]),
            custody_signer=Pubkey.from_string(obj["custody_signer"]),
            mint_authority=Pubkey.from_string(obj["mint_authority"]),
        )
