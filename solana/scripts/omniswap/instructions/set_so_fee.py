from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetSoFeeArgs(typing.TypedDict):
    so_fee_by_ray: int


layout = borsh.CStruct("so_fee_by_ray" / borsh.U64)


class SetSoFeeAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey


def set_so_fee(
    args: SetSoFeeArgs,
    accounts: SetSoFeeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa4\x9e\xd5\xe2X\x05\xc8$"
    encoded_args = layout.build(
        {
            "so_fee_by_ray": args["so_fee_by_ray"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
