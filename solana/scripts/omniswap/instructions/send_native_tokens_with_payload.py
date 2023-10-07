from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT, CLOCK
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SendNativeTokensWithPayloadArgs(typing.TypedDict):
    batch_id: int
    amount: int
    wormhole_data: bytes
    so_data: bytes
    swap_data: bytes


layout = borsh.CStruct(
    "batch_id" / borsh.U32,
    "amount" / borsh.U64,
    "wormhole_data" / borsh.Bytes,
    "so_data" / borsh.Bytes,
    "swap_data" / borsh.Bytes,
)


class SendNativeTokensWithPayloadAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey
    foreign_contract: Pubkey
    mint: Pubkey
    from_token_account: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    token_bridge_custody: Pubkey
    token_bridge_authority_signer: Pubkey
    token_bridge_custody_signer: Pubkey
    wormhole_bridge: Pubkey
    wormhole_message: Pubkey
    token_bridge_emitter: Pubkey
    token_bridge_sequence: Pubkey
    wormhole_fee_collector: Pubkey


def send_native_tokens_with_payload(
    args: SendNativeTokensWithPayloadArgs,
    accounts: SendNativeTokensWithPayloadAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["foreign_contract"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=True),
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
            pubkey=accounts["token_bridge_custody"], is_signer=False, is_writable=True
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
    identifier = b"\xc7e\xfe\xe6\x0f \xdf\xc9"
    encoded_args = layout.build(
        {
            "batch_id": args["batch_id"],
            "amount": args["amount"],
            "wormhole_data": args["wormhole_data"],
            "so_data": args["so_data"],
            "swap_data": args["swap_data"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
