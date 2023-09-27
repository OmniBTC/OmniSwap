import json
import random
import secrets
import time
from pathlib import Path

from brownie import Claim, MockToken, accounts, web3, network
from brownie.network.account import Account

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
        data[i][1] = str(int(data[i][1]))
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


def claim_test():
    account: Account = get_account()

    index = 808
    amount = 2467489637769138280061
    proof = [
        "0x71087c4d990909323ac5fe7efadb7e2b630d482d0192be03c96da964b3163a6f",
        "0x74ba0035eb40d276197a366e6793c94500df39ceabbeea8f9de1e46186ee0440",
        "0x7c5976b7c29df481480e5d6215c30f13abefa31e7eac1c3164fd23b48128ae3f",
        "0x1241e63c00d69ac02e8fdcbc5925d4a49dafe0e23f1fbfa5cd33761533c7d14b",
        "0x8e6ff94322bb620a53a2a58aeadfb28074f7706345e282a85db3e6db8cedf46a",
        "0x70ba4c5be4736525cbf00b834cae36ce46d17499ca8b16297336b56546895c5c",
        "0xf75db365841adacb53eb699d0dc0773734eee52fb9730e5ff6f2dedb7f0bbd74",
        "0x449c88bf14260a967529033b3acd71b004f2cc8644de24c1cc93e215a7d9e132",
        "0xaead6e5191d458c7e115584edcfb7262d11a13bfd4375e1a7ea6c9286c4ab566",
        "0x400d126f35c6fbbb437c42decb116541945114b915ea41654ef5eda52f00a510",
        "0x4eaf2844f368dbe2c98f9513f488c92c26a5a0c9dbd58586c5763e95113399f4",
        "0xeecb42086fac38b632e53fb848900544fcd40d14a07aaba61fcb9f83d8806cad",
        "0xf411c5ba74f39059b3823080dd25e3bf2a09fc15601395577509674d82027e7a",
        "0x6b942e058a31016399412c20008b5bf23f96e04778cd279dc8767910cdde6b9c",
        "0x636d83c93bf376bfd7a51df6607cedafea762c8d430db4fc2187265e2c389d07"
    ]
    # MockToken[-1].transfer(Claim[-1].address, amount, {"from": account})
    new_account = accounts.add("0xdd04778b596300c3d5b3fce9e00bfbfdc21af16a69d515ccaeb000307f41e2fe")
    # account.transfer(new_account, int(0.0001 * 1e18))
    Claim[-1].claim(index, amount, proof, {"from": new_account})


def deploy_op():
    account = get_account()
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x4200000000000000000000000000000000000042"
    start = int(time.time() + 10)
    merkle_root = "0x9ae91b8f4b19e1661c68035121d6327515524954587e14f75a8d30254386b9b8"
    Claim.deploy(start, token_address, merkle_root, {"from": account})


def deploy_arb():
    account = get_account()
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
    start = int(time.time() + 10)
    merkle_root = f"0x{secrets.token_bytes(32).hex()}"
    Claim.deploy(start, token_address, merkle_root, {"from": account})
    Claim[-1].pause({"from": account})
