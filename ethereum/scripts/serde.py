import functools
from pathlib import Path

from brownie import Contract, network, config, project

omniswap_ethereum_path = Path(__file__).parent.parent
omniswap_ethereum_project = project.load(
    str(omniswap_ethereum_path), raise_if_loaded=False
)


@functools.lru_cache()
def get_serde_facet():
    contract_name = "SerdeFacet"
    return Contract.from_abi(
        contract_name,
        config["networks"][network.show_active()]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi,
    )


@functools.lru_cache()
def get_wormhole_facet():
    contract_name = "WormholeFacet"
    net = network.show_active()
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi,
    )


def get_cctp_facet():
    contract_name = "CCTPFacet"
    net = network.show_active()
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi,
    )


@functools.lru_cache()
def get_stargate_facet():
    contract_name = "StargateFacet"
    net = network.show_active()
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi,
    )


@functools.lru_cache()
def get_stargate_helper_facet():
    contract_name = "StargateHelper"
    net = network.show_active()
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["StargateHelper"],
        omniswap_ethereum_project[contract_name].abi,
    )


@functools.lru_cache()
def get_token_bridge():
    contract_name = "TokenBridge"
    net = network.show_active()
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["wormhole"]["token_bridge"],
        omniswap_ethereum_project.interface.IWormholeBridge.abi,
    )


@functools.lru_cache()
def get_wormhole():
    net = network.show_active()
    contract_name = "Wormhole"
    return Contract.from_abi(
        contract_name,
        config["networks"][net]["wormhole"]["wormhole"],
        omniswap_ethereum_project.interface.IWormhole.abi,
    )


def parse_vaa(vaa: str):
    """
    Decode vaa
    :param vaa:
    :return:
        {
            version: result[0],
            timestamp: result[1],
            nonce: result[2],
            emitterChainId: result[3],
            emitterAddress: result[4],
            sequence: result[5].toString(),
            consistencyLevel: result[6],
            payload: result[7],
            guardianSetIndex: result[8],
            signatures: result[9],
            hash: result[10]
        }
    """
    if not str(vaa).startswith("0x"):
        vaa = "0x" + vaa
    return get_wormhole().parseVM(vaa)


def parse_transfer_with_payload(vaa_payload: str):
    """

    :param vaa_payload:
    :return:
        {
            payloadID: result[0],
            amount: result[1],
            tokenAddress: result[2],
            tokenChain: result[3],
            to: result[4],
            toChain: result[5],
            fromAddress: result[6],
            payload: result[7]
          }
    """
    if not str(vaa_payload).startswith("0x"):
        vaa_payload = "0x" + vaa_payload
    return get_token_bridge().parseTransferWithPayload(vaa_payload)


def parse_transfer(vaa_payload: str):
    """

    :param vaa_payload:
    :return:
        {
            payloadID: result[0],
            amount: result[1],
            tokenAddress: result[2],
            tokenChain: result[3],
            to: result[4],
            toChain: result[5],
            fee: result[6]
          }
    """
    if not str(vaa_payload).startswith("0x"):
        vaa_payload = "0x" + vaa_payload
    return get_token_bridge().parseTransfer(vaa_payload)


def parse_wormhole_payload(transfer_payload: str):
    """

    :param transfer_payload:
    :return:
        {
            dstMaxGas,
            dstMaxGasPrice,
            soData,
            dstSwapData
        }
        {
            transactionId: result[2][0],
            receiver: result[2][1],
            sourceChainId: result[2][2],
            sendingAssetId: result[2][3],
            destinationChainId: result[2][4],
            receivingAssetId: result[2][5],
            amount: result[2][6]
          }
        [{
            callTo: result[3][i][0],
            approveTo: result[3][i][1],
            sendingAssetId: result[3][i][2],
            receivingAssetId: result[3][i][3],
            fromAmount: result[3][i][4],
            callData: result[3][i][5]
          }]
    """
    if not str(transfer_payload).startswith("0x"):
        transfer_payload = "0x" + transfer_payload
    return get_wormhole_facet().decodeWormholePayload(transfer_payload)


def parse_vaa_to_wormhole_payload(vaa: str):
    vaa_data = parse_vaa(vaa)
    transfer_data = parse_transfer_with_payload(vaa_data[-4])
    wormhole_data = parse_wormhole_payload(transfer_data[-1])
    return vaa_data, transfer_data, wormhole_data
