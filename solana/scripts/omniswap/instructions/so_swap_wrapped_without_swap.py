from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT, CLOCK
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class SoSwapWrappedWithoutSwapAccounts(typing.TypedDict):
    payer: Pubkey
    request: Pubkey
    config: Pubkey
    fee_config: Pubkey
    price_manager: Pubkey
    beneficiary_account: Pubkey
    foreign_contract: Pubkey
    token_bridge_wrapped_mint: Pubkey
    from_token_account: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    token_bridge_wrapped_meta: Pubkey
    token_bridge_authority_signer: Pubkey
    wormhole_bridge: Pubkey
    wormhole_message: Pubkey
    token_bridge_emitter: Pubkey
    token_bridge_sequence: Pubkey
    wormhole_fee_collector: Pubkey


def so_swap_wrapped_without_swap(
    accounts: SoSwapWrappedWithoutSwapAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["request"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["fee_config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["price_manager"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["beneficiary_account"], is_signer=False, is_writable=True
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
            pubkey=accounts["from_token_account"], is_signer=False, is_writable=True
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
        AccountMeta(
            pubkey=accounts["token_bridge_wrapped_meta"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_authority_signer"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["wormhole_bridge"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["wormhole_message"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_emitter"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_sequence"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["wormhole_fee_collector"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x99\xff\x90\t6N\x97S"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
