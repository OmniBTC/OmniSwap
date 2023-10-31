from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class WrapSolArgs(typing.TypedDict):
    amount_to_be_wrapped: int


layout = borsh.CStruct("amount_to_be_wrapped" / borsh.U64)


class WrapSolAccounts(typing.TypedDict):
    payer: Pubkey
    wrap_sol_account: Pubkey
    wsol_mint: Pubkey


def wrap_sol(
    args: WrapSolArgs,
    accounts: WrapSolAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["wrap_sol_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["wsol_mint"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"/>\x9b\xac\x83\xcd%\xc9"
    encoded_args = layout.build(
        {
            "amount_to_be_wrapped": args["amount_to_be_wrapped"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
