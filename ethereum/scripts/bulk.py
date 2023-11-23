from pathlib import Path

from brownie import (
    BulkTransfer,
    MockToken,
    Contract
)

from scripts.helpful_scripts import get_account, read_json


def bulk_test():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    test_data = [
        [acc.address, acc.address],
        [int(1 * 1e18), int(0.5 * 1e18)]
    ]

    # op
    token_addr = "0x4200000000000000000000000000000000000042"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    print(int(sum(test_data[1]) + 1))
    token.approve(BulkTransfer[-1].address, int(sum(test_data[1]) + 1), {"from": acc})

    BulkTransfer[-1].batchTransferToken(token.address, test_data[0], test_data[1], {"from": acc})


def bulk():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/op_account_20231123.json"))

    data = list(zip(*data))

    print(data)
    # op
    token_addr = "0x4200000000000000000000000000000000000042"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    token.approve(BulkTransfer[-1].address, int(sum(data[1]) + 1), {"from": acc})

    # BulkTransfer[-1].batchTransferToken(token, data[0], data[1], {"from": acc})
