import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID
from .. import types


class SenderConfigJSON(typing.TypedDict):
    owner: str
    bump: int
    token_bridge: types.outbound_token_bridge_addresses.OutboundTokenBridgeAddressesJSON
    nonce: int


@dataclass
class SenderConfig:
    discriminator: typing.ClassVar = b"\x00\xf1\xdcM\xa7\x80O\x98"
    layout: typing.ClassVar = borsh.CStruct(
        "owner" / BorshPubkey,
        "bump" / borsh.U8,
        "token_bridge"
        / types.outbound_token_bridge_addresses.OutboundTokenBridgeAddresses.layout,
        "nonce" / borsh.U64,
    )
    owner: Pubkey
    bump: int
    token_bridge: types.outbound_token_bridge_addresses.OutboundTokenBridgeAddresses
    nonce: int

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["SenderConfig"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["SenderConfig"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["SenderConfig"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "SenderConfig":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = SenderConfig.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            owner=dec.owner,
            bump=dec.bump,
            token_bridge=types.outbound_token_bridge_addresses.OutboundTokenBridgeAddresses.from_decoded(
                dec.token_bridge
            ),
            nonce=dec.nonce,
        )

    def to_json(self) -> SenderConfigJSON:
        return {
            "owner": str(self.owner),
            "bump": self.bump,
            "token_bridge": self.token_bridge.to_json(),
            "nonce": self.nonce,
        }

    @classmethod
    def from_json(cls, obj: SenderConfigJSON) -> "SenderConfig":
        return cls(
            owner=Pubkey.from_string(obj["owner"]),
            bump=obj["bump"],
            token_bridge=types.outbound_token_bridge_addresses.OutboundTokenBridgeAddresses.from_json(
                obj["token_bridge"]
            ),
            nonce=obj["nonce"],
        )
