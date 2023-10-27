from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SoSwapPostCrossRequestArgs(typing.TypedDict):
    so_data: bytes
    swap_data_src: bytes
    wormhole_data: bytes
    swap_data_dst: bytes


layout = borsh.CStruct(
    "so_data" / borsh.Bytes,
    "swap_data_src" / borsh.Bytes,
    "wormhole_data" / borsh.Bytes,
    "swap_data_dst" / borsh.Bytes,
)


class SoSwapPostCrossRequestAccounts(typing.TypedDict):
    payer: Pubkey
    config: Pubkey
    request: Pubkey
    fee_config: Pubkey
    foreign_contract: Pubkey
    price_manager: Pubkey
    wormhole_bridge: Pubkey


def so_swap_post_cross_request(
    args: SoSwapPostCrossRequestArgs,
    accounts: SoSwapPostCrossRequestAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["config"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["request"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["fee_config"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["foreign_contract"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["price_manager"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["wormhole_bridge"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"<\xc1\x84\x89\xc9\xe6\x17~"
    encoded_args = layout.build(
        {
            "so_data": args["so_data"],
            "swap_data_src": args["swap_data_src"],
            "wormhole_data": args["wormhole_data"],
            "swap_data_dst": args["swap_data_dst"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
