import secrets

from brownie import (
    ChainXBridge,
    Contract,
    config, network
)

from scripts.helpful_scripts import get_account


def load_chainx_bridge():
    return Contract.from_abi(
        "ChainXBridge",
        config["networks"][network.show_active()]["chainx_bridge"]
        , ChainXBridge.abi)


def main():
    chainx_bridge = load_chainx_bridge()
    acc = get_account()
    amount = int(1 / 1e8 * 1e18)
    print("nonce", acc.nonce)
    while True:
        start = acc.nonce
        end = 1000
        try:
            for _ in range(start, end):
                swap_id = f"0x{secrets.token_bytes(32).hex()}"
                swap_id = swap_id[:-4] + "cccc"
                chainx_bridge.swap_out(
                    swap_id,
                    10,
                    str(acc.address)[2:],
                    amount,
                    100,
                    {"from": acc, "value": amount}
                )
        except Exception as e:
            print("Error:", e)
        if acc.nonce >= end:
            break
