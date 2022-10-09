import os
from time import sleep
from brownie import Contract
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


def so_swap_via_wormhole(so_data, dst_diamond_address: str = "", dst_chainid: int = 0, p: Project = None):
    account = get_account()

    proxy_diamond = Contract.from_abi(
        "WormholeFacet", p["SoDiamond"][-1].address, p["WormholeFacet"].abi)
    src_swap = []
    dst_swap = []

    so_data = so_data.format_to_contract()
    # test calculated fee
    dstMaxGasForRelayer = 10000000
    dstMaxGasPriceInWeiForRelayer = 10000000000
    wormhole_data = [dst_chainid, dstMaxGasForRelayer,
                     dstMaxGasPriceInWeiForRelayer, dst_diamond_address]
    proxy_diamond.soSwapViaWormhole(
        so_data, src_swap, wormhole_data, dst_swap, {'from': account, 'value': amount})


def test_complete():
    from brownie import SoDiamond, WormholeFacet
    account = get_account()
    vm = "01000000000100e1e3e2d2712e917c9b71dbe0431c83dd00c82f1748b50053d490626fe107fb841a834360dda5dd99ffa09d22a80a09b987d030d8982919e08fb702725cda2b9201634299040000000100040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09000000000000078f0f0300000000000000000000000000000000000000000000000000000000000f4240000000000000000000000000ae13d989dac2f0debff460ac112a837c89baa7cd00040000000000000000000000005171f34a150773834bdbd62945af0d3c14a7b6fa000600000000000000000000000076cce94ff033c7ed8a39b9c0712dc15be80c9c7300000000000000000000000000000000000000000000000000000002540be40089b489c30c507eaced8051ec908cb7ec7b911945a20da3b82446d6a63255b1b8b6b12ada59a8ac44ded72e03693dd1461422434900000000000000000000000000000000000000000000000000000000000000610000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a86910f1053bf2884b28ee0bd7a2ddba237af3511d29000000000000000000000000000000000000000000000000002386f26fc10000"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)
    proxy_diamond.completeSoSwap(vm, {'from': account})


def test_get_gas():
    from brownie import SoDiamond, WormholeFacet
    account = get_account()
    vm = "01000000000100e1e3e2d2712e917c9b71dbe0431c83dd00c82f1748b50053d490626fe107fb841a834360dda5dd99ffa09d22a80a09b987d030d8982919e08fb702725cda2b9201634299040000000100040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09000000000000078f0f0300000000000000000000000000000000000000000000000000000000000f4240000000000000000000000000ae13d989dac2f0debff460ac112a837c89baa7cd00040000000000000000000000005171f34a150773834bdbd62945af0d3c14a7b6fa000600000000000000000000000076cce94ff033c7ed8a39b9c0712dc15be80c9c7300000000000000000000000000000000000000000000000000000002540be40089b489c30c507eaced8051ec908cb7ec7b911945a20da3b82446d6a63255b1b8b6b12ada59a8ac44ded72e03693dd1461422434900000000000000000000000000000000000000000000000000000000000000610000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a86910f1053bf2884b28ee0bd7a2ddba237af3511d29000000000000000000000000000000000000000000000000002386f26fc10000"
    proxy_diamond = Contract.from_abi(
        "WormholeFacet", SoDiamond[-1].address, WormholeFacet.abi)

    receipt = proxy_diamond.getMaxGasAndPrice(vm)
    print(f'{receipt}')


def test_get_price_ratio():
    from brownie import LibSoFeeWormholeV1
    (ratio, ok) = LibSoFeeWormholeV1[-1].getPriceRatio(5)
    print(f'ratio: {ratio}, ok: {ok}')


def main():
    global src_session
    global dst_session
    dst_session = Session(
        net="avax-test", project_path=root_path, name="avax-test", daemon=False)

    dst_diamond_address = dst_session.put_task(
        get_dst_diamond, with_project=True)

    dst_chainid = dst_session.put_task(get_dst_chainid, with_project=True)

    src_session = Session(
        net="bsc-test", project_path=root_path, name="bsc-test", daemon=False)

    so_data = SoData.create(
        src_session,
        dst_session,
        src_session.put_task(get_account_address),
        amount=amount,
        sendingTokenName="eth",
        receiveTokenName="wbnb")

    src_session.put_task(so_swap_via_wormhole, args=(
        so_data, dst_diamond_address, dst_chainid),  with_project=True)

    src_session.terminate()
    dst_session.terminate()
