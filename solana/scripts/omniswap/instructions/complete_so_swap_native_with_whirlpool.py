from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CompleteSoSwapNativeWithWhirlpoolArgs(typing.TypedDict):
    vaa_hash: list[int]


layout = borsh.CStruct("vaa_hash" / borsh.U8[32])


class CompleteSoSwapNativeWithWhirlpoolAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey
    fee_config: Pubkey
    beneficiary_token_account: Pubkey
    foreign_contract: Pubkey
    whirlpool_program: Pubkey
    whirlpool_account: Pubkey
    whirlpool_token_owner_account_a: Pubkey
    whirlpool_token_vault_a: Pubkey
    whirlpool_token_owner_account_b: Pubkey
    whirlpool_token_vault_b: Pubkey
    whirlpool_tick_array0: Pubkey
    whirlpool_tick_array1: Pubkey
    whirlpool_tick_array2: Pubkey
    whirlpool_oracle: Pubkey
    unwrap_sol_account: typing.Optional[Pubkey]
    wsol_mint: typing.Optional[Pubkey]
    recipient: typing.Optional[Pubkey]
    mint: Pubkey
    recipient_token_account: Pubkey
    recipient_bridge_token_account: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    vaa: Pubkey
    token_bridge_claim: Pubkey
    token_bridge_foreign_endpoint: Pubkey
    token_bridge_custody: Pubkey
    token_bridge_custody_signer: Pubkey


def complete_so_swap_native_with_whirlpool(
    args: CompleteSoSwapNativeWithWhirlpoolArgs,
    accounts: CompleteSoSwapNativeWithWhirlpoolAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["fee_config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["beneficiary_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["foreign_contract"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_token_owner_account_a"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_token_vault_a"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_token_owner_account_b"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_token_vault_b"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_tick_array0"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_tick_array1"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_tick_array2"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["whirlpool_oracle"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["unwrap_sol_account"], is_signer=False, is_writable=True
        )
        if accounts["unwrap_sol_account"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["wsol_mint"], is_signer=False, is_writable=False)
        if accounts["wsol_mint"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["recipient"], is_signer=False, is_writable=True)
        if accounts["recipient"]
        else AccountMeta(pubkey=program_id, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["recipient_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["recipient_bridge_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["tmp_token_account"], is_signer=False, is_writable=True
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
        AccountMeta(pubkey=accounts["vaa"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["token_bridge_claim"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_foreign_endpoint"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_custody"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_custody_signer"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xdf\xa3\xb1\x16\x1eb\xa0b"
    encoded_args = layout.build(
        {
            "vaa_hash": args["vaa_hash"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
