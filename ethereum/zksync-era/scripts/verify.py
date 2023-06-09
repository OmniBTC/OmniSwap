import subprocess
import json
import argparse

DEPLOYED = "./deployed.json"


def read_json(file):
    try:
        with open(file) as f:
            return json.load(f)
    except:
        print(f"Err: open {file}")
        return []


def get_deployed_contracts():
    return read_json(DEPLOYED)


def execute_command(command):
    process = subprocess.Popen(
        command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Command execution failed with error: {error.decode('utf-8')}")
    else:
        print(f"Command executed successfully:\n{output.decode('utf-8')}")


def main():

    deployer = ""
    so_diamond = ""
    diamond_cut = ""
    base_cmd = "yarn hardhat verify "

    parser = argparse.ArgumentParser()
    parser.add_argument("--main", action="store_true")
    parser.add_argument("--deployer", required=True)
    args = parser.parse_args()

    if args.main:
        base_cmd = base_cmd + "--network zkMainnet "

    if args.deployer != "":
        deployer = args.deployer
    else:
        print("Invalid deployer")

    verify_cmds = []

    for (name, address) in get_deployed_contracts().items():
        # print(name, address)
        if name == "SoDiamond":
            so_diamond = address
            continue

        if name == "DiamondCutFacet":
            diamond_cut = address

        verify_cmds.append(base_cmd + address)

    if deployer == "":
        print("Not set deployer")
        return

    with_constructor_args_cmd = (
        base_cmd + so_diamond + " " + deployer + " " + diamond_cut
    )
    verify_cmds.append(with_constructor_args_cmd)

    for command in verify_cmds:
        print(command)
        execute_command(command)


if __name__ == "__main__":
    main()
