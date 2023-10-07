from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateRelayerFeeArgs(typing.TypedDict):
    relayer_fee: int
    relayer_fee_precision: int


layout = borsh.CStruct("relayer_fee" / borsh.U32, "relayer_fee_precision" / borsh.U32)


class UpdateRelayerFeeAccounts(typing.TypedDict):
    owner: Pubkey
    config: Pubkey


def update_relayer_fee(
    args: UpdateRelayerFeeArgs,
    accounts: UpdateRelayerFeeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\xf7\x04"#\x1e\x95N\x19'
    encoded_args = layout.build(
        {
            "relayer_fee": args["relayer_fee"],
            "relayer_fee_precision": args["relayer_fee_precision"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
