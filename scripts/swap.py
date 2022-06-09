import time

from brownie import DiamondCutFacet, SoDiamond, DiamondLoupeFacet, DexManagerFacet, StargateFacet, WithdrawFacet, \
    OwnershipFacet, GenericSwapFacet, interface, Contract, config, web3

from scripts.helpful_scripts import get_account, change_network, zero_address, get_contract


def generate_dst_swap_data(dst_net: str, func_name: str, amount_in: int, receiving_asset_id: str):
    change_network(dst_net)
    so_diamond = SoDiamond[-1]
    dst_swap_info = config["networks"][dst_net]["swap"][0]
    dst_swap = Contract.from_abi(
        dst_swap_info[1], dst_swap_info[0], getattr(interface, dst_swap_info[1]).abi)
    approve_to = dst_swap.address
    call_to = dst_swap.address
    sending_asset_id = config["networks"][dst_net]["usdc"]
    if receiving_asset_id == zero_address():
        path = [sending_asset_id, config["networks"][dst_net]["weth"]]
    else:
        path = [sending_asset_id, receiving_asset_id]
    from_amount = 0
    call_data = getattr(dst_swap, func_name).encode_input(
        amount_in,
        0,
        path,
        so_diamond.address,
        int(time.time() + 3000)
    )
    swap_data = [[approve_to, call_to, sending_asset_id,
                  receiving_asset_id, from_amount, call_data]]
    return swap_data


def generate_src_swap_data(src_net: str, func_name: str, amount_in: int, sending_asset_id: str):
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    src_swap_info = config["networks"][src_net]["swap"][0]
    src_swap = Contract.from_abi(
        src_swap_info[1], src_swap_info[0], getattr(interface, src_swap_info[1]).abi)
    approve_to = src_swap.address
    call_to = src_swap.address
    receiving_asset_id = config["networks"][src_net]["usdc"]
    if sending_asset_id == zero_address():
        path = [config["networks"][src_net]["weth"], receiving_asset_id]
        call_data = getattr(src_swap, func_name).encode_input(
            0,
            path,
            so_diamond.address,
            int(time.time() + 3000)
        )
        from_amount = amount_in
        swap_data = [[approve_to, call_to, sending_asset_id,
                      receiving_asset_id, from_amount, call_data]]
        return swap_data, from_amount
    else:
        path = [sending_asset_id, receiving_asset_id]
        call_data = getattr(src_swap, func_name).encode_input(
            amount_in,
            0,
            path,
            so_diamond.address,
            int(time.time() + 3000)
        )
        from_amount = 0
        swap_data = [[approve_to, call_to, sending_asset_id,
                      receiving_asset_id, from_amount, call_data]]
        return swap_data, from_amount


def generate_so_data(dst_net: str, receiver: str, amount_in: int):
    return ["0x0000000000000000000000000000000000000000000000000000000000000000", receiver, 1,
            "0x0000000000000000000000000000000000000000", 2, "0x076488D244A73DA4Fa843f5A8Cd91F655CA81a1e",
            amount_in]


def generate_stargate_data(src_net: str,
                           dst_net: str,
                           usdc_amount: int,
                           src_fee: int,
                           dst_gas: int):
    change_network(dst_net)
    so_diamond = SoDiamond[-1]
    return [1,
            config["networks"][src_net]["usdc"],
            config["networks"][dst_net]["stargate_chainid"],
            1,
            int(usdc_amount * 0.9),
            [dst_gas, 0, b""],
            so_diamond.address]


def estimate_dst_gas(src_net: str,
                     dst_net: str,
                     so_data: list,
                     dst_swap: list,
                     ):
    change_network(dst_net)
    account = get_account()
    so_diamond = SoDiamond[-1]
    proxy_stargate = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    payload = proxy_stargate.encodePayload(so_data, dst_swap)
    calldata = proxy_stargate.sgReceive.encode_input(
        config["networks"][src_net]["stargate_chainid"],
        so_diamond.address,
        0,
        config["networks"][dst_net]["usdc"],
        10 * 10 ** 6,
        payload)
    return account.estimate_gas(so_diamond.address, 0, data=calldata)


def swap(src_net: str, dst_net: str):
    account = get_account()

    # 1. startBridgeTokensViaStargate
    # print(f"from:{src_net}->to:{dst_net}, startBridgeTokensViaStargate...")
    # # # generate data
    # usdc_amount = int(100 * 1e6)
    # so_data = generate_so_data(dst_net, account, usdc_amount)
    # src_fee = int(0.01 * 1e18)
    # dst_gas = 100000
    # stargate_data = generate_stargate_data(src_net, dst_net, usdc_amount, src_fee, dst_gas)
    # # # call
    # change_network(src_net)

    # usdc = get_contract("usdc")
    # so_diamond = SoDiamond[-1]
    # usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    # proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # proxy_stargate.soSwapViaStargate(
    #     so_data,
    #     [],
    #     stargate_data,
    #     [],
    #     {'from': account, 'value': src_fee}
    # )

    # 2. startSwapAndBridgeTokensViaStargate
    # print(f"from:{src_net}->to:{dst_net}, startSwapAndBridgeTokensViaStargate...")
    # # # generate data
    # so_data = generate_so_data(dst_net, account, int(2 * 1e-10 * 1e18))
    # usdc_amount = int(100 * 1e6)
    # src_fee = int(0.01 * 1e18)
    # dst_gas = 100000
    # stargate_data = generate_stargate_data(src_net, dst_net, usdc_amount, src_fee, dst_gas)
    # if src_net == "rinkeby":
    #     func_name = "swapExactETHForTokens"
    # elif src_net == "avax-test":
    #     func_name = "swapExactAVAXForTokens"
    # else:
    #     raise ValueError
    # src_swap_data, from_amount = generate_src_swap_data(src_net, func_name, int(2 * 1e-10 * 1e18), zero_address())
    # # # call
    # change_network(src_net)
    # so_diamond = SoDiamond[-1]
    # proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # proxy_stargate.soSwapViaStargate(
    #     so_data,
    #     src_swap_data,
    #     stargate_data,
    #     [],
    #     {'from': account, 'value': int(from_amount + src_fee)}
    # )

    # 3. startBridgeTokensAndSwapViaStargate
    print(f"from:{src_net}->to:{dst_net}, startBridgeTokensAndSwapViaStargate...")
    # # generate data
    usdc_amount = int(100 * 1e6)
    so_data = generate_so_data(dst_net, account, usdc_amount)
    src_fee = int(0.01 * 1e18)

    if dst_net == "rinkeby":
        func_name = "swapExactTokensForETH"
    elif dst_net == "avax-test":
        func_name = "swapExactTokensForAVAX"
    else:
        raise ValueError
    dst_swap_data = generate_dst_swap_data(
        dst_net, func_name, int(99 * 1e6), zero_address())

    dst_gas = estimate_dst_gas(src_net, dst_net, so_data, dst_swap_data)
    print(f"Estimated dst_gas:{dst_gas}")

    stargate_data = generate_stargate_data(
        src_net, dst_net, usdc_amount, src_fee, dst_gas)

    # # call
    change_network(src_net)
    so_diamond = SoDiamond[-1]
    usdc = get_contract("usdc")
    usdc.approve(so_diamond.address, usdc_amount, {'from': account})
    proxy_stargate = Contract.from_abi(
        "StargateFacet", so_diamond.address, StargateFacet.abi)
    proxy_stargate.soSwapViaStargate(
        so_data,
        [],
        stargate_data,
        dst_swap_data,
        {'from': account, 'value': src_fee}
    )

    # 4. startSwapAndSwapViaStargate
    # print(f"from:{src_net}->to:{dst_net}, startSwapAndSwapViaStargate...")
    # # # generate data
    # usdc_amount = int(100 * 1e6)
    # so_data = generate_so_data(dst_net, account, usdc_amount)
    # src_fee = int(0.01 * 1e18)
    # dst_gas = 300000
    # stargate_data = generate_stargate_data(src_net, dst_net, usdc_amount, src_fee, dst_gas)
    # if src_net == "rinkeby":
    #     func_name = "swapExactETHForTokens"
    # elif src_net == "avax-test":
    #     func_name = "swapExactAVAXForTokens"
    # else:
    #     raise ValueError
    # src_swap_data, from_amount = generate_src_swap_data(src_net, func_name, int(2 * 1e-10 * 1e18), zero_address())
    # if dst_net == "rinkeby":
    #     func_name = "swapExactTokensForETH"
    # elif dst_net == "avax-test":
    #     func_name = "swapExactTokensForAVAX"
    # else:
    #     raise ValueError
    # dst_swap_data = generate_dst_swap_data(dst_net, func_name, int(99 * 1e6), zero_address())
    # # # call
    # change_network(src_net)
    # so_diamond = SoDiamond[-1]
    # proxy_stargate = Contract.from_abi("StargateFacet", so_diamond.address, StargateFacet.abi)
    # proxy_stargate.soSwapViaStargate(
    #     so_data,
    #     src_swap_data,
    #     stargate_data,
    #     dst_swap_data,
    #     {'from': account, 'value': int(src_fee + from_amount)}
    # )


def main():
    swap("rinkeby", "avax-test")
