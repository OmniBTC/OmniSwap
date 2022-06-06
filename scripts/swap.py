# @Time    : 2022/6/6 13:55
# @Author  : WeiDai
# @FileName: swap.py
from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, network, config

from scripts.helpful_scripts import get_account, get_contract


def main():
    account = get_account()
    so_diamond = SoDiamond[-1]
    net = network.show_active()
    print(f"SoDiamond:{so_diamond}, Network:{net}, account:{account.address}")
    proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)

    usdc = get_contract("usdc")
    # 1 usdc
    usdc_amount = 1

    dst_nets = ["ftm-test", "avax-test"]
    for dst_net in dst_nets:
        if dst_net == net:
            continue
        dst_chainid = config["networks"][dst_net]["stargate_chainid"]
        print(f"from:{net}->to:{dst_net}, startBridgeTokensViaStargate...")
        so_data = ["0x0000000000000000000000000000000000000000000000000000000000000000",
                   "0x0000000000000000000000000000000000000000", "0x076488D244A73DA4Fa843f5A8Cd91F655CA81a1e",
                   "0xB6B12aDA59a8Ac44Ded72e03693dd14614224349", dst_chainid, 100000000]
        stargate_data = [1,
                         dst_chainid,
                         1,
                         usdc_amount,
                         int(usdc_amount * 0.9),
                         [0, 0, b""],
                         account,
                         usdc.address]
        usdc.approve(so_diamond, usdc_amount, {'from': account})
        proxy_stargate.startBridgeTokensViaStargate(
            so_data,
            stargate_data,
            {'from': account, 'value': 10000000000000000}
        )

