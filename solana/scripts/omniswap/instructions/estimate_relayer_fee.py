from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class EstimateRelayerFeeArgs(typing.TypedDict):
    so_data: bytes
    wormhole_data: bytes
    swap_data_dst: bytes


layout = borsh.CStruct(
    "so_data" / borsh.Bytes,
    "wormhole_data" / borsh.Bytes,
    "swap_data_dst" / borsh.Bytes,
)


class EstimateRelayerFeeAccounts(typing.TypedDict):
    fee_config: Pubkey
    foreign_contract: Pubkey
    price_manager: Pubkey
    wormhole_bridge: Pubkey


def estimate_relayer_fee(
    args: EstimateRelayerFeeArgs,
    accounts: EstimateRelayerFeeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
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
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"!\xe9(\x129\xfa:\x85"
    encoded_args = layout.build(
        {
            "so_data": args["so_data"],
            "wormhole_data": args["wormhole_data"],
            "swap_data_dst": args["swap_data_dst"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
