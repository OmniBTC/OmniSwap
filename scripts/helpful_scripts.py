import functools
import json
from pathlib import Path
from typing import Union

from brownie import (
    network,
    accounts,
    config,
    project
)
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
    def __init__(self,
                 net: str,
                 project_path: Union[Path, str, None],
                 group=None,
                 name=None,
                 kwargs={},
                 *,
                 daemon=None):
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
            daemon=daemon
        )
        self.start()

    def work(self,
             task_queue: Queue,
             result_queue: Queue):
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


def get_stargate_info():
    return get_current_net_info()["stargate"]


def get_stargate_router():
    return get_stargate_info()["router"]


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
        return 10 ** 18
    else:
        return 10 ** get_token_info(token_name)["decimal"]


def get_account_address():
    return get_account().address
