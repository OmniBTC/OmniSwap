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


class PriceManagerJSON(typing.TypedDict):
    owner: str
    current_price_ratio: int
    last_update_timestamp: int


@dataclass
class PriceManager:
    discriminator: typing.ClassVar = b'k\xe3\xe7M5\xf6\x05"'
    layout: typing.ClassVar = borsh.CStruct(
        "owner" / BorshPubkey,
        "current_price_ratio" / borsh.U64,
        "last_update_timestamp" / borsh.U64,
    )
    owner: Pubkey
    current_price_ratio: int
    last_update_timestamp: int

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["PriceManager"]:
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
    ) -> typing.List[typing.Optional["PriceManager"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["PriceManager"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "PriceManager":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = PriceManager.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            owner=dec.owner,
            current_price_ratio=dec.current_price_ratio,
            last_update_timestamp=dec.last_update_timestamp,
        )

    def to_json(self) -> PriceManagerJSON:
        return {
            "owner": str(self.owner),
            "current_price_ratio": self.current_price_ratio,
            "last_update_timestamp": self.last_update_timestamp,
        }

    @classmethod
    def from_json(cls, obj: PriceManagerJSON) -> "PriceManager":
        return cls(
            owner=Pubkey.from_string(obj["owner"]),
            current_price_ratio=obj["current_price_ratio"],
            last_update_timestamp=obj["last_update_timestamp"],
        )
