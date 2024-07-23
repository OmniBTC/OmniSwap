import json
import random
import secrets
import time
from pathlib import Path

from brownie import Claim, MockToken, accounts, web3, network, Contract
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
    account: Account = get_account("deploy_key")

    index = 152
    amount = 2982610
    proof = [
        "0x1e112fd4b580356956aa2c3f509b30bc566389f2a0cddf61d261c7a03e92eeb8",
        "0x20164d627e3006f7df7d47487500cd0ce526bb53bc715cdba27dedbb7a0b4771",
        "0x83cbae1b310a351d33eccbb3143a5772adab26b904096e807bea35e658da2598",
        "0xa3ef647496e97aa5d2e3a06fe838f7cd9bb571625622f99252fb28f82d87e409",
        "0xc3e0c3d1cd6f4a979894124df7f36a928bd910949e8eb1df2d3d65e58a1a0d25",
        "0x707578c46bc73214a0b075103e094217c7af9fd26b6a8d160447587b0bf8c5b5",
        "0x9673984e49a3dd103adb9af777d5752773275eba27c847f94f2f377a02208c82",
        "0x7c93a63fa304310cebf744fee5d4861678f48a3b29bbb10208a5437f81bcfc97",
        "0x98d72f54292e0f218430beadf30b31997b1bd83fa2df4fc7516dd9ee0ecf08e0",
        "0x953428c56793fba0d98258836a4f72c88d45eb8d4e7d5d13ddb799e2ad38b04d"
    ]
    Claim[-1].claim(index, amount, proof, {"from": account})


def deploy_op():
    account = get_account("deploy_key")
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x4200000000000000000000000000000000000042"
    start = int(time.time() + 10)
    merkle_root = "0xbffe5101179a4eb2955b92ec64142334ad44e75a7eb6adf0fca1f1dc4df9264f"
    Claim.deploy(start, token_address, merkle_root, {"from": account})


def deploy_bevm():
    account = get_account("deploy_key")
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x041bbB9c16fDBa8C805565D0bB34931e37895EC9"
    start = int(time.time() + 10)
    merkle_root = "0x83f3a31e458be02ec0c9996d9bf16c090f3409a19d658bf70e016bca900b725a"
    Claim.deploy(start, token_address, merkle_root, {"from": account, "gas_price": "0.05 gwei"})


def deploy_arb():
    account = get_account("deploy_key")
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x912CE59144191C1204E64559FE8253a0e49E6548"
    start = int(time.time() + 10)
    merkle_root = f"0x{secrets.token_bytes(32).hex()}"
    Claim.deploy(start, token_address, merkle_root, {"from": account})
    Claim[-1].pause({"from": account})


def deploy_poly():
    account = get_account("deploy_key")
    if "test" in network.show_active():
        MockToken.deploy("OP", "OP", {"from": account})
        token_address = MockToken[-1].address
    else:
        token_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    start = int(time.time() + 10)
    merkle_root = "0x0af56c4a460194df83b31f068a4c5bf9a915e97532de75437f651c488f3fd7d2"
    Claim.deploy(start, token_address, merkle_root, {"from": account})


def pause():
    account = get_account("deploy_key")
    c = Contract.from_abi("Claim", "0xE56a4CcfEaDb140333b91f561C6B0cF308450ac5", Claim.abi)
    # c.pause({"from": account})

    token_address = "0x4200000000000000000000000000000000000042"
    token = Contract.from_abi("Token", token_address, MockToken.abi)
    balance = token.balanceOf(c.address)

    c.reFund(token_address, balance, {"from": account})
