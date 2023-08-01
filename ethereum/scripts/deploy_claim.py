import json
import random
import time
from pathlib import Path

from brownie import Claim, MockToken, accounts, web3

from scripts.helpful_scripts import get_account, write_json, read_json
from merkletreepy import MerkleTree


def generate_test_account(count=300):
    data = []

    for index in range(count):
        print("Generate:", index)
        acc = accounts.add()
        amount = random.randint(1, 10000)
        data.append([
            acc.address,
            amount,
            str(acc.private_key)
        ])
    write_json(Path(__file__).parent.joinpath("data/test_airdrop_account.json"), data)


def format_account():
    file = Path(__file__).parent.joinpath("data/test_airdrop_account.json")
    data = read_json(file)
    for i in range(len(data)):
        data[i][1] = str(int(data[i][1] * 1e18))
    write_json(file, data)


def keccak256(x):
    return bytes.fromhex(web3.keccak(x).hex()[2:])


def generate_node(data: list):
    data = [[index, d[0], d[1]] for index, d in enumerate(sorted(data, key=lambda x: x[0].lower()))]
    nodes = [bytes.fromhex(web3.solidityKeccak(['uint256', 'address', 'uint256'], d).hex()[2:]) for d in data]
    return nodes, data


def generate_proof():
    data = read_json(Path(__file__).parent.joinpath("data/test_airdrop_account.json"))
    nodes, data = generate_node(data)
    tree = MerkleTree(nodes, keccak256, sort=True)
    root = tree.get_hex_root()

    DESIRED_COHORT_SIZE = 101

    address_chunks = {}

    file_path = Path(__file__).parent.joinpath("data/chunks")

    for i in range(0, len(data), DESIRED_COHORT_SIZE):
        last_index = min(i + DESIRED_COHORT_SIZE - 1, len(nodes) - 1)
        address_chunks[data[i][1]] = data[last_index][1]
        address_proofs = {}
        for j in range(i, last_index + 1):
            print(f"Generate {j} for {len(nodes)} nodes")
            address_proofs[data[j][1]] = {
                "index": data[j][0],
                "amount": data[j][2],
                "proof": [f"0x{d}" for d in tree.get_hex_proof(nodes[j])]
            }
        cur_file = file_path.joinpath(f"{data[i][1]}.json")
        write_json(cur_file, address_proofs)
    root_data = {"root": root}
    root_file = file_path.joinpath("root.json")
    write_json(root_file, root_data)

    map_file = file_path.joinpath("mapping.json")
    write_json(map_file, address_chunks)


def main():
    account = get_account()
    token_address = "0x4200000000000000000000000000000000000042"
    start = int(time.time() + 10)
    Claim.deploy(start, token_address, {"from": account})
