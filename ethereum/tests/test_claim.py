import random
import time
from pathlib import Path

import brownie
import pytest

from brownie import Claim, MockToken

from scripts.helpful_scripts import get_account, read_json

file_path = Path(__file__).parent.parent.joinpath("scripts/data/chunks")


def get_address_index(user):
    mapping_data = read_json(file_path.joinpath("mapping.json"))
    for left, right in mapping_data.items():
        if left.lower() <= user.lower() <= right.lower():
            return left
    return "NotClaimed"


@pytest.fixture
def token():
    account = get_account()
    return account.deploy(MockToken, "OP", "OP")


@pytest.fixture
def claim(token):
    root_data = read_json(file_path.joinpath("root.json"))
    account = get_account()
    return account.deploy(Claim, int(time.time() + 1), token.address, root_data["root"])


def test_claim(token, claim):
    account = get_account()
    # Load test account data
    test_account_data = read_json(file_path.parent.joinpath("op_account_20231115.json"))

    # # Check state
    indexes = random.choices(list(range(len(test_account_data))), k=100)
    for i in indexes:
        address = test_account_data[i][0]
        address_index = get_address_index(address)
        assert address_index != "NotClaimed", "NotClaimed"
        proof_data = read_json(file_path.joinpath(f"{address_index}.json"))
        account_data = proof_data[address]
        account_data["amount"] = int(account_data["amount"])
        assert claim.getState(account_data["index"], address,
                              account_data["amount"], account_data["proof"]) == "PendingClaimed"

    # # Test account state
    # new_account_data = None
    # new_account = None
    # indexes = random.choices(list(range(len(test_account_data))), k=100)
    # for i in indexes:
    #     new_account = brownie.accounts.add(test_account_data[i][-1])
    #     address_index = get_address_index(new_account.address)
    #     assert address_index != "NotClaimed", "NotClaimed"
    #     proof_data = read_json(file_path.joinpath(f"{address_index}.json"))
    #     new_account_data = proof_data[new_account.address]
    #     new_account_data["amount"] = int(new_account_data["amount"])
    #     assert claim.getState(new_account_data["index"], new_account.address,
    #                           new_account_data["amount"], new_account_data["proof"]) == "PendingClaimed"
    #
    # # Test account claim
    # assert claim.getState(new_account_data["index"], account, new_account_data["amount"],
    #                       new_account_data["proof"]) == "NotClaimed"
    # transfer_amount = new_account_data["amount"] * 2
    # token.mint(account, transfer_amount, {"from": account})
    # token.transfer(claim, transfer_amount, {"from": account})
    # assert token.balanceOf(claim) == transfer_amount
    #
    # before = token.balanceOf(new_account)
    # time.sleep(1)
    # claim.claim(new_account_data["index"], new_account_data["amount"], new_account_data["proof"], {"from": new_account})
    # assert token.balanceOf(new_account) - before == new_account_data["amount"]
    # assert token.balanceOf(claim) == new_account_data["amount"]
    # with brownie.reverts("HasClaimed"):
    #     claim.claim(new_account_data["index"], new_account_data["amount"], new_account_data["proof"],
    #                 {"from": new_account})
    #
    # # Test refund
    # with brownie.reverts("Ownable: caller is not the owner"):
    #     claim.reFund(token, new_account_data["amount"], {"from": new_account})
    # claim.reFund(token, new_account_data["amount"], {"from": account})
    # assert token.balanceOf(claim) == 0
