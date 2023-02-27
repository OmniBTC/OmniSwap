import copy

import pytest
from scripts.helpful_scripts import get_account, to_hex_str
from brownie import WormholeFacet
from scripts.swap import SoData, SwapData


@pytest.fixture
def wormholeFacet():
    account = get_account()
    return account.deploy(WormholeFacet)


def get_aptos_bytes(data: bytes) -> str:
    return f"0x{data.hex()}"


def test_serde_wormhole_data(wormholeFacet):
    normalized_data = [1, 10000, 2389, "0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"]
    data = wormholeFacet.encodeNormalizedWormholeData(normalized_data)
    assert (
        data
        == "0x00010000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000095500000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af"
    )
    data = wormholeFacet.decodeNormalizedWormholeData(data)
    assert data == normalized_data


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


def test_serde_wormhole_payload(wormholeFacet):
    # dstMaxGasPrice, dstMaxGas
    dstMaxGasPrice = 10000
    dstMaxGas = 59

    so_data = SoData(
        transactionId="0x4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        sourceChainId=1,
        sendingAssetId=to_hex_str("0x1::aptos_coin::AptosCoin"),
        destinationChainId=2,
        receivingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        amount=100000000,
    )
    so_data_padding = padding_so_data(so_data)
    print(so_data_padding)
    so_data = so_data.format_to_contract()

    swap_data = [
        SwapData(
            callTo="0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81",
            approveTo="0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81",
            sendingAssetId=to_hex_str("0x1::aptos_coin::AptosCoin"),
            receivingAssetId=to_hex_str("0x1::omni_bridge::XBTC"),
            fromAmount=8900000000,
            callData=to_hex_str(
                "0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81::curves::Uncorrelated"
            ),
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
    data = wormholeFacet.encodeWormholePayload(dstMaxGasPrice, dstMaxGas, so_data, [])
    assert (
        data
        == "0x022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c1719"
    )
    data = wormholeFacet.decodeWormholePayload(data)
    assert data == [dstMaxGasPrice, dstMaxGas, so_data_padding, []]

    # With swap
    data = wormholeFacet.encodeWormholePayload(
        dstMaxGasPrice, dstMaxGas, so_data, swap_data
    )
    assert (
        data
        == "0x022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c17190102204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c811a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e163078313a3a6f6d6e695f6272696467653a3a5842544300583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c6174656414957eb0316f02ba4a9de3d308742eefd44a3c1719142514895c72f50d8bd4b4f9b1110f0d6bd2c9752614143db3ceefbdfe5631add3e50f7614b6ba708ba700146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7"
    )
    data = wormholeFacet.decodeWormholePayload(data)
    assert data == [dstMaxGasPrice, dstMaxGas, so_data_padding, swap_data_padding]
