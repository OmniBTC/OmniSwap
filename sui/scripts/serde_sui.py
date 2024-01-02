import base64
import csv
import functools
import json

import requests
import sui_brownie
from brownie import Contract

from scripts import sui_project
from scripts.struct_sui import change_network, omniswap_ethereum_project


def parse_u256(data):
    assert len(data) == 32
    output = 0
    for i in range(32):
        output = (output << 8) + int(data[31 - i])
    return output


def parse_u64(data):
    assert len(data) == 8
    output = 0
    for i in range(8):
        output = (output << 8) + int(data[7 - i])
    return output


@functools.lru_cache()
def get_serde_facet(net: str):
    change_network(net)
    contract_name = "SerdeFacet"
    return Contract.from_abi(
        contract_name,
        sui_project.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


@functools.lru_cache()
def get_wormhole_facet(net: str):
    change_network(net)
    contract_name = "WormholeFacet"
    return Contract.from_abi(
        contract_name,
        sui_project.config["networks"][net]["SoDiamond"],
        omniswap_ethereum_project[contract_name].abi
    )


@functools.lru_cache()
def get_token_bridge(net: str):
    change_network(net)
    contract_name = "TokenBridge"
    return Contract.from_abi(
        contract_name,
        sui_project.config["networks"][net]["wormhole"]["token_bridge"],
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
        price_manager,
        dst_chain_id: int
):
    return_value = package.so_fee_wormhole.get_price_ratio.inspect(
        price_manager, dst_chain_id)["results"][0]["returnValues"][0][0]
    return parse_u64(return_value)


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
        _project: sui_brownie.SuiProject,
        net: str,
        vaa_payload: str
):
    """

    :param _project:
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
    return get_token_bridge(net).parseTransferWithPayload(vaa_payload)


def parse_transfer(
        _project: sui_brownie.SuiProject,
        net: str,
        vaa_payload: str
):
    """

    :param _project:
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
    return get_token_bridge(net).parseTransfer(vaa_payload)


def parse_wormhole_payload(
        _project: sui_brownie.SuiProject,
        net: str,
        transfer_payload: str
):
    """

    :param _project:
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
    return get_wormhole_facet(net).decodeWormholePayload(transfer_payload)


def parse_vaa_to_wormhole_payload(
        project: sui_brownie.SuiProject,
        net: str,
        vaa: str
):
    vaa_data = parse_vaa(project, net, vaa)
    transfer_data = parse_transfer_with_payload(project, net, vaa_data[-4])
    wormhole_data = parse_wormhole_payload(project, net, transfer_data[-1])
    return vaa_data, transfer_data, wormhole_data


def get_pending_data(url: str = None) -> list:
    """
    Get data for pending relayer
    :return: list
        [{'chainName': 'bsc-test',
        'extrinsicHash': '0x63942108e3e0b4ca70ba331acc1c7419ffc43ebcc10e75abe4b0c05a4ce2e2d5',
        'srcWormholeChainId': 0,
        'dstWormholeChainId': 0,
        'sequence': 2110, '
        blockTimestamp': 0}]
    """
    if url is None:
        # url = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
        url = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    try:
        response = requests.get(url)
        result = response.json()["record"]
        return result if isinstance(result, list) else []
    except Exception as _e:
        return []


def get_signed_vaa(
        sequence: int,
        src_wormhole_id: int = None,
):
    url = "http://wormhole-vaa.chainx.org"
    if src_wormhole_id is None:
        data = {
            "method": "GetSignedVAA",
            "params": [
                str(sequence),
            ]
        }
    else:
        data = {
            "method": "GetSignedVAA",
            "params": [
                str(sequence),
                src_wormhole_id,
            ]
        }
    headers = {'content-type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response.json()


NET_TO_WORMHOLE_CHAINID = {
    # mainnet
    "mainnet": 2,
    "bsc-main": 4,
    "polygon-main": 5,
    "avax-main": 6,
    "optimism-main": 24,
    "arbitrum-main": 23,
    "aptos-mainnet": 22,
    "sui-mainnet": 21,
    # testnet
    "goerli": 2,
    "bsc-test": 4,
    "polygon-test": 5,
    "avax-test": 6,
    "optimism-test": 24,
    "arbitrum-test": 23,
    "aptos-testnet": 22,
    "sui-testnet": 21,
}

WORMHOLE_CHAINID_TO_NET = {
    chainid: net
    for net, chainid in NET_TO_WORMHOLE_CHAINID.items()
    if ("main" in sui_project.network and "main" in net)
       or ("main" not in sui_project.network and "main" not in net)
}

TOKEN_BRIDGE_EMITTER_ADDRESS = {
    # mainnet
    "mainnet": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
    "bsc-main": "0xB6F6D86a8f9879A9c87f643768d9efc38c1Da6E7",
    "polygon-main": "0x5a58505a96D1dbf8dF91cB21B54419FC36e93fdE",
    "avax-main": "0x0e082F06FF657D94310cB8cE8B0D9a04541d8052",
    "optimism-main": "0x0b2402144Bb366A632D14B83F244D2e0e21bD39c",
    "arbitrum-main": "0x1D68124e65faFC907325e3EDbF8c4d84499DAa8b",
    "aptos-mainnet": "0x0000000000000000000000000000000000000000000000000000000000000001",
    "sui-mainnet": "0xccceeb29348f71bdd22ffef43a2a19c1f5b5e17c5cca5411529120182672ade5",
    # testnet
    "goerli": "0xF890982f9310df57d00f659cf4fd87e65adEd8d7",
    "bsc-test": "0x9dcF9D205C9De35334D646BeE44b2D2859712A09",
    "polygon-test": "0x377D55a7928c046E18eEbb61977e714d2a76472a",
    "avax-test": "0x61E44E506Ca5659E6c0bba9b678586fA2d729756",
    "optimism-test": "0xC7A204bDBFe983FCD8d8E61D02b475D4073fF97e",
    "arbitrum-test": "0x23908A62110e21C04F3A4e011d24F901F911744A",
    "aptos-testnet": "0x0000000000000000000000000000000000000000000000000000000000000001",
    "sui-testnet": "0xb22cd218bb63da447ac2704c1cc72727df6b5e981ee17a22176fd7b84c114610",
}


def get_wormhole_url(related_net):
    if "main" not in related_net:
        return "https://api.testnet.wormholescan.io"
    else:
        return "https://api.wormholescan.io"


def format_emitter_address(addr):
    addr = addr.replace("0x", "")
    if len(addr) < 64:
        addr = "0" * (64 - len(addr)) + addr
    return addr


def get_signed_vaa_by_wormhole(
        sequence: int,
        src_net: str = None
):
    """
    Get signed vaa
    :param src_net:
    :param sequence:
    :return: dict
        {'vaaBytes': 'AQAAAAEOAGUI...'}
    """
    emitter_address = format_emitter_address(TOKEN_BRIDGE_EMITTER_ADDRESS[src_net])
    emitter_chainid = NET_TO_WORMHOLE_CHAINID[src_net]
    url = f"{get_wormhole_url(src_net)}/v1/signed_vaa/{emitter_chainid}/{emitter_address}/{sequence}"
    response = requests.get(url)
    return response.json()


def process_aptos_pending():
    file_name = 'query_aptos_pending-2024-01-02_93738.csv'
    pending_data = get_pending_data()
    csv_datas = []
    with open(file_name, 'r') as f:
        reader = csv.DictReader(f)
        for record in reader:
            for data in pending_data:
                if record['extrinsic_hash'] == data['extrinsicHash']:
                    src_chain_id = data['srcWormholeChainId']
                    sequence = data['sequence']
                    print(f"src_chain_id: {src_chain_id}, sequence: {sequence}")
                    try:
                        net = WORMHOLE_CHAINID_TO_NET[src_chain_id]
                        vaa_bytes = get_signed_vaa_by_wormhole(sequence, net)[
                            'vaaBytes']
                        vaa = f'0x{base64.b64decode(vaa_bytes).hex()}'
                        result = parse_vaa_to_wormhole_payload(sui_project, 'polygon-main', vaa)
                        transfer_data = result[1]
                        amount = transfer_data[1]
                        if result[2][3]:
                            swap_data = result[2][3][0]
                            receive_asset = bytes(swap_data[2]).decode('utf-8')
                        else:
                            receive_asset = bytes(result[2][2][5]).decode('utf-8')
                        print(f"receive_token: {receive_asset}, amount: {amount}")
                        record['receive_token'] = receive_asset
                        record['amount'] = amount
                    except Exception as e:
                        print(e)
                    csv_datas.append(dict(record))

    new_file_name = f'processed_{file_name}'
    with open(new_file_name, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=csv_datas[0].keys())
        writer.writeheader()
        writer.writerows(csv_datas)


if __name__ == "__main__":
    process_aptos_pending()
    # vaa_bytes = get_signed_vaa_by_wormhole(107260, WORMHOLE_CHAINID_TO_NET[5])[
    #     'vaaBytes']
    # vaa = f'0x{base64.b64decode(vaa_bytes).hex()}'
    # result = parse_vaa_to_wormhole_payload(sui_project, "polygon-main", vaa)
    # swap_data = result[2][3][0]
    # transfer_data = result[1]
    # amount = transfer_data[1]
    # print(swap_data)
    # print(bytes(swap_data[3]))
    # print(bytes(swap_data[5]))
    # print(amount)
