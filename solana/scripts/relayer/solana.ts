import {ParsedTokenTransferVaa, parseTokenTransferVaa, postVaaSolana} from "@certusone/wormhole-sdk";
import {Connection, Keypair} from "@solana/web3.js";
import path from "path";
import fs from "fs";
import axios from "axios";

const NET = "DEVNET";
let SOLANA_EMITTER_CHAIN: number;
let SOLANA_WORMHOLE_ADDRESS: string;
let SOLANA_TOKEN_BRIDGE_ADDRESS: string;
let WORMHOLE_URL: string[];
let NET_TO_WORMHOLE_CHAIN_ID;
let NET_TO_EMITTER;
let PENDING_URL;

// @ts-ignore
if (NET !== "MAINNET") {
    WORMHOLE_URL = [
        "https://wormhole-v2-testnet-api.certus.one"
    ];
    NET_TO_WORMHOLE_CHAIN_ID = {
        "goerli": 2,
        "bsc-test": 4,
        "polygon-test": 5,
        "avax-test": 6,
        "optimism-test": 24,
        "arbitrum-test": 23,
        "aptos-testnet": 22,
        "sui-testnet": 21,
    }
    NET_TO_EMITTER = {
        "mainnet": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
        "bsc-main": "0xB6F6D86a8f9879A9c87f643768d9efc38c1Da6E7",
        "polygon-main": "0x5a58505a96D1dbf8dF91cB21B54419FC36e93fdE",
        "avax-main": "0x0e082F06FF657D94310cB8cE8B0D9a04541d8052",
        "optimism-main": "0x1D68124e65faFC907325e3EDbF8c4d84499DAa8b",
        "arbitrum-main": "0x0b2402144Bb366A632D14B83F244D2e0e21bD39c",
        "aptos-mainnet": "0000000000000000000000000000000000000000000000000000000000000001",
        "sui-mainnet": "0xccceeb29348f71bdd22ffef43a2a19c1f5b5e17c5cca5411529120182672ade5",
        "base-main": "0x8d2de8d2f73F1F4cAB472AC9A881C9b123C79627",
    }
    SOLANA_WORMHOLE_ADDRESS = "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5";
    SOLANA_TOKEN_BRIDGE_ADDRESS = "DZnkkTmCiFWfYTfT41X3Rd1kDgozqzxWaHqsw6W4x2oe";
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
} else {
    WORMHOLE_URL = [
        "https://wormhole-v2-mainnet-api.certus.one",
        "https://wormhole-v2-mainnet-api.mcf.rocks",
        "https://wormhole-v2-mainnet-api.chainlayer.network",
        "https://wormhole-v2-mainnet-api.staking.fund",
    ];
    NET_TO_WORMHOLE_CHAIN_ID = {
        "mainnet": 2,
        "bsc-main": 4,
        "polygon-main": 5,
        "avax-main": 6,
        "optimism-main": 24,
        "arbitrum-main": 23,
        "aptos-mainnet": 22,
        "sui-mainnet": 21,
        "base-main": 30,
    }
    NET_TO_EMITTER = {
        "mainnet": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
        "bsc-main": "0xB6F6D86a8f9879A9c87f643768d9efc38c1Da6E7",
        "polygon-main": "0x5a58505a96D1dbf8dF91cB21B54419FC36e93fdE",
        "avax-main": "0x0e082F06FF657D94310cB8cE8B0D9a04541d8052",
        "optimism-main": "0x1D68124e65faFC907325e3EDbF8c4d84499DAa8b",
        "arbitrum-main": "0x0b2402144Bb366A632D14B83F244D2e0e21bD39c",
        "aptos-mainnet": "0000000000000000000000000000000000000000000000000000000000000001",
        "sui-mainnet": "0xccceeb29348f71bdd22ffef43a2a19c1f5b5e17c5cca5411529120182672ade5",
        "base-main": "0x8d2de8d2f73F1F4cAB472AC9A881C9b123C79627",
    }
    SOLANA_WORMHOLE_ADDRESS = "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth";
    SOLANA_TOKEN_BRIDGE_ADDRESS = "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb";
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
}

function getRandomWormholeUrl() {
    const randomIndex: number = Math.floor(Math.random() * WORMHOLE_URL.length);
    return WORMHOLE_URL[randomIndex]
}

function remove0x(addr) {
    if (addr.startsWith("0x")) {
        addr = addr.substring(2);
    }
    return addr
}

function formatEmitterAddress(addr) {
    addr = remove0x(addr);
    while (addr.length < 62) {
        addr = "0" + addr;
    }
    return addr
}


async function getSignedVaaByWormhole(
    sequence,
    emitter_chain_id
): Promise<Buffer> {
    const wormhole_url = getRandomWormholeUrl()
    const src_net = NET_TO_WORMHOLE_CHAIN_ID[emitter_chain_id]
    const emitter = NET_TO_EMITTER[src_net]
    const emitter_address = formatEmitterAddress(emitter)

    const url = `${wormhole_url}/v1/signed_vaa/${emitter_chain_id}/${emitter_address}/${sequence}`
    try {
        const response = await axios.get(url);
        let data = response.data;
        if (!('vaaBytes' in data)) {
            return null
        }
        const decodedData: string = atob(data["vaaBytes"])

        let hexString: string = "";
        for (let i = 0; i < decodedData.length; i++) {
            const hex = decodedData.charCodeAt(i).toString(16);
            hexString += (hex.length === 1 ? "0" : "") + hex;
        }
        return Buffer.from(hexString, "hex")
    } catch (error) {
        return null
    }
}

async function getPendingData(dstWormholeChainId) {
    /*
    Get data for pending relayer
    [{'chainName': 'bsc-test',
    'extrinsicHash': '0x63942108e3e0b4ca70ba331acc1c7419ffc43ebcc10e75abe4b0c05a4ce2e2d5',
    'srcWormholeChainId': 0,
    'dstWormholeChainId': 0,
    'sequence': 2110, '
    blockTimestamp': 0}]
    */

    try {
        const response = await axios.get(PENDING_URL);
        let data = response.data;
        data.sort((x0, x1) => x0["sequence"] - x1["sequence"]);
        data = data.filter((x) => x["dstWormholeChainId"].toString() == dstWormholeChainId.toString())
        return data;
    } catch (error) {
        return [];
    }

}

export interface WormholeData {
    dstMaxGasPrice: bigint;
}

export interface ParsedPayload extends ParsedTokenTransferVaa, WormholeData {
}


function parseVaaToWormholePayload(vaa: Buffer): ParsedPayload {
    const token_transfer = parseTokenTransferVaa(vaa);
    const dstMaxGasPrice = {dstMaxGasPrice: token_transfer.tokenTransferPayload.readBigUInt64BE(0)};
    return {
        ...dstMaxGasPrice,
        ...token_transfer,
    }
}

function logWithTimestamp(message: string): void {
    const currentDatetime: string = new Date().toLocaleString();
    const logMessage: string = `[${currentDatetime}] ${message}`;
    console.log(logMessage);
}

async function process_vaa(
    dstSoDiamond,
    vaa: Buffer,
    emitterChainId,
    sequence,
    extrinsicHash,
): Promise<boolean> {
    const payload = parseVaaToWormholePayload(vaa);
    if (payload.dstMaxGasPrice !== 10000000n) {
        logWithTimestamp(`Parse signed vaa for emitterChainId:${emitterChainId} sequence:${sequence} 
        dstMaxGasPrice != ${payload.dstMaxGasPrice}`)
        return false;
    }
    if (!vaa.toString("hex").includes(dstSoDiamond)) {
        logWithTimestamp(`Parse signed vaa for 
        emitterChainId:${emitterChainId} sequence:${sequence} not found ${dstSoDiamond}`)
        return false;
    }


}


async function main() {
    const connection = new Connection(
        "https://sparkling-wild-hexagon.solana-devnet.discover.quiknode.pro/2129a56170ae922c0d50ec36a09a6f683ab5a466/",
        "processed"
    );

    const defaultPath = path.join(process.env.HOME, ".config/solana/id.json");
    const rawKey = JSON.parse(fs.readFileSync(defaultPath, "utf-8"));
    const wallet = Keypair.fromSecretKey(Uint8Array.from(rawKey));

    const payerAddress = wallet.publicKey.toString();
    const SOL_BRIDGE_ADDRESS = "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5";
    const signedVAA =
        "01000000000100cafc1955b08730243327375cd826063f375968dc9f85ccde3a820d47621d12397314aea6c90095c25b795fc58e00f2879248519b1a0bdb79760609b9781b58cb016513f84100000000001540440411a170b4842ae7dee4f4a7b7a58bc0a98566e998850a7bb87bf5dc05b9000000000000007c000300000000000000000000000000000000000000000000000000000002540be400bda28aeb93874baba2273db9c92fb7b7fe2f412352e9633c0258978a32620a230015ceda17841d79db34bd17721d2024343b5d9dd0320626958e10f4cf3d800a719e000135fbfedfe4ba06b311b86ae1d2064e08e583e6d550524307fc626648c4718c0c0138e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938";

    await postVaaSolana(
        connection,
        async (transaction) => {
            transaction.partialSign(wallet);
            return transaction;
        },
        SOL_BRIDGE_ADDRESS,
        payerAddress,
        Buffer.from(signedVAA, "hex")
    );

    console.log("payer: ", payerAddress);
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
