import json
import random
import time
from pathlib import Path

from brownie import Claim, MockToken, accounts

from scripts.helpful_scripts import get_account
from merkletreepy import MerkleTree


def write_json(file: Path, data):
    f = file.parent
    f.mkdir(parents=True, exist_ok=True)
    with open(str(file), "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def read_json(file):
    with open(file, "r") as f:
        return json.load(f)


def generate_test_account(count=2000):
    data = []

    for index in range(count):
        print("Generate:", index)
        acc = accounts.add()
        amount = random.randint(1e16, 1e22)
        data.append([
            acc.address,
            amount
        ])
    write_json(Path(__file__).parent.joinpath("data/test_airdrop_account.json"), data)


def generate_proof():
    account = get_account()
    data = read_json(Path(__file__).parent.joinpath("data/test_airdrop_account.json"))
    accs, amts = zip(*data)
    interval = 100
    print(f"All acount:{len(accs)}, interval:{interval}")
    for i in range(0, len(accs), interval):
        Claim[-1].batchSetClaim(accs[i:i + interval], amts[i:i + interval], {"from": account})
        break


def main():
    account = get_account()
    token_address = "0x4200000000000000000000000000000000000042"
    start = int(time.time() + 10)
    Claim.deploy(start, token_address, {"from": account})
