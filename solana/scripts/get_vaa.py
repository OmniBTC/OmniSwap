import requests
import base64
from parse import parseTransferWithPayloadVaa


def get_sui_signed_vaa(sequence: str):
    base_url = "https://wormhole-v2-testnet-api.certus.one/v1/signed_vaa/21/40440411a170b4842ae7dee4f4a7b7a58bc0a98566e998850a7bb87bf5dc05b9/"

    response = requests.get(base_url + sequence)
    if "vaaBytes" not in response.json():
        raise ValueError(f"Get sui-testnet signed vaa failed: {response.text}")

    vaa_bytes = response.json()["vaaBytes"]
    vaa = base64.b64decode(vaa_bytes).hex()

    return vaa


def get_solana_signed_vaa(sequence: str):
    base_url = "https://wormhole-v2-testnet-api.certus.one/v1/signed_vaa/1/3b26409f8aaded3f5ddca184695aa6a0fa829b0c85caf84856324896d214ca98/"

    response = requests.get(base_url + sequence)
    if "vaaBytes" not in response.json():
        raise ValueError(f"Get sui-testnet signed vaa failed: {response.text}")

    vaa_bytes = response.json()["vaaBytes"]
    vaa = base64.b64decode(vaa_bytes).hex()

    return vaa


def get_bsc_signed_vaa(sequence: str):
    base_url = "https://wormhole-v2-testnet-api.certus.one/v1/signed_vaa/4/0000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a09/"

    response = requests.get(base_url + sequence)
    if "vaaBytes" not in response.json():
        raise ValueError(f"Get sui-testnet signed vaa failed: {response.text}")

    vaa_bytes = response.json()["vaaBytes"]
    vaa = base64.b64decode(vaa_bytes).hex()

    return vaa


if __name__ == "__main__":
    # print(get_sui_signed_vaa("126"))
    vaa = get_solana_signed_vaa("25717")
    # vaa = get_bsc_signed_vaa("5115")

    p1, p2, p3 = parseTransferWithPayloadVaa(vaa)
    print(p1, p2, p3)
    print(f"vaa: {vaa}")
