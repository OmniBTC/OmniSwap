import yaml


def fix_brownie_config(chain):
    with open(f"{chain}/brownie-config.yaml", "r") as f:
        config = yaml.safe_load(f)

    config["dotenv"] = "./env/.env"

    with open(f"{chain}/brownie-config.yaml", "w") as f:
        yaml.safe_dump(config, f)


def main():
    fix_brownie_config("aptos")
    fix_brownie_config("sui")
    fix_brownie_config("ethereum")


if __name__ == "__main__":
    main()
