from brownie import (
    network,
    accounts,
    config,
    Contract,
    interface,
    web3
)
from brownie.network.web3 import Web3
from brownie.network import priority_fee

NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
    "mainnet-fork",
    "binance-fork",
    "matic-fork",
]

contract_to_type = {
    "stargate_router": interface.IStargate,
    "usdc": interface.IERC20
}

DECIMALS = 18
INITIAL_VALUE = web3.toWei(2000, "ether")


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])


def get_contract(contract_name):
    """If you want to use this function, go to the brownie config and add a new entry for
    the contract that you want to be able to 'get'. Then add an entry in the variable 'contract_to_type'.
    You'll see examples like the 'link_token'.
        This script will then either:
            - Get a address from the config
            - Or deploy a mock to use for a network that doesn't have it

        Args:
            contract_name (string): This is the name that is referred to in the
            brownie config and 'contract_to_type' variable.

        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            Contract of the type specificed by the dictionary. This could be either
            a mock or the 'real' contract on a live network.
    """
    contract_type = contract_to_type[contract_name]
    try:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        return contract
    except KeyError:
        print(
            f"{network.show_active()} address not found, perhaps you should add it to the config or deploy mocks?"
        )
        print(
            f"brownie run scripts/deploy_mocks.py --network {network.show_active()}"
        )


def get_func_prototype(data):
    func_prototype = ""
    for index1, params in enumerate(data):
        if index1 > 0:
            func_prototype += ','
        if params['type'] in ['tuple', 'tuple[]']:
            func_prototype += '('
            func_prototype += get_func_prototype(params['components'])
            func_prototype += ')'
            if params['type'] == 'tuple[]':
                func_prototype += "[]"
        else:
            func_prototype += params['type']
    return func_prototype


def get_method_signature_by_abi(abi):
    result = {}
    for d in abi:
        if d["type"] != "function":
            continue
        func_name = d["name"]
        func_prototype = get_func_prototype(d["inputs"])
        func_prototype = f"{func_name}({func_prototype})"
        result[func_name] = Web3.sha3(text=func_prototype)[0:4]
    return result


def get_event_signature_by_abi(abi):
    result = {}
    for d in abi:
        if d["type"] != "event":
            continue
        func_name = d["name"]
        func_prototype = get_func_prototype(d["inputs"])
        func_prototype = f"{func_name}({func_prototype})"
        result[func_name] = Web3.sha3(text=func_prototype)
    return result


def change_network(dst_net):
    if network.show_active() == dst_net:
        return
    if network.is_connected():
        network.disconnect()
    network.connect(dst_net)
    if dst_net in ["rinkeby"]:
        priority_fee("2 gwei")


def zero_address():
    return "0x0000000000000000000000000000000000000000"
