import copy

import pytest
from scripts.helpful_scripts import get_account
from brownie import StargateFacet
from scripts.swap import SoData, SwapData


@pytest.fixture
def stargateFacet():
    account = get_account()
    return account.deploy(StargateFacet)


def padding_so_data(so_data: SoData):
    data = copy.deepcopy(so_data)
    data.sourceChainId = 0
    data.sendingAssetId = ""
    data.destinationChainId = 0
    data.amount = 0
    return data.format_to_contract()


def padding_swap_data(swap_data: SwapData):
    data = copy.deepcopy(swap_data)
    data.approveTo = data.callTo
    data.fromAmount = 0
    return data.format_to_contract()


def test_serde_stargate_payload(stargateFacet):
    so_data = SoData(
        transactionId="0x4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        sourceChainId=1,
        sendingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        destinationChainId=2,
        receivingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        amount=100000000,
    )
    so_data_padding = padding_so_data(so_data)
    print(so_data_padding)
    so_data = so_data.format_to_contract()

    swap_data = [
        SwapData(
            callTo="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            approveTo="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            sendingAssetId="0x2514895c72f50d8bd4b4f9b1110f0d6bd2c97526",
            receivingAssetId="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            fromAmount=8900000000,
            callData="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
        ),
        SwapData(
            callTo="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            approveTo="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            sendingAssetId="0x2514895c72f50d8bd4b4f9b1110f0d6bd2c97526",
            receivingAssetId="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            fromAmount=7700000000,
            callData="0x6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7",
        ),
    ]
    swap_data_padding = [padding_swap_data(d) for d in swap_data]
    swap_data = [d.format_to_contract() for d in swap_data]

    # Not swap
    data = stargateFacet.encodeStargatePayload(so_data, [])
    assert (
        data
        == "0x204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c1719"
    )
    data = stargateFacet.decodeStargatePayload(data)
    assert data == [so_data_padding, []]

    # With swap
    data = stargateFacet.encodeStargatePayload(so_data, swap_data)
    assert (
        data
        == "0x204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c1719010214957eb0316f02ba4a9de3d308742eefd44a3c1719142514895c72f50d8bd4b4f9b1110f0d6bd2c9752614143db3ceefbdfe5631add3e50f7614b6ba708ba70014143db3ceefbdfe5631add3e50f7614b6ba708ba714957eb0316f02ba4a9de3d308742eefd44a3c1719142514895c72f50d8bd4b4f9b1110f0d6bd2c9752614143db3ceefbdfe5631add3e50f7614b6ba708ba700146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7"
    )
    data = stargateFacet.decodeStargatePayload(data)
    assert data == [so_data_padding, swap_data_padding]
