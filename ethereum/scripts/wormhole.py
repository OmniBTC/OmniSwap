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


def so_swap_via_wormhole(so_data, dst_diamond_address: str = "", dst_chainid: int = 0, p: Project = None):
    account = get_account()

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", p["SoDiamond"][-1].address, p["WormholeFacet"].abi)
    src_swap = []
    dst_swap = []

    usdt_address = "0xF49E250aEB5abDf660d643583AdFd0be41464EfD"
    usdt = Contract.from_abi("IERC20", usdt_address, p.interface.IERC20.abi)
    usdt.approve(proxy_diamond.address, amount, {"from": account})

    so_data = so_data.format_to_contract()
    # test calculated fee
    dstMaxGasForRelayer = 0
    dstMaxGasPriceInWeiForRelayer = 25000000000
    wormhole_data = [dst_chainid, dstMaxGasForRelayer,
                     dstMaxGasPriceInWeiForRelayer, dst_diamond_address]
    # value = wormhole_fee + input_eth_amount + relayer_fee
    relayer_fee = proxy_diamond.estimateRelayerFee(wormhole_data)
    wormhole_fee = proxy_diamond.getWormholeMessageFee()
    msg_value = wormhole_fee + relayer_fee
    proxy_diamond.soSwapViaWormhole(
        so_data, src_swap, wormhole_data, dst_swap, {'from': account, 'value': msg_value})


def test_complete():
    from brownie import SoDiamond, WormholeFacet
    account = get_account()
    vm = "01000000000100a5cc8af10a0aa7934b706284df95a561c6a8f794ddcbea3ffe3de9d6d42e8590780fa0d0aacf30099a8729830814bbc5e80d4134aa37353c844355bab8fc01c6016344e3990000000c00040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000007cf0f0300000000000000000000000000000000000000000000000000000000000185d7000000000000000000000000f49e250aeb5abdf660d643583adfd0be41464efd000400000000000000000000000085211a005319d407ec6479b29e183e901ffc0155000600000000000000000000000010d2b31d8058bc02a51950b60f72335ebfb07cf300000000000000000000000000000000000000000000000000000005d21dba0081a03417616e3052793e54269d21904e6ce17d4389286d23d30393a4c5b049a0b6b12ada59a8ac44ded72e03693dd14614224349000000000000000000000000000000000000000000000000000000000000006171b7e25be7879e042e55fbabd4037de116ae07e0000000000000000000000000000000000000000000000000000000000000a8698337e5ef98af25012e1b39cd996772143f6c5fdf00000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000000016d481b9f59b22b6eb097b986fc06e438d585c0396d481b9f59b22b6eb097b986fc06e438d585c0398337e5ef98af25012e1b39cd996772143f6c5fdf4a0d1092e9df255cf95d72834ea925513278231800000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000085211a005319d407ec6479b29e183e901ffc0155000000000000000000000000000000000000000000000000000000006344ef4300000000000000000000000000000000000000000000000000000000000000020000000000000000000000008337e5ef98af25012e1b39cd996772143f6c5fdf0000000000000000000000004a0d1092e9df255cf95d72834ea9255132782318"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)
    proxy_diamond.completeSoSwap(vm, {'from': account})


def test_get_gas():
    from brownie import SoDiamond, WormholeFacet
    vm = "01000000000100a5cc8af10a0aa7934b706284df95a561c6a8f794ddcbea3ffe3de9d6d42e8590780fa0d0aacf30099a8729830814bbc5e80d4134aa37353c844355bab8fc01c6016344e3990000000c00040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000007cf0f0300000000000000000000000000000000000000000000000000000000000185d7000000000000000000000000f49e250aeb5abdf660d643583adfd0be41464efd000400000000000000000000000085211a005319d407ec6479b29e183e901ffc0155000600000000000000000000000010d2b31d8058bc02a51950b60f72335ebfb07cf300000000000000000000000000000000000000000000000000000005d21dba0081a03417616e3052793e54269d21904e6ce17d4389286d23d30393a4c5b049a0b6b12ada59a8ac44ded72e03693dd14614224349000000000000000000000000000000000000000000000000000000000000006171b7e25be7879e042e55fbabd4037de116ae07e0000000000000000000000000000000000000000000000000000000000000a8698337e5ef98af25012e1b39cd996772143f6c5fdf00000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000000016d481b9f59b22b6eb097b986fc06e438d585c0396d481b9f59b22b6eb097b986fc06e438d585c0398337e5ef98af25012e1b39cd996772143f6c5fdf4a0d1092e9df255cf95d72834ea925513278231800000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000010438ed173900000000000000000000000000000000000000000000000000000000000003e8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000085211a005319d407ec6479b29e183e901ffc0155000000000000000000000000000000000000000000000000000000006344ef4300000000000000000000000000000000000000000000000000000000000000020000000000000000000000008337e5ef98af25012e1b39cd996772143f6c5fdf0000000000000000000000004a0d1092e9df255cf95d72834ea9255132782318"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)

    receipt = proxy_diamond.getMaxGasAndPrice(vm)
    print(f'{receipt}')


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
        sendingTokenName="usdt",
        receiveTokenName="wusdt")

    src_session.put_task(so_swap_via_wormhole, args=(
        so_data, dst_diamond_address, dst_chainid),  with_project=True)

    src_session.terminate()
    dst_session.terminate()
