from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RedeemNativeTransferWithPayloadArgs(typing.TypedDict):
    vaa_hash: list[int]


layout = borsh.CStruct("vaa_hash" / borsh.U8[32])


class RedeemNativeTransferWithPayloadAccounts(typing.TypedDict):
    payer: Pubkey
    payer_token_account: Pubkey
    config: Pubkey
    foreign_contract: Pubkey
    mint: Pubkey
    recipient_token_account: Pubkey
    recipient: Pubkey
    tmp_token_account: Pubkey
    wormhole_program: Pubkey
    token_bridge_program: Pubkey
    token_bridge_config: Pubkey
    vaa: Pubkey
    token_bridge_claim: Pubkey
    token_bridge_foreign_endpoint: Pubkey
    token_bridge_custody: Pubkey
    token_bridge_custody_signer: Pubkey


def redeem_native_transfer_with_payload(
    args: RedeemNativeTransferWithPayloadArgs,
    accounts: RedeemNativeTransferWithPayloadAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(
            pubkey=accounts["payer_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["foreign_contract"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["mint"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["recipient_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(pubkey=accounts["recipient"], is_signer=False, is_writable=True),
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
    identifier = b"a0\x06\x0c\xd1\x81\xe4*"
    encoded_args = layout.build(
        {
            "vaa_hash": args["vaa_hash"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
