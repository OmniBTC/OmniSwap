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


class SoFeeConfigJSON(typing.TypedDict):
    owner: str
    beneficiary: str
    so_fee: int
    actual_reserve: int
    estimate_reserve: int


@dataclass
class SoFeeConfig:
    discriminator: typing.ClassVar = b")h!l\xf5ZM\x82"
    layout: typing.ClassVar = borsh.CStruct(
        "owner" / BorshPubkey,
        "beneficiary" / BorshPubkey,
        "so_fee" / borsh.U64,
        "actual_reserve" / borsh.U64,
        "estimate_reserve" / borsh.U64,
    )
    owner: Pubkey
    beneficiary: Pubkey
    so_fee: int
    actual_reserve: int
    estimate_reserve: int

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["SoFeeConfig"]:
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
    ) -> typing.List[typing.Optional["SoFeeConfig"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["SoFeeConfig"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "SoFeeConfig":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = SoFeeConfig.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            owner=dec.owner,
            beneficiary=dec.beneficiary,
            so_fee=dec.so_fee,
            actual_reserve=dec.actual_reserve,
            estimate_reserve=dec.estimate_reserve,
        )

    def to_json(self) -> SoFeeConfigJSON:
        return {
            "owner": str(self.owner),
            "beneficiary": str(self.beneficiary),
            "so_fee": self.so_fee,
            "actual_reserve": self.actual_reserve,
            "estimate_reserve": self.estimate_reserve,
        }

    @classmethod
    def from_json(cls, obj: SoFeeConfigJSON) -> "SoFeeConfig":
        return cls(
            owner=Pubkey.from_string(obj["owner"]),
            beneficiary=Pubkey.from_string(obj["beneficiary"]),
            so_fee=obj["so_fee"],
            actual_reserve=obj["actual_reserve"],
            estimate_reserve=obj["estimate_reserve"],
        )
