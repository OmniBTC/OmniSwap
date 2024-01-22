from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import CLOCK
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetPriceRatioArgs(typing.TypedDict):
    chain: int
    new_price_ratio: int


layout = borsh.CStruct("chain" / borsh.U16, "new_price_ratio" / borsh.U64)


class SetPriceRatioAccounts(typing.TypedDict):
    owner: Pubkey
    price_manager: Pubkey


def set_price_ratio(
    args: SetPriceRatioArgs,
    accounts: SetPriceRatioAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["price_manager"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\x19\n\xe4%\xf5"\xe8\x03'
    encoded_args = layout.build(
        {
            "chain": args["chain"],
            "new_price_ratio": args["new_price_ratio"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
