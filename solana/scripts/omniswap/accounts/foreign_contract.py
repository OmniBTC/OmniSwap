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


class ForeignContractJSON(typing.TypedDict):
    chain: int
    address: list[int]
    token_bridge_foreign_endpoint: str


@dataclass
class ForeignContract:
    discriminator: typing.ClassVar = b"\xb0\xeaP=\xde\xcd\xa2K"
    layout: typing.ClassVar = borsh.CStruct(
        "chain" / borsh.U16,
        "address" / borsh.U8[32],
        "token_bridge_foreign_endpoint" / BorshPubkey,
    )
    chain: int
    address: list[int]
    token_bridge_foreign_endpoint: Pubkey

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["ForeignContract"]:
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
    ) -> typing.List[typing.Optional["ForeignContract"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["ForeignContract"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "ForeignContract":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = ForeignContract.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            chain=dec.chain,
            address=dec.address,
            token_bridge_foreign_endpoint=dec.token_bridge_foreign_endpoint,
        )

    def to_json(self) -> ForeignContractJSON:
        return {
            "chain": self.chain,
            "address": self.address,
            "token_bridge_foreign_endpoint": str(self.token_bridge_foreign_endpoint),
        }

    @classmethod
    def from_json(cls, obj: ForeignContractJSON) -> "ForeignContract":
        return cls(
            chain=obj["chain"],
            address=obj["address"],
            token_bridge_foreign_endpoint=Pubkey.from_string(
                obj["token_bridge_foreign_endpoint"]
            ),
        )
