import functools
import json
from pathlib import Path
from typing import Union, List

from brownie import network, accounts, config, project, web3
from brownie.network.web3 import Web3
from brownie.network import priority_fee
from multiprocessing import Queue, Process, set_start_method

from brownie.project import get_loaded_projects

NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["hardhat", "development", "ganache"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = NON_FORKED_LOCAL_BLOCKCHAIN_ENVIRONMENTS + [
    "mainnet-fork",
    "binance-fork",
    "matic-fork",
]


def hex_str_to_vector_u8(data: str) -> List[int]:
    assert judge_hex_str(data)
    return list(bytearray.fromhex(data.replace("0x", "")))


def judge_hex_str(data: str):
    if not data.startswith("0x"):
        return False
    if len(data) % 2 != 0:
        return False
    try:
        web3.toInt(hexstr=data)
        return True
    except:
        return False


def to_hex_str(data: str):
    if judge_hex_str(data):
        return data
    else:
        return str("0x") + str(bytes(data, "ascii").hex())


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["from_key"])


def get_func_prototype(data):
    func_prototype = ""
    for index1, params in enumerate(data):
        if index1 > 0:
            func_prototype += ","
        if params["type"] in ["tuple", "tuple[]"]:
            func_prototype += "("
            func_prototype += get_func_prototype(params["components"])
            func_prototype += ")"
            if params["type"] == "tuple[]":
                func_prototype += "[]"
        else:
            func_prototype += params["type"]
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
    if dst_net in ["rinkeby", "goerli"]:
        priority_fee("2 gwei")


def zero_address():
    return "0x0000000000000000000000000000000000000000"


def read_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        return []


def padding_to_bytes(data: str, padding="right", length=32):
    if data[:2] == "0x":
        data = data[2:]
    padding_length = length * 2 - len(data)
    if padding == "right":
        return "0x" + data + "0" * padding_length
    else:
        return "0x" + "0" * padding_length + data


def combine_bytes(bs: list):
    output = "0x"
    for b in bs:
        output += b.replace("0x", "")
    return output


def find_loaded_projects(name):
    for loaded_project in get_loaded_projects():
        if loaded_project._name == name:
            return loaded_project


class TaskType:
    Execute = "execute"
    ExecuteWithProject = "execute_with_project"


class Session(Process):
    def __init__(
        self,
        net: str,
        project_path: Union[Path, str, None],
        group=None,
        name=None,
        kwargs={},
        *,
        daemon=None,
    ):
        self.net = net
        self.project_path = project_path
        try:
            set_start_method("spawn")
        except:
            pass
        self.task_queue = Queue(maxsize=1)
        self.result_queue = Queue(maxsize=1)

        super().__init__(
            group=group,
            target=self.work,
            name=name,
            args=(self.task_queue, self.result_queue),
            kwargs=kwargs,
            daemon=daemon,
        )
        self.start()

    def work(self, task_queue: Queue, result_queue: Queue):
        p = project.load(self.project_path, name=self.name)
        p.load_config()
        change_network(self.net)
        print(f"network {self.net} is connected!")
        while True:
            task_type, task = task_queue.get()
            if task_type == TaskType.Execute:
                result_queue.put(task())
            else:
                result_queue.put(task(p=p))

    def put_task(self, func, args=(), with_project=False):
        task = functools.partial(func, *args)
        if with_project:
            self.task_queue.put((TaskType.ExecuteWithProject, task))
        else:
            self.task_queue.put((TaskType.Execute, task))
        return self.result_queue.get()


def get_chain_id():
    return network.chain.id


def get_current_net_info():
    return config["networks"][network.show_active()]


def get_wormhole_info():
    return get_current_net_info()["wormhole"]


def get_wormhole_chainid():
    return get_wormhole_info()["chainid"]


def get_wormhole_bridge():
    return get_wormhole_info()["token_bridge"]


def get_wormhole_actual_reserve():
    return get_wormhole_info()["actual_reserve"]


def get_wormhole_estimate_reserve():
    return get_wormhole_info()["estimate_reserve"]


def get_oracles():
    return get_current_net_info()["oracle"]


def get_native_oracle_address():
    oracles = get_oracles()
    chainid = get_wormhole_chainid()
    for oracle in oracles:
        if chainid == oracles[oracle]["chainid"]:
            return oracles[oracle]["address"]


def get_celer_info():
    return get_current_net_info()["bridges"]["celer"]


def get_celer_message_bus():
    try:
        return get_celer_info()["message_bus"]
    except:
        return ""


def get_celer_chain_id():
    return get_celer_info()["chainid"]


def get_celer_oracles():
    return get_celer_info()["oracle"]


def get_celer_native_oracle_address():
    oracles = get_celer_oracles()
    chainid = get_celer_chain_id()
    for oracle in oracles:
        if chainid == oracles[oracle]["chainid"]:
            return oracles[oracle]["address"]


def get_celer_actual_reserve():
    return get_celer_info()["actual_reserve"]


def get_celer_estimate_reserve():
    return get_celer_info()["estimate_reserve"]


def get_multichain_info():
    return get_current_net_info()["bridges"]["multichain"]


def get_multichain_router():
    try:
        return get_multichain_info()["fast_router"]
    except:
        return ""


def get_multichain_id():
    return get_multichain_info()["chainid"]


def get_stargate_info():
    return get_current_net_info()["stargate"]


def get_stargate_router():
    try:
        return get_stargate_info()["router"]
    except:
        return ""


def get_stargate_chain_id():
    return get_stargate_info()["chainid"]


def get_stargate_pool_id(token_name: str):
    return get_stargate_info()["poolid"][token_name]


def get_swap_info():
    return get_current_net_info()["swap"]


def get_token_info(token_name: str):
    return get_current_net_info()["token"][token_name]


def get_token_address(token_name: str):
    if token_name == "eth":
        return zero_address()
    else:
        return get_token_info(token_name)["address"]


def get_token_decimal(token_name: str):
    if token_name == "eth":
        return 10**18
    else:
        return 10 ** get_token_info(token_name)["decimal"]


def get_bridge_token_info(bridge: str, token_name: str):
    return get_current_net_info()["bridges"][bridge]["token"][token_name]


def get_bridge_token_address(bridge: str, token_name: str):
    if token_name == "eth":
        return zero_address()
    else:
        return get_bridge_token_info(bridge, token_name)["address"]


def get_bridge_token_decimal(bridge: str, token_name: str):
    if token_name == "eth":
        return 10**18
    else:
        return 10 ** get_bridge_token_info(bridge, token_name)["decimal"]


def get_account_address():
    return get_account().address
