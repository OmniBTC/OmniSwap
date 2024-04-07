from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import CLOCK
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RegisterForeignContractArgs(typing.TypedDict):
    chain: int
    address: list[int]
    normalized_dst_base_gas_le: list[int]
    normalized_dst_gas_per_bytes_le: list[int]
    price_manager_owner: Pubkey
    init_price_ratio: int


layout = borsh.CStruct(
    "chain" / borsh.U16,
    "address" / borsh.U8[32],
    "normalized_dst_base_gas_le" / borsh.U8[32],
    "normalized_dst_gas_per_bytes_le" / borsh.U8[32],
    "price_manager_owner" / BorshPubkey,
    "init_price_ratio" / borsh.U64,
)


class RegisterForeignContractAccounts(typing.TypedDict):
    owner: Pubkey
    config: Pubkey
    foreign_contract: Pubkey
    price_manager: Pubkey
    token_bridge_foreign_endpoint: Pubkey
    token_bridge_program: Pubkey


def register_foreign_contract(
    args: RegisterForeignContractArgs,
    accounts: RegisterForeignContractAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["foreign_contract"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["price_manager"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_foreign_endpoint"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x84t\xa6\xf8Cm\x08\xe3"
    encoded_args = layout.build(
        {
            "chain": args["chain"],
            "address": args["address"],
            "normalized_dst_base_gas_le": args["normalized_dst_base_gas_le"],
            "normalized_dst_gas_per_bytes_le": args["normalized_dst_gas_per_bytes_le"],
            "price_manager_owner": args["price_manager_owner"],
            "init_price_ratio": args["init_price_ratio"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
