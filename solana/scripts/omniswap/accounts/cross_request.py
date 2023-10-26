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


class CrossRequestJSON(typing.TypedDict):
    owner: str
    payer: str
    nonce: int
    so_data: list[int]
    swap_data_src: list[int]
    wormhole_data: list[int]
    swap_data_dst: list[int]


@dataclass
class CrossRequest:
    discriminator: typing.ClassVar = b"\xa7VdD\xb78<\x1d"
    layout: typing.ClassVar = borsh.CStruct(
        "owner" / BorshPubkey,
        "payer" / BorshPubkey,
        "nonce" / borsh.U64,
        "so_data" / borsh.Bytes,
        "swap_data_src" / borsh.Bytes,
        "wormhole_data" / borsh.Bytes,
        "swap_data_dst" / borsh.Bytes,
    )
    owner: Pubkey
    payer: Pubkey
    nonce: int
    so_data: bytes
    swap_data_src: bytes
    wormhole_data: bytes
    swap_data_dst: bytes

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["CrossRequest"]:
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
    ) -> typing.List[typing.Optional["CrossRequest"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["CrossRequest"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "CrossRequest":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = CrossRequest.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            owner=dec.owner,
            payer=dec.payer,
            nonce=dec.nonce,
            so_data=dec.so_data,
            swap_data_src=dec.swap_data_src,
            wormhole_data=dec.wormhole_data,
            swap_data_dst=dec.swap_data_dst,
        )

    def to_json(self) -> CrossRequestJSON:
        return {
            "owner": str(self.owner),
            "payer": str(self.payer),
            "nonce": self.nonce,
            "so_data": list(self.so_data),
            "swap_data_src": list(self.swap_data_src),
            "wormhole_data": list(self.wormhole_data),
            "swap_data_dst": list(self.swap_data_dst),
        }

    @classmethod
    def from_json(cls, obj: CrossRequestJSON) -> "CrossRequest":
        return cls(
            owner=Pubkey.from_string(obj["owner"]),
            payer=Pubkey.from_string(obj["payer"]),
            nonce=obj["nonce"],
            so_data=bytes(obj["so_data"]),
            swap_data_src=bytes(obj["swap_data_src"]),
            wormhole_data=bytes(obj["wormhole_data"]),
            swap_data_dst=bytes(obj["swap_data_dst"]),
        )
