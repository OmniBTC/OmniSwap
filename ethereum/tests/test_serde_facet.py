import pytest
from scripts.helpful_scripts import get_account, to_hex_str, zero_address
from brownie import SerdeFacet
from scripts.swap import SoData, SwapData


@pytest.fixture
def serdeFacet():
    account = get_account()
    return account.deploy(SerdeFacet)


def get_aptos_bytes(data: bytes) -> str:
    return f"0x{data.hex()}"


def test_serde_so_data(serdeFacet):
    so_data = SoData(
        transactionId="0x4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
        receiver="0x2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
        sourceChainId=1,
        sendingAssetId=to_hex_str("0x1::aptos_coin::AptosCoin"),
        destinationChainId=2,
        receivingAssetId="0x957Eb0316f02ba4a9De3D308742eefd44a3c1719",
        amount=100000000,
    )
    normalized_data = so_data.format_to_contract()
    data = serdeFacet.encodeNormalizedSoData(normalized_data)
    assert (
        data
        == "0x00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100"
    )
    data = serdeFacet.decodeNormalizedSoData(data)
    assert data == normalized_data

    compare_data = so_data
    compare_data.sendingAssetId = zero_address()
    data = serdeFacet.denormalizeSoData(normalized_data)
    assert compare_data.format_to_contract() == data
    data = serdeFacet.normalizeSoData(data)
    assert compare_data.format_to_contract() == data


def test_serde_swap_data(serdeFacet):
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
    normalized_data = [d.format_to_contract() for d in swap_data]
    data = serdeFacet.encodeNormalizedSwapData(normalized_data)
    assert (
        data
        == "0x000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7"
    )
    data = serdeFacet.decodeNormalizedSwapData(data)
    assert data == normalized_data

    swap_data = [
        SwapData(
            callTo="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            approveTo="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            sendingAssetId="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            receivingAssetId="0x143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            fromAmount=8900000000,
            callData=to_hex_str(
                "0x4e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81::curves::Uncorrelated"
            ),
        )
    ]
    normalized_data = [d.format_to_contract() for d in swap_data]

    data = serdeFacet.denormalizeSwapData(normalized_data)
    assert normalized_data == data
    data = serdeFacet.normalizeSwapData(data)
    assert normalized_data == data
