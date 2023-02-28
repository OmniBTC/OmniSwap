import json
import polling
import requests
import base64

from brownie.convert import to_address, to_uint

SUCCESS_CODE = 200
TRANSFER_COMPLETED = 5
TRANSFER_REFUND_TO_BE_CONFIRMED = 8
TRANSFER_REFUNDED = 10

# main https://cbridge-prod2.celer.app/v2/getTransferStatus
# test "https://cbridge-v2-test.celer.network/v2/getTransferStatus"
CELER_URL = "https://cbridge-v2-test.celer.network/v2/getTransferStatus"
HEADERS = {"Content-Type": "application/json"}

TransferHistoryStatus = [
    "TRANSFER_UNKNOWN",
    "TRANSFER_SUBMITTING",
    "TRANSFER_FAILED",
    "TRANSFER_WAITING_FOR_SGN_CONFIRMATION",
    "TRANSFER_WAITING_FOR_FUND_RELEASE",
    "TRANSFER_COMPLETED",
    "TRANSFER_TO_BE_REFUNDED",
    "TRANSFER_REQUESTING_REFUND",
    "TRANSFER_REFUND_TO_BE_CONFIRMED",
    "TRANSFER_CONFIRMING_YOUR_REFUND",
    "TRANSFER_REFUNDED",
]

XferStatus = [
    "UNKNOWN",
    "OK_TO_RELAY",
    "SUCCESS",
    "BAD_LIQUIDITY",
    "BAD_SLIPPAGE",
    "BAD_TOKEN",
    "REFUND_REQUESTED",
    "REFUND_DONE",
    "BAD_XFER_DISABLED",
    "BAD_DEST_CHAIN",
]

# https://cbridge-docs.celer.network/developer/api-reference/contract-pool-based-transfer-refund
def convert_parameters(data):
    print("wd_onchain:", data["wd_onchain"])
    print("sorted_sigs:", data["sorted_sigs"])
    print("signers:", data["signers"])
    print("powers:", data["powers"])

    print("=================================")

    wd_onchain = base64.b64decode(data["wd_onchain"])
    sigs = list(map(lambda p: base64.b64decode(p), data["sorted_sigs"]))
    signers = list(
        map(lambda p: to_address(base64.b64decode(p).hex()), data["signers"])
    )
    powers = list(map(lambda p: to_uint(base64.b64decode(p)), data["powers"]))

    print("wd_onchain:", wd_onchain.hex())
    print("signs:", list(map(lambda p: p.hex(), sigs)))
    print("signers:", signers)
    print("powers:", powers)

    return wd_onchain, sigs, signers, powers


def is_correct_response(response):
    """Check celer tx status"""

    if response.status_code != SUCCESS_CODE:
        print(f"\nstatus code: {response.status_code}\n")
        return False

    data = json.loads(response.text)

    if data["err"] is not None:
        print(data["err"])
        return False

    print("tx status: ", TransferHistoryStatus[data["status"]])
    print("refund_reason:", XferStatus[data["refund_reason"]])

    if data["status"] == TRANSFER_COMPLETED or data["status"] == TRANSFER_REFUNDED:
        src_tx = data["src_block_tx_link"]
        dst_tx = data["dst_block_tx_link"]
        print(f"src_block_tx_link: {src_tx}\ndst_block_tx_link: {dst_tx}")
        return True

    return False


def get_celer_transfer_status(transfer_id):
    payload = json.dumps({"transfer_id": transfer_id})
    polling.poll(
        lambda: requests.request("POST", CELER_URL, headers=HEADERS, data=payload),
        check_success=is_correct_response,
        step=10,
        max_tries=30,
    )


if __name__ == "__main__":
    get_celer_transfer_status(
        "0xa9e4ca82b2ccff7506fe13eae3cbb8066d28fb8f23010ee8d58383d826ab2107"
    )
