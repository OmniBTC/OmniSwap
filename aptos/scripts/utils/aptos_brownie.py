from __future__ import annotations

import abc
import functools
import os
import time
from pathlib import Path
from typing import Union, List

from aptos_sdk.bcs import Deserializer, Serializer
from aptos_sdk.transactions import EntryFunction, ModuleId, TransactionArgument, TransactionPayload
from aptos_sdk.type_tag import TypeTag, StructTag, AccountAddressTag, U128Tag, U64Tag, U8Tag, BoolTag
from dotenv import load_dotenv
from aptos_sdk.account import Account
from aptos_sdk.client import RestClient, FaucetClient

import yaml
import toml

Tag = Union[BoolTag, U8Tag, U64Tag, U128Tag, AccountAddressTag, StructTag]


class VectorTag(metaclass=abc.ABCMeta):
    value: List[Tag]

    def __init__(self, value):
        self.value = value

    def __eq__(self, other: VectorTag) -> bool:
        return self.value == other.value

    def variant(self):
        return TypeTag.VECTOR

    @abc.abstractmethod
    def deserialize(deserializer: Deserializer) -> VectorTag:
        raise NotImplementedError

    def serialize(self, serializer: Serializer):
        serializer.sequence(self.value, Serializer.struct)


class VectorBoolTag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([BoolTag(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorBoolTag:
        return deserializer.sequence(BoolTag.deserialize)


class VectorU8Tag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([U8Tag(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorU8Tag:
        return deserializer.sequence(U8Tag.deserialize)


class VectorU64Tag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([U64Tag(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorU64Tag:
        return deserializer.sequence(U64Tag.deserialize)


class VectorU128Tag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([U128Tag(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorU128Tag:
        return deserializer.sequence(U128Tag.deserialize)


class VectorAccountAddressTag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([AccountAddressTag(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorAccountAddressTag:
        return deserializer.sequence(AccountAddressTag.deserialize)


class VectorStructTag(VectorTag):
    def __init__(self, value):
        assert isinstance(list(value), list), "value must sequence"
        super().__init__([StructTag.from_str(v) for v in value])

    def deserialize(deserializer: Deserializer) -> VectorStructTag:
        return deserializer.sequence(StructTag.deserialize)


class ArgumentABI:
    name: str
    type_tag: type(Tag)

    def __init__(self, name: str, type_tag):
        self.name = name
        self.type_tag = type_tag

    def __repr__(self):
        return f'{"{"}"name": "{self.name}", "type_tag": "{self.type_tag.__name__}"{"}"}'

    def __str__(self):
        self.__repr__()

    def __eq__(self, other: ArgumentABI) -> bool:
        return self.name == other.name and self.type_tag == other.type_tag

    @staticmethod
    def get_tag(variant: int):
        if variant == TypeTag.BOOL:
            return BoolTag
        elif variant == TypeTag.U8:
            return U8Tag
        elif variant == TypeTag.U64:
            return U64Tag
        elif variant == TypeTag.U128:
            return U128Tag
        elif variant == TypeTag.ACCOUNT_ADDRESS:
            return AccountAddressTag
        elif variant == TypeTag.SIGNER:
            raise NotImplementedError
        elif variant == TypeTag.VECTOR:
            return VectorTag
        elif variant == TypeTag.STRUCT:
            return StructTag
        raise NotImplementedError

    @staticmethod
    def get_vector_tag(tag):
        if tag == BoolTag:
            return VectorBoolTag
        elif tag == U8Tag:
            return VectorU8Tag
        elif tag == U64Tag:
            return VectorU64Tag
        elif tag == U128Tag:
            return VectorU128Tag
        elif tag == AccountAddressTag:
            return VectorAccountAddressTag
        elif tag == VectorTag:
            raise NotImplementedError
        elif tag == StructTag:
            return VectorStructTag
        raise NotImplementedError

    def deserialize(deserializer: Deserializer) -> ArgumentABI:
        name = deserializer.str()
        variant = deserializer.uleb128()
        type_tag = ArgumentABI.get_tag(variant)
        if type_tag == VectorTag:
            variant = deserializer.uleb128()
            type_tag = ArgumentABI.get_vector_tag(ArgumentABI.get_tag(variant))
        return ArgumentABI(name, type_tag)


class EntryFunctionABI:
    name: str
    module: ModuleId
    doc: str
    ty_args: List[str]
    args: List[ArgumentABI]

    def __init__(self, name, module, doc, ty_args, args):
        self.name = name
        self.module = module
        self.doc = doc
        self.ty_args = ty_args
        self.args = args

    def key(self):
        return f"{self.module.name}::{self.name}"

    def __repr__(self):
        return f'{"{"}"name": "{self.name}", "module": "{self.module}", "doc": "{self.doc}", ' \
               f'"ty_args": {self.ty_args}, "args": {self.args}{"}"}'

    def deserialize(deserializer: Deserializer) -> EntryFunctionABI:
        deserializer.u8()
        name = deserializer.str()
        module = ModuleId.deserialize(deserializer)
        doc = deserializer.str()
        ty_args = deserializer.sequence(Deserializer.str)
        args = deserializer.sequence(ArgumentABI.deserialize)
        return EntryFunctionABI(name, module, doc, ty_args, args)


class AptosPackage:
    def __init__(self,
                 project_path: Union[Path, str] = Path.cwd(),
                 network: str = "aptos-testnet"
                 ):
        if isinstance(project_path, Path):
            self.project_path = project_path
        else:
            self.project_path = Path(project_path)
        self.network = network

        # # # # # load config
        assert self.project_path.joinpath("brownie-config.yaml").exists(), "brownie-config.yaml not found"
        self.config_path = self.project_path.joinpath("brownie-config.yaml")
        self.config = {}
        with self.config_path.open() as fp:
            self.config = yaml.safe_load(fp)
        try:
            load_dotenv(self.project_path.joinpath(self.config["dotenv"]))
            self.private_key = os.getenv("PRIVATE_KEY")
            if self.private_key is None:
                raise EnvironmentError
        except Exception as e:
            raise e
        self.account = Account.load_key(self.private_key)
        self.network_config = self.config["networks"][network]
        self.rest_client = RestClient(self.config["networks"][network]["node_url"])
        self.faucet_client = FaucetClient(self.config["networks"][network]["faucet_url"], self.rest_client)

        # # # # # load move toml
        assert self.project_path.joinpath("Move.toml").exists(), "Move.toml not found"
        self.move_path = self.project_path.joinpath("Move.toml")
        self.move_toml = {}
        with self.move_path.open() as fp:
            self.move_toml = toml.load(fp)
        self.package_name = self.move_toml["package"]["name"]

        # # # # # Replace address
        self.replace_address = ""
        has_replace = {}
        if "addresses" in self.move_toml:
            if "replace_address" in self.network_config:
                for k in self.network_config["replace_address"]:
                    if k not in self.move_toml["addresses"] or (k in has_replace):
                        continue
                    if len(self.replace_address) == 0:
                        self.replace_address = f"--named-addresses {k}={self.network_config['replace_address'][k]}"
                    else:
                        self.replace_address += f',{k}={self.network_config["replace_address"][k]}'
                    has_replace[k] = True
            for k in self.move_toml["addresses"]:
                if k in has_replace:
                    continue
                if self.move_toml["addresses"][k] == "_":
                    if len(self.replace_address) == 0:
                        self.replace_address = f"--named-addresses {k}={self.account.account_address}"
                    else:
                        self.replace_address += f',{k}={self.account.account_address}'

        # # # # # Compile
        view = "Compile"
        print("-" * 50 + view + "-" * 50)
        compile_cmd = f"aptos move compile --included-artifacts all --save-metadata --package-dir {self.project_path} {self.replace_address}"
        print(compile_cmd)
        os.system(compile_cmd)
        print("-" * (100 + len(view)))
        print("\n")

        # # # # # Metadata
        self.build_path = self.project_path.joinpath(f"build/{self.package_name}")
        with open(self.build_path.joinpath(f"package-metadata.bcs"), "rb") as f:
            self.package_metadata = f.read()

        # # # # # Bytecode
        self.move_module_files = []
        bytecode_modules = self.build_path.joinpath("bytecode_modules")
        for m in os.listdir(bytecode_modules):
            if str(m).endswith(".mv"):
                self.move_module_files.append(bytecode_modules.joinpath(str(m)))
        self.move_modules = []
        for m in self.move_module_files:
            with open(m, "rb") as f:
                self.move_modules.append(f.read())

        # # # # # Abis
        self.abis_path = self.build_path.joinpath("abis")
        self.abis = {}
        if self.abis_path.exists():
            for v1 in os.listdir(self.abis_path):
                module_abi_path = self.abis_path.joinpath(str(v1))
                if not module_abi_path.is_dir():
                    continue
                for v2 in os.listdir(module_abi_path):
                    if not str(v2).endswith(".abi"):
                        continue
                    with open(module_abi_path.joinpath(str(v2)), "rb") as f:
                        data = f.read()
                        abi = EntryFunctionABI.deserialize(Deserializer(data))
                        self.abis[abi.key()] = abi

    def publish_package(self):
        txn_hash = self.rest_client.publish_package(self.account, self.package_metadata, self.move_modules)
        print(f"Publish package: {self.package_name}, hash: {txn_hash}, waiting...")
        self.rest_client.wait_for_transaction(txn_hash)
        print(f"Publish package: {self.package_name} Success.\n")

    def __getitem__(self, key):
        assert key in self.abis, f"key not found in abi"
        return functools.partial(self.submit_bcs_transaction, self.abis[key])

    def submit_bcs_transaction(
            self, abi: EntryFunctionABI, *args, ty_args: List[str] = None, **kwargs,
    ) -> dict:
        if ty_args is None:
            ty_args = []
        assert isinstance(list(ty_args), list) and len(abi.ty_args) == len(ty_args), f"ty_args error: {abi.ty_args}"
        assert len(args) == len(abi.args) or len(kwargs) == len(abi.args), f"args error: {abi.args}"

        normal_args = []
        if len(kwargs):
            for function_arg in abi.args:
                assert function_arg.name in kwargs, f"Param {function_arg.name} not found"
                if function_arg.type_tag == StructTag:
                    assert StructTag.from_str(kwargs[function_arg.name]), f"Param {function_arg} not match"
                    value = StructTag.from_str(kwargs[function_arg.name])
                else:
                    assert function_arg.type_tag(kwargs[function_arg.name]), f"Param {function_arg} not match"
                    value = function_arg.type_tag(kwargs[function_arg.name])
                normal_args.append({
                    "value": value,
                    "abi": function_arg})
        else:
            for i, function_arg in enumerate(abi.args):
                if function_arg.type_tag == StructTag:
                    assert StructTag.from_str(args[i]), f"Param {function_arg} not match"
                    value = StructTag.from_str(args[i])
                else:
                    assert function_arg.type_tag(args[i]), f"Param {function_arg} not match"
                    value = function_arg.type_tag(args[i])

                normal_args.append({
                    "value": value,
                    "abi": function_arg})

        payload = EntryFunction.natural(
            str(abi.module),
            str(abi.name),
            [TypeTag(StructTag.from_str(v)) for v in ty_args],
            [
                TransactionArgument(arg["value"], Serializer.struct)
                for arg in normal_args
            ],
        )
        signed_transaction = self.rest_client.create_single_signer_bcs_transaction(
            self.account, TransactionPayload(payload)
        )
        txn_hash = self.rest_client.submit_bcs_transaction(signed_transaction)
        print(f"Execute {abi.module.name}::{abi.name}, transaction hash: {txn_hash}, waiting...")
        response = self.wait_for_transaction(txn_hash)
        print(f"Execute {abi.module.name}::{abi.name} Success.\n")
        return {
            "hash": txn_hash,
            "response": response
        }

    def wait_for_transaction(self, txn_hash: str):
        """Waits up to 20 seconds for a transaction to move past pending state."""

        count = 0
        while self.rest_client.transaction_pending(txn_hash):
            assert count < 20, f"transaction {txn_hash} timed out"
            time.sleep(1)
            count += 1
        response = self.rest_client.client.get(f"{self.rest_client.base_url}/transactions/by_hash/{txn_hash}")
        assert (
                "success" in response.json() and response.json()["success"]
        ), f"{response.text} - {txn_hash}"
        return response.json()


if __name__ == "__main__":
    # # # # # Example
    omniswap = AptosPackage("../..")
    omniswap.publish_package()
    try:
        # Maybe dump initialize
        omniswap["so_fee_wormhole_v1::initialize"]()
    except:
        pass
    omniswap["so_fee_wormhole_v1::set_price_ratio"](1, 1)
