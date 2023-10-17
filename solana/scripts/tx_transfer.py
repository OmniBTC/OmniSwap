import asyncio

from solana.transaction import Transaction
from solders.pubkey import Pubkey

from omniswap.instructions import (
    so_swap_native_without_swap,
    so_swap_wrapped_without_swap,
)
from omniswap.program_id import PROGRAM_ID
from helper import (
    getSendWrappedTransferAccounts,
    deriveTokenTransferMessageKey,
    getSendNativeTransferAccounts,
)
from config import get_client, get_payer, wormhole_devnet, token_bridge_devnet

from cross import WormholeData, SoData, generate_random_bytes32


async def omniswap_send_wrapped_tokens_with_payload():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    # bsc-testnet
    recipient_chain = 4
    # wrapper token
    token_on_solana = bytes(Pubkey.from_string("todo"))
    token_on_bsc = bytes.fromhex("todo")
    # wrapper token account
    wrapper_token_account = Pubkey.from_string("todo")
    # send amount(decimals=8), 1 coin
    amount = 100000000
    # recipient
    recipient_address = bytes.fromhex("todo")

    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )

    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string("vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS")

    send_wrapped_accounts = getSendWrappedTransferAccounts(
        token_bridge_devnet,
        wormhole_devnet,
        PROGRAM_ID,
        recipient_chain,
        token_on_bsc,
    )

    current_seq_bytes = await client.get_account_info(
        send_wrapped_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")

    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(PROGRAM_ID, next_seq)

    ix = so_swap_wrapped_without_swap(
        args={
            "amount": amount,
            "wormhole_data": WormholeData(
                dstWormholeChainId=4,
                dstMaxGasPriceInWeiForRelayer=100000,
                wormholeFee=0,
                dstSoDiamond=dst_so_diamond_padding,
            ).encode_normalized(),
            "so_data": SoData(
                transactionId=bytes.fromhex(
                    generate_random_bytes32().replace("0x", "")
                ),
                receiver=recipient_address,
                sourceChainId=1,
                sendingAssetId=token_on_solana,
                destinationChainId=4,
                receivingAssetId=token_on_bsc,
                amount=amount,
            ).encode_normalized(),
            "swap_data_dst": bytes(),
        },
        accounts={
            "payer": payer.pubkey(),
            "config": send_wrapped_accounts["send_config"],
            "fee_config": send_wrapped_accounts["fee_config"],
            "price_manager": send_wrapped_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_wrapped_accounts["foreign_contract"],
            "token_bridge_wrapped_mint": send_wrapped_accounts[
                "token_bridge_wrapped_mint"
            ],
            "from_token_account": wrapper_token_account,
            "tmp_token_account": send_wrapped_accounts["tmp_token_account"],
            "wormhole_program": send_wrapped_accounts["wormhole_program"],
            "token_bridge_program": send_wrapped_accounts["token_bridge_program"],
            "token_bridge_wrapped_meta": send_wrapped_accounts[
                "token_bridge_wrapped_meta"
            ],
            "token_bridge_config": send_wrapped_accounts["token_bridge_config"],
            "token_bridge_authority_signer": send_wrapped_accounts[
                "token_bridge_authority_signer"
            ],
            "wormhole_bridge": send_wrapped_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_wrapped_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_wrapped_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_wrapped_accounts["wormhole_fee_collector"],
        },
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    await client.close()


async def omniswap_send_native_tokens_with_payload():
    client = get_client()
    await client.is_connected()

    payer = get_payer()

    # bsc-testnet
    recipient_chain = 4
    usdc_mint = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
    usdc_token_on_solana = bytes(usdc_mint)
    # usdc account
    usdc_account = Pubkey.from_string("68DjnBuZ6UtM6dGoTGhu2rqV5ZSowsPGgv2AWD1xuGB4")
    # send 1 usdc
    amount = 1000000
    # recipient
    recipient_address = bytes.fromhex("cAF084133CBdBE27490d3afB0Da220a40C32E307")
    usdc_token_on_bsc = bytes.fromhex("51a3cc54eA30Da607974C5D07B8502599801AC08")
    dst_so_diamond_padding = bytes.fromhex(
        "00000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc"
    )
    # collect relayer gas fee
    beneficiary_account = Pubkey.from_string("vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS")

    send_native_accounts = getSendNativeTransferAccounts(
        token_bridge_devnet,
        wormhole_devnet,
        PROGRAM_ID,
        recipient_chain,
        usdc_mint,
    )

    current_seq_bytes = await client.get_account_info(
        send_native_accounts["token_bridge_sequence"]
    )
    current_seq = int.from_bytes(current_seq_bytes.value.data, byteorder="little")
    print(f"current_seq={current_seq}")

    next_seq = current_seq + 1
    wormhole_message = deriveTokenTransferMessageKey(PROGRAM_ID, next_seq)

    ix = so_swap_native_without_swap(
        args={
            "amount": amount,
            "wormhole_data": WormholeData(
                dstWormholeChainId=4,
                dstMaxGasPriceInWeiForRelayer=100000,
                wormholeFee=0,
                dstSoDiamond=dst_so_diamond_padding,
            ).encode_normalized(),
            "so_data": SoData(
                transactionId=bytes.fromhex(
                    generate_random_bytes32().replace("0x", "")
                ),
                receiver=recipient_address,
                sourceChainId=1,
                sendingAssetId=usdc_token_on_solana,
                destinationChainId=4,
                receivingAssetId=usdc_token_on_bsc,
                amount=amount,
            ).encode_normalized(),
            "swap_data_dst": bytes(),
        },
        accounts={
            "payer": payer.pubkey(),
            "config": send_native_accounts["send_config"],
            "fee_config": send_native_accounts["fee_config"],
            "price_manager": send_native_accounts["price_manager"],
            "beneficiary_account": beneficiary_account,
            "foreign_contract": send_native_accounts["foreign_contract"],
            "mint": usdc_mint,
            "from_token_account": usdc_account,
            "tmp_token_account": send_native_accounts["tmp_token_account"],
            "wormhole_program": send_native_accounts["wormhole_program"],
            "token_bridge_program": send_native_accounts["token_bridge_program"],
            "token_bridge_config": send_native_accounts["token_bridge_config"],
            "token_bridge_custody": send_native_accounts["token_bridge_custody"],
            "token_bridge_authority_signer": send_native_accounts[
                "token_bridge_authority_signer"
            ],
            "token_bridge_custody_signer": send_native_accounts[
                "token_bridge_custody_signer"
            ],
            "wormhole_bridge": send_native_accounts["wormhole_bridge"],
            "wormhole_message": wormhole_message,
            "token_bridge_emitter": send_native_accounts["token_bridge_emitter"],
            "token_bridge_sequence": send_native_accounts["token_bridge_sequence"],
            "wormhole_fee_collector": send_native_accounts["wormhole_fee_collector"],
        },
    )

    tx = Transaction(fee_payer=payer.pubkey()).add(ix)

    tx_sig = await client.send_transaction(tx, payer)
    print(tx_sig)

    await client.close()


asyncio.run(omniswap_send_native_tokens_with_payload())
