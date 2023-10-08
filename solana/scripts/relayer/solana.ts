import {ParsedTokenTransferVaa, parseTokenTransferVaa, postVaaSolana} from "@certusone/wormhole-sdk";
import {
    Connection,
    Keypair,
    PublicKey,
    sendAndConfirmTransaction,
    Transaction,
    TransactionInstruction
} from "@solana/web3.js";
import fs from "fs";
import axios from "axios";
import {
    createRedeemNativeTransferWithPayloadInstruction,
    createRedeemWrappedTransferWithPayloadInstruction
} from "./helper";
import {createObjectCsvWriter} from 'csv-writer';

const NET = "solana-test";
let SOLANA_EMITTER_CHAIN: number;
let CORE_BRIDGE_PID;
let TOKEN_BRIDGE_PID;
let WORMHOLE_URL: string[];
let NET_TO_WORMHOLE_CHAIN_ID;
let NET_TO_EMITTER;
let PENDING_URL;
let OMNISWAP_PID;
let SOLANA_URL;

// @ts-ignore
if (NET !== "solana-mainnet") {
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
        "solana-testnet": 1
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
        "solana-mainnet": "0x2b1246c9eefa3c466792253111f35fec1ee8ee5e9debc412d2e9adadfecdcc72"
    }
    CORE_BRIDGE_PID = new PublicKey("3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5");
    TOKEN_BRIDGE_PID = new PublicKey("DZnkkTmCiFWfYTfT41X3Rd1kDgozqzxWaHqsw6W4x2oe");
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap-pre.coming.chat/v1/getUnSendTransferFromWormhole"
    OMNISWAP_PID = new PublicKey("9YYGvVLZJ9XmKM2A1RNv1Dx3oUnHWgtXWt8V3HU5MtXU");
    SOLANA_URL = "https://sparkling-wild-hexagon.solana-devnet.discover.quiknode.pro/2129a56170ae922c0d50ec36a09a6f683ab5a466/";
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
        "solana-mainnet": 1
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
        "solana-mainnet": "0x0e0a589a41a55fbd66c52a475f2d92a6d3dc9b4747114cb9af825a98b545d3ce"
    }
    CORE_BRIDGE_PID = new PublicKey("worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth");
    TOKEN_BRIDGE_PID = new PublicKey("wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb");
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    OMNISWAP_PID = new PublicKey("9YYGvVLZJ9XmKM2A1RNv1Dx3oUnHWgtXWt8V3HU5MtXU");
    SOLANA_URL = "";
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
    emitterChainId
): Promise<Buffer> {
    const wormholeUrl = getRandomWormholeUrl()
    const srcNet = NET_TO_WORMHOLE_CHAIN_ID[emitterChainId]
    const emitter = NET_TO_EMITTER[srcNet]
    const emitterAddress = formatEmitterAddress(emitter)

    const url = `${wormholeUrl}/v1/signed_vaa/${emitterChainId}/${emitterAddress}/${sequence}`
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
    const tokenTransfer = parseTokenTransferVaa(vaa);
    const dstMaxGasPrice = {dstMaxGasPrice: tokenTransfer.tokenTransferPayload.readBigUInt64BE(0)};
    return {
        ...dstMaxGasPrice,
        ...tokenTransfer,
    }
}

function logWithTimestamp(message: string): void {
    const currentDatetime: string = new Date().toLocaleString();
    const logMessage: string = `[${currentDatetime}] ${message}`;
    console.log(logMessage);
}

const sendAndConfirmIx = async (
    connection: Connection,
    payer: Keypair,
    ix: TransactionInstruction | Promise<TransactionInstruction>
) => {
    const tx = new Transaction().add(await ix);
    return await sendAndConfirmTransaction(connection, tx, [payer]);
}

async function processVaa(
    connection: Connection,
    payer: Keypair,
    dstSoDiamond,
    vaa: Buffer,
    emitterChainId,
    sequence,
    extrinsicHash,
): Promise<boolean> {
    const payload = parseVaaToWormholePayload(vaa);
    const payAddress = payer.publicKey.toString();
    if (payload.dstMaxGasPrice !== BigInt("10000000")) {
        logWithTimestamp(`Parse signed vaa for emitterChainId:${emitterChainId} sequence:${sequence} 
        dstMaxGasPrice != ${payload.dstMaxGasPrice}`)
        return false;
    }
    if (!vaa.toString("hex").includes(dstSoDiamond)) {
        logWithTimestamp(`Parse signed vaa for 
        emitterChainId:${emitterChainId} sequence:${sequence} not found ${dstSoDiamond}`)
        return false;
    }

    try {
        await postVaaSolana(
            connection,
            async (transaction) => {
                transaction.partialSign(payer);
                return transaction;
            },
            CORE_BRIDGE_PID,
            payAddress,
            vaa
        );
    } catch (error) {
    }

    let dstTx;
    try {
        const ix = await createRedeemNativeTransferWithPayloadInstruction(
            connection,
            OMNISWAP_PID,
            payAddress,
            TOKEN_BRIDGE_PID,
            CORE_BRIDGE_PID,
            vaa
        );
        dstTx = await sendAndConfirmIx(connection, payer, ix);

    } catch (error) {
        const ix = await createRedeemWrappedTransferWithPayloadInstruction(
            connection,
            OMNISWAP_PID,
            payAddress,
            TOKEN_BRIDGE_PID,
            CORE_BRIDGE_PID,
            vaa
        );
        dstTx = await sendAndConfirmIx(connection, payer, ix);
    }
    recordGas(extrinsicHash, dstTx);
}

function recordGas(
    srcTx,
    dstTx,
) {
    const data = [
        {srcTx: srcTx, dstTx: dstTx},
    ];
    const fileExists = fs.existsSync('solana.csv');

    const csvWriter = createObjectCsvWriter({
        path: 'solana.csv',
        header: [
            {id: 'srcTx', title: 'srcTx'},
            {id: 'dstTx', title: 'dstTx'},
        ],
        append: fileExists,
        alwaysQuote: true,
    });

    csvWriter.writeRecords(data)
        .then(() => {
        })
        .catch((error) => {
        });
}

async function processV2(
    dstWormholeChainId,
    dstSoDiamond,
) {
    const connection = new Connection(
        SOLANA_URL,
        "processed"
    );
    let payer: Keypair;
    const hasProcess = new Map<any[], number>();
    const pendingInterval = 10;
    let lastPendingTime = 0;
    while (true) {
        const currentTimeStamp: number = Date.now();
        if (currentTimeStamp < lastPendingTime + pendingInterval) {
            continue;
        } else {
            lastPendingTime = currentTimeStamp;
        }
        const pendingData = await getPendingData(dstWormholeChainId);

        for (const d of pendingData) {
            const vaa = await getSignedVaaByWormhole(d["sequence"], d["srcWormholeChainId"])
            if (vaa == null) {
                logWithTimestamp(`Waiting vaa for emitterChainId: ${d["srcWormholeChainId"]}, 
                sequence:${d["sequence"]}`);
                continue;
            }
            const hasKey = [d["sequence"], d["srcWormholeChainId"]];
            if (hasProcess.has(hasKey) && currentTimeStamp - hasProcess.get(hasKey) <= 10 * 60) {
                logWithTimestamp(`emitterChainId:${d["srcWormholeChainId"]} sequence:${d["sequence"]} inner 10min has process`);
                continue;
            } else {
                hasProcess.set(hasKey, currentTimeStamp);
            }
            await processVaa(connection, payer, dstSoDiamond, vaa, d["srcWormholeChainId"], d["sequence"], d["extrinsicHash"]);
        }
    }
}


async function main() {
    logWithTimestamp("Start solana relayer....")
    await processV2(SOLANA_EMITTER_CHAIN, NET_TO_EMITTER[NET]);
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
