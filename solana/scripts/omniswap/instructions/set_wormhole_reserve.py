from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetWormholeReserveArgs(typing.TypedDict):
    actual_reserve: int
    estimate_reserve: int


layout = borsh.CStruct("actual_reserve" / borsh.U64, "estimate_reserve" / borsh.U64)


class SetWormholeReserveAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey


def set_wormhole_reserve(
    args: SetWormholeReserveArgs,
    accounts: SetWormholeReserveAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"A\xbc\x15\xdc\x15]\xcf\xf5"
    encoded_args = layout.build(
        {
            "actual_reserve": args["actual_reserve"],
            "estimate_reserve": args["estimate_reserve"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
