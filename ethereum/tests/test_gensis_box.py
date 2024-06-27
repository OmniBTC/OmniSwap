from pathlib import Path

import brownie
import pytest

from brownie import GenesisBoxStaking, MockNFT
from scripts.helpful_scripts import get_account, read_json

file_path = Path(__file__).parent.parent.joinpath("scripts/data")


@pytest.fixture
def nft():
    account = get_account()
    return account.deploy(MockNFT, "GenesisBox", "GBX")


@pytest.fixture
def genesis_box_staking(nft):
    account = get_account()
    return account.deploy(GenesisBoxStaking, nft.address)


def test_receive_nft(nft, genesis_box_staking):
    account = get_account()

    # Mint an NFT to the account
    nft.mint(account, {"from": account})
    token_id = 1

    # Approve and transfer the NFT to the staking contract
    nft.approve(genesis_box_staking.address, token_id, {"from": account})
    genesis_box_staking.receiveNFT(token_id, {"from": account})

    # Check the points assigned
    points = genesis_box_staking.getPoints(token_id)
    assert 500 <= points <= 1500, "Points should be between 500 and 1500"

    # Ensure the contract now owns the NFT
    assert nft.ownerOf(token_id) == genesis_box_staking.address, "Staking contract should own the NFT"

    # Try to claim the points
    with brownie.reverts("NOT OWNER"):
        genesis_box_staking.receiveNFT(token_id, {"from": account})
