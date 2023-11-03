from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CompleteSoSwapWrappedWithoutSwapArgs(typing.TypedDict):
    vaa_hash: list[int]
    skip_verify_soswap_message: bool


layout = borsh.CStruct(
    "vaa_hash" / borsh.U8[32], "skip_verify_soswap_message" / borsh.Bool
)


class CompleteSoSwapWrappedWithoutSwapAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey
    fee_config: Pubkey
    beneficiary_token_account: Pubkey
    foreign_contract: Pubkey
    token_bridge_wrapped_mint: Pubkey
    recipient_token_account: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_wrapped_meta: Pubkey
    token_bridge_config: Pubkey
    vaa: Pubkey
    token_bridge_claim: Pubkey
    token_bridge_foreign_endpoint: Pubkey
    token_bridge_mint_authority: Pubkey


def complete_so_swap_wrapped_without_swap(
    args: CompleteSoSwapWrappedWithoutSwapArgs,
    accounts: CompleteSoSwapWrappedWithoutSwapAccounts,
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
            pubkey=accounts["token_bridge_wrapped_mint"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["recipient_token_account"],
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
            pubkey=accounts["token_bridge_wrapped_meta"],
            is_signer=False,
            is_writable=False,
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
            pubkey=accounts["token_bridge_mint_authority"],
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
    identifier = b"f\xc9R\xefqcDd"
    encoded_args = layout.build(
        {
            "vaa_hash": args["vaa_hash"],
            "skip_verify_soswap_message": args["skip_verify_soswap_message"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
