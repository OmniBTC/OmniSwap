from brownie import GenesisBoxStaking

from scripts.helpful_scripts import get_account


def deploy_genesis_box_staking(nft_contract_address):
    account = get_account("deploy_key")
    genesis_box_staking = GenesisBoxStaking.deploy(nft_contract_address, {"from": account, "gas_price": "0.05 gwei"})
    return genesis_box_staking


def main():
    nft_contract_address = "0x09Ff8E49D0EA411A3422ed95E8f5497D4241F532"
    deploy_genesis_box_staking(nft_contract_address)
