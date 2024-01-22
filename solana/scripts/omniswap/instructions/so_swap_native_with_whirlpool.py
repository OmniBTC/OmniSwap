from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT, CLOCK
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class SoSwapNativeWithWhirlpoolAccounts(typing.TypedDict):
    payer: Pubkey
    request: Pubkey
    config: Pubkey
    fee_config: Pubkey
    price_manager: Pubkey
    beneficiary_account: Pubkey
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
    mint: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    token_bridge_custody: Pubkey
    token_bridge_custody_signer: Pubkey
    token_bridge_authority_signer: Pubkey
    wormhole_bridge: Pubkey
    wormhole_message: Pubkey
    token_bridge_emitter: Pubkey
    token_bridge_sequence: Pubkey
    wormhole_fee_collector: Pubkey


def so_swap_native_with_whirlpool(
    accounts: SoSwapNativeWithWhirlpoolAccounts,
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
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True),
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
            pubkey=accounts["token_bridge_custody"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_bridge_custody_signer"],
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
    identifier = b"\xd2:\x04X\xa0\xd8\x13\xa6"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
