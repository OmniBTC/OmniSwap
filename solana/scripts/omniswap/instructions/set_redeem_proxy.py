from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SetRedeemProxyArgs(typing.TypedDict):
    new_proxy: Pubkey


layout = borsh.CStruct("new_proxy" / BorshPubkey)


class SetRedeemProxyAccounts(typing.TypedDict):
    owner: Pubkey
    config: Pubkey


def set_redeem_proxy(
    args: SetRedeemProxyArgs,
    accounts: SetRedeemProxyAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x94\xdc\xcb\x06>\xb2k\x9c"
    encoded_args = layout.build(
        {
            "new_proxy": args["new_proxy"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
