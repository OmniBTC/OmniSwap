from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeArgs(typing.TypedDict):
    beneficiary: Pubkey
    redeemer_proxy: Pubkey
    actual_reserve: int
    estimate_reserve: int
    so_fee_by_ray: int


layout = borsh.CStruct(
    "beneficiary" / BorshPubkey,
    "redeemer_proxy" / BorshPubkey,
    "actual_reserve" / borsh.U64,
    "estimate_reserve" / borsh.U64,
    "so_fee_by_ray" / borsh.U64,
)


class InitializeAccounts(typing.TypedDict):
    owner: Pubkey
    fee_config: Pubkey
    sender_config: Pubkey
    redeemer_config: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    token_bridge_authority_signer: Pubkey
    token_bridge_custody_signer: Pubkey
    token_bridge_mint_authority: Pubkey
    wormhole_bridge: Pubkey
    token_bridge_emitter: Pubkey
    wormhole_fee_collector: Pubkey
    token_bridge_sequence: Pubkey


def initialize(
    args: InitializeArgs,
    accounts: InitializeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["fee_config"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["sender_config"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["redeemer_config"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["wormhole_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_config"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_authority_signer"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_custody_signer"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_mint_authority"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["wormhole_bridge"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_emitter"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["wormhole_fee_collector"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_sequence"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xaf\xafm\x1f\r\x98\x9b\xed"
    encoded_args = layout.build(
        {
            "beneficiary": args["beneficiary"],
            "redeemer_proxy": args["redeemer_proxy"],
            "actual_reserve": args["actual_reserve"],
            "estimate_reserve": args["estimate_reserve"],
            "so_fee_by_ray": args["so_fee_by_ray"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
