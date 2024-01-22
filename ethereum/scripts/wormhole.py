import os

from brownie import Contract
from brownie.project.main import Project
from scripts.helpful_scripts import (
    Session,
    get_account,
    get_account_address,
    get_wormhole_bridge,
    get_wormhole_chainid,
    zero_address,
)
from scripts.swap import SoData

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

ether = 1e18
amount = 0.001 * ether

support_networks = ["avax-main", "bsc-main", "polygon-main", "mainnet"]


def get_contract(contract_name: str, p: Project = None):
    return p[contract_name]


def get_contract_address(contract_name: str, p: Project = None):
    return get_contract(contract_name, p)[-1].address


def get_dst_diamond(p: Project = None):
    return p["SoDiamond"][-1].address


def get_dst_chainid(p: Project = None):
    return get_wormhole_chainid()


def get_receive_native_token_name(net):
    if net == "avax-test":
        return "wbnb"
    elif net == "bsc-test":
        return "wavax"


def get_stable_coin_address(net):
    from brownie import config

    try:
        return ("usdc", config["networks"][net]["token"]["usdc"]["address"])
    except Exception:
        return ("usdt", config["networks"][net]["token"]["usdt"]["address"])


def get_usdc_address(net):
    from brownie import config

    try:
        return config["networks"][net]["token"]["usdc"]["address"]
    except Exception:
        return None


def get_usdt_address(net):
    from brownie import config

    try:
        return config["networks"][net]["token"]["usdt"]["address"]
    except Exception:
        return None


def get_weth_address(net):
    from brownie import config

    try:
        return config["networks"][net]["token"]["weth"]["address"]
    except Exception:
        return zero_address()


def get_net_from_wormhole_chainid(chainid):
    if chainid == 2:
        return "mainnet"
    elif chainid == 4:
        return "bsc-main"
    elif chainid == 5:
        return "polygon-main"
    elif chainid == 6:
        return "avax-main"
    elif chainid == 10:
        return "ftm-main"
    elif chainid == 22:
        return "aptos-mainnet"
    elif chainid == 21:
        return "sui-mainnet"
    elif chainid == 1:
        return "solana-mainnet"
    elif chainid == 30:
        return "base-main"


def get_native_token_name(net):
    if "avax" in net:
        return "AVAX"
    elif "bsc" in net:
        return "BNB"
    elif "ftm" in net:
        return "FTM"
    elif "polygon" in net:
        return "MATIC"
    elif "aptos" in net:
        return "APT"
    elif "sui" in net:
        return "SUI"
    else:
        return "ETH"


def so_swap_via_wormhole(
        so_data: SoData,
        dst_diamond_address: str = "",
        dst_chainid: int = 0,
        p: Project = None,
):
    account = get_account()

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", p["SoDiamond"][-1].address, p["WormholeFacet"].abi
    )
    src_swap = []
    dst_swap = []

    # usdt_address = "0x6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"
    # usdt = Contract.from_abi("IERC20", usdt_address, p.interface.IERC20.abi)
    # usdt.approve(proxy_diamond.address, amount, {"from": account})
    so_data = so_data.format_to_contract()
    dstMaxGasPriceInWeiForRelayer = 25000000000
    wormhole_data = [dst_chainid, dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]
    # value = wormhole_fee + input_eth_amount + relayer_fee
    relayer_fee = proxy_diamond.estimateRelayerFee(so_data, wormhole_data, dst_swap)
    print(f"relayer fee:{relayer_fee}")
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee + amount
    wormhole_data[2] = msg_value

    proxy_diamond.soSwapViaWormhole(
        so_data,
        src_swap,
        wormhole_data,
        dst_swap,
        {"from": account, "value": msg_value},
    )


def test_get_weth():
    from brownie import interface

    token_bridge = Contract.from_abi(
        "IWormholeBridge", get_wormhole_bridge(), interface.IWormholeBridge.abi
    )
    # wrapped_address = token_bridge.wrappedAsset(
    #     6, "0xF49E250aEB5abDf660d643583AdFd0be41464EfD")

    print(token_bridge.WETH())


def get_all_warpped_token():
    from brownie import interface, config, network

    token_bridge = Contract.from_abi(
        "IWormholeBridge", get_wormhole_bridge(), interface.IWormholeBridge.abi
    )

    current_net = network.show_active()

    src_wormhole_chain_id = get_wormhole_chainid()
    chain_path = []
    for net in support_networks:
        if net == current_net:
            continue
        print(f"{net} --> {current_net}")

        wormhole_chain_id = config["networks"][net]["wormhole"]["chainid"]
        weth = get_weth_address(net)
        usdc_address = get_usdc_address(net)
        usdt_address = get_usdt_address(net)
        wrapped_eth = token_bridge.wrappedAsset(wormhole_chain_id, weth)

        chain_path.append(
            {
                "SrcWormholeChainId": src_wormhole_chain_id,
                "SrcTokenAddress": wrapped_eth,
                "DstWormholeChainId": wormhole_chain_id,
                "DstTokenAddress": zero_address(),
            }
        )

        if usdc_address != None:
            wrapped_usdc_token = token_bridge.wrappedAsset(
                wormhole_chain_id, usdc_address
            )
            if wrapped_usdc_token != zero_address():
                chain_path.append(
                    {
                        "SrcWormholeChainId": src_wormhole_chain_id,
                        "SrcTokenAddress": wrapped_usdc_token,
                        "DstWormholeChainId": wormhole_chain_id,
                        "DstTokenAddress": usdc_address,
                    }
                )
                print(
                    f"{net}: usdc [{usdc_address}] -> {current_net}: usdc [{wrapped_usdc_token}]"
                )

        if usdt_address != None:
            wrapped_usdt_token = token_bridge.wrappedAsset(
                wormhole_chain_id, usdt_address
            )
            if wrapped_usdt_token != zero_address():
                chain_path.append(
                    {
                        "SrcWormholeChainId": src_wormhole_chain_id,
                        "SrcTokenAddress": wrapped_usdt_token,
                        "DstWormholeChainId": wormhole_chain_id,
                        "DstTokenAddress": usdt_address,
                    }
                )
                print(
                    f"{net}: usdt [{usdt_address}] -> {current_net}: usdt [{wrapped_usdt_token}]"
                )

        native_token_name = get_native_token_name(net)

        print(
            f"{net}: {native_token_name} -> {current_net}: W{native_token_name} [{wrapped_eth}]\n"
        )

    return chain_path


def test_complete():
    from brownie import SoDiamond, WormholeFacet

    account = get_account()
    vm = "01000000000100434683cfbd400b0c789553c78b19b7a939f285cf124ba59a76698c131e808d142bf18b547e2129b8225d0fc1bc4976a02a0bedc16290638a86743a971889bdc501634baeba6241010000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000008660f0100000000000000000000000000000000000000000000000000000004a8270a4052170b4cd48de5ef6e6b789974efaef06deb499a18fa707ac5940be0b5723f170001201fc815cc1acfb02ee4d500e9a74adf832cbe096b6d5e3bc16059280ae67492000100000000000000000000000000000000000000000000000000000000000f4240"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )
    proxy_diamond.completeSoSwap(vm, {"from": account})


def test_parse_payload():
    from brownie import SoDiamond, WormholeFacet

    encoded_payload = "00000000000000000000000000000000000000000000000000000005d21dba0000000000000000000000000000000000000000000000000000000000000091c800000000000000a00000000000000020260bb0b6554d65a8c25cc019e836d42ae7b634499498a6424ad53da4c7edd4c30000000000000014b6b12ada59a8ac44ded72e03693dd14614224349a869000000000000001410f1053bf2884b28ee0bd7a2ddba237af3511d29006100000000000000140000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002386f26fc100000000000000000000"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi
    )

    # receipt = proxy_diamond.parseMaxGasPrice(encoded_payload)
    # print(f'MaxGasPrice: {receipt}')
    # receipt = proxy_diamond.parseSoData(encoded_payload)
    # print(f'Sodata: {receipt}')
    receipt = proxy_diamond.decodeWormholePayload(encoded_payload)
    print(f"decode data: {receipt}")


def test_get_price_ratio():
    from brownie import LibSoFeeWormholeV1

    (ratio, ok) = LibSoFeeWormholeV1[-1].getPriceRatio(5)
    print(f"ratio: {ratio}, ok: {ok}")


def main(src_net="avax-main", dst_net="polygon-main"):
    global src_session
    global dst_session
    src_session = Session(
        net=src_net, project_path=root_path, name=src_net, daemon=False
    )
    dst_session = Session(
        net=dst_net, project_path=root_path, name=dst_net, daemon=False
    )

    dst_diamond_address = dst_session.put_task(get_dst_diamond, with_project=True)

    dst_chainid = dst_session.put_task(get_dst_chainid, with_project=True)

    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=amount,
        sendingTokenName="eth",
        receiveTokenName="WAVAX",
    )

    src_session.put_task(
        so_swap_via_wormhole,
        args=(so_data, dst_diamond_address, dst_chainid),
        with_project=True,
    )

    src_session.terminate()
    dst_session.terminate()
