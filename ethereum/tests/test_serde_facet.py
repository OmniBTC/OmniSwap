# @Time    : 2022/10/11 18:08
# @Author  : WeiDai
# @FileName: test_serde_facet.py
import pytest
from scripts.helpful_scripts import get_account
from brownie import SerdeFacet
from scripts.swap import SoData, SwapData


@pytest.fixture
def serdeFacet():
    account = get_account()
    return account.deploy(SerdeFacet)

def get_aptos_asset_id_bytes(data: bytes):
    return str("0x") + str(data.hex())


def test_serde_so_data(serdeFacet):
    so_data = SoData(
        transactionId="0x4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        sourceChainId=1,
        sendingAssetId=get_aptos_asset_id_bytes(b"0x1::aptos_coin::AptosCoin"),
        destinationChainId=2,
        receivingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        amount=100000000
    )
    data = serdeFacet.encodeNormalizedSoData(so_data.format_to_contract())
    assert data == "0x00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100"

def test_serde_swap_data(serdeFacet):
    pass
