import functools

from brownie import Contract

from scripts.struct import change_network, omniswap_ethereum_project, padding_to_bytes, hex_str_to_vector_u8
import sui_brownie


@functools.lru_cache()
def get_serde_facet(
        project: sui_brownie.SuiProject,
        net: str):
    change_network(net)
    contract_name = "SerdeFacet"
    return Contract.from_abi(
        contract_name,
        project.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


@functools.lru_cache()
def get_wormhole_facet(
        project: sui_brownie.SuiProject,
        net: str):
    change_network(net)
    contract_name = "WormholeFacet"
    return Contract.from_abi(
        contract_name,
        project.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


@functools.lru_cache()
def get_token_bridge(
        project: sui_brownie.SuiProject,
        net: str):
    change_network(net)
    contract_name = "TokenBridge"
    return Contract.from_abi(
        contract_name,
        project.config["networks"][net]["wormhole"]["token_bridge"],
        omniswap_ethereum_project.interface.IWormholeBridge.abi
    )


@functools.lru_cache()
def get_wormhole(
        project: sui_brownie.SuiProject,
        net: str):
    change_network(net)
    contract_name = "Wormhole"
    return Contract.from_abi(
        contract_name,
        project.config["networks"][net]["wormhole"]["wormhole"],
        omniswap_ethereum_project.interface.IWormhole.abi
    )


@functools.lru_cache()
def get_price_ratio(
        package: sui_brownie.SuiPackage,
        dst_chain_id: int
):
    # todo! fix
    return 1


def parse_vaa(
        project: sui_brownie.SuiProject,
        net: str,
        vaa: str
):
    """
    Decode vaa
    :param project:
    :param net:
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
    return get_wormhole(project, net).parseVM(vaa)


def parse_transfer_with_payload(
        project: sui_brownie.SuiProject,
        net: str,
        vaa_payload: str
):
    """

    :param project:
    :param net:
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
    return get_token_bridge(project, net).parseTransferWithPayload(vaa_payload)


def parse_transfer(
        project: sui_brownie.SuiProject,
        net: str,
        vaa_payload: str
):
    """

    :param project:
    :param net:
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
    return get_token_bridge(project, net).parseTransfer(vaa_payload)


def parse_wormhole_payload(
        project: sui_brownie.SuiProject,
        net: str,
        transfer_payload: str
):
    """

    :param project:
    :param net:
    :param transfer_payload:
    :return:
        {
            dstMaxGasPrice,
            dstMaxGas,
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
    return get_wormhole_facet(project, net).decodeWormholePayload(transfer_payload)


def parse_vaa_to_wormhole_payload(
        project: sui_brownie.SuiProject,
        net: str,
        vaa: str
):
    vaa_data = parse_vaa(project, net, vaa)
    transfer_data = parse_transfer_with_payload(project, net, vaa_data[-4])
    wormhole_data = parse_wormhole_payload(project, net, transfer_data[-1])
    return vaa_data, transfer_data, wormhole_data