import time

import brownie
import pytest

from brownie import Claim, MockToken

from scripts.helpful_scripts import get_account


@pytest.fixture
def token():
    account = get_account()
    return account.deploy(MockToken, "OP", "OP")


@pytest.fixture
def claim(token):
    account = get_account()
    return account.deploy(Claim, int(time.time() + 1), token.address)


def test_claim(token, claim):
    account = get_account()
    new_account = brownie.accounts.add()
    assert claim.getState(account) == "NotClaimed"
    token.transfer(claim, 2000, {"from": account})
    assert token.balanceOf(claim) == 2000
    claim.setClaim(account, 900)
    assert claim.getState(account) == "PendingClaimed"
    before = token.balanceOf(account)
    time.sleep(1)
    claim.claim({"from": account})
    assert token.balanceOf(account) - before == 900
    assert token.balanceOf(claim) == 1100
    with brownie.reverts("HasClaimed"):
        claim.claim({"from": account})
    with brownie.reverts("Ownable: caller is not the owner"):
        claim.reFund(token, 1100, {"from": new_account})
    claim.reFund(token, 1100, {"from": account})
    assert token.balanceOf(claim) == 0



