import os
from time import sleep
from brownie import Contract
from brownie.network import gas_price
from scripts.helpful_scripts import Session, get_account, get_account_address, get_wormhole_chainid
from scripts.swap import SoData, src_session, dst_session
from brownie.project.main import Project

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

ether = 1e18
amount = 0.01 * ether


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


def so_swap_via_wormhole(so_data: SoData, dst_diamond_address: str = "", dst_chainid: int = 0, p: Project = None):
    account = get_account()

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", p["SoDiamond"][-1].address, p["WormholeFacet"].abi)
    src_swap = []
    dst_swap = []

    usdt_address = "0x6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"
    usdt = Contract.from_abi("IERC20", usdt_address, p.interface.IERC20.abi)
    usdt.approve(proxy_diamond.address, amount, {"from": account})
    so_data = so_data.format_to_contract()
    dstMaxGasPriceInWeiForRelayer = 25000000000
    wormhole_data = [dst_chainid,
                     dstMaxGasPriceInWeiForRelayer, 0, dst_diamond_address]
    # value = wormhole_fee + input_eth_amount + relayer_fee
    relayer_fee = proxy_diamond.estimateRelayerFee(
        so_data, wormhole_data, dst_swap)
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee
    wormhole_data[2] = msg_value
    proxy_diamond.soSwapViaWormhole(
        so_data, src_swap, wormhole_data, dst_swap, {'from': account, 'value': msg_value})


def test_complete():
    from brownie import SoDiamond, WormholeFacet
    account = get_account()
    vm = "01000000000100a33e0be8e4353d3dca667e6b4102846c46eb72e982847548cd80207cd325d8dd7d60bf401bc6a07bef6e54a45ffeb25eca9761ece516cbb74c324e38b2e92938006347c2ba00000000000600000000000000000000000061e44e506ca5659e6c0bba9b678586fa2d729756000000000000117f010300000000000000000000000000000000000000000000000000000000000f4240000000000000000000000000ae13d989dac2f0debff460ac112a837c89baa7cd000400000000000000000000000010d2b31d8058bc02a51950b60f72335ebfb07cf3000400000000000000000000000085211a005319d407ec6479b29e183e901ffc015500000000000000000000000000000000000000000000000000000005d21dba0000000000000000000000000000000000000000000000000000000000000091c800000000000000a00000000000000020260bb0b6554d65a8c25cc019e836d42ae7b634499498a6424ad53da4c7edd4c30000000000000014b6b12ada59a8ac44ded72e03693dd14614224349a869000000000000001410f1053bf2884b28ee0bd7a2ddba237af3511d29006100000000000000140000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002386f26fc100000000000000000000"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)
    proxy_diamond.completeSoSwap(vm, {'from': account})


def test_parse_payload():
    from brownie import SoDiamond, WormholeFacet
    encoded_payload = "00000000000000000000000000000000000000000000000000000005d21dba0000000000000000000000000000000000000000000000000000000000000091c800000000000000a00000000000000020260bb0b6554d65a8c25cc019e836d42ae7b634499498a6424ad53da4c7edd4c30000000000000014b6b12ada59a8ac44ded72e03693dd14614224349a869000000000000001410f1053bf2884b28ee0bd7a2ddba237af3511d29006100000000000000140000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002386f26fc100000000000000000000"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)

    # receipt = proxy_diamond.parseMaxGasPrice(encoded_payload)
    # print(f'MaxGasPrice: {receipt}')
    # receipt = proxy_diamond.parseSoData(encoded_payload)
    # print(f'Sodata: {receipt}')
    receipt = proxy_diamond.decodeWormholePayload(encoded_payload)
    print(f'decode data: {receipt}')


def test_get_price_ratio():
    from brownie import LibSoFeeWormholeV1
    (ratio, ok) = LibSoFeeWormholeV1[-1].getPriceRatio(5)
    print(f'ratio: {ratio}, ok: {ok}')


def main(src_net="bsc-test", dst_net="avax-test"):
    global src_session
    global dst_session
    src_session = Session(
        net=src_net, project_path=root_path, name=src_net, daemon=False)
    dst_session = Session(
        net=dst_net, project_path=root_path, name=dst_net, daemon=False)

    dst_diamond_address = dst_session.put_task(
        get_dst_diamond, with_project=True)

    dst_chainid = dst_session.put_task(get_dst_chainid, with_project=True)

    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=amount,
        sendingTokenName=get_receive_native_token_name(src_net),
        receiveTokenName="eth")

    src_session.put_task(so_swap_via_wormhole, args=(
        so_data, dst_diamond_address, dst_chainid),  with_project=True)

    src_session.terminate()
    dst_session.terminate()
