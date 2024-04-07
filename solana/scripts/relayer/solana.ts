import {
    ComputeBudgetProgram,
    Connection,
    Keypair,
    PublicKey,
    TransactionInstruction,
    TransactionMessage,
    VersionedTransaction
} from "@solana/web3.js";
import fs from "fs";
import axios from "axios";
import {
    createCompleteSoSwapNativeWithoutSwap,
    createCompleteSoSwapNativeWithWhirlpool,
    createCompleteSoSwapWrappedWithoutSwap,
    createCompleteSoSwapWrappedWithWhirlpool,
    ParsedOmniswapPayload,
    parseVaaToOmniswapPayload,
    PersistentDictionary,
    queryRelayEventByGetLogs
} from "./helper";
import {createObjectCsvWriter} from 'csv-writer';
import * as dotenv from 'dotenv';
import {ethers} from 'ethers';
import {postVaaSolanaWithRetry} from "@certusone/wormhole-sdk";


const ARGS = process.argv.slice(2);
if (ARGS.length != 2) {
    throw new Error("Please set .env path and gas path")
}
const ENV_FILE = ARGS[0];
const GAS_FILE = ARGS[1];
if (dotenv.config({path: ENV_FILE}).error) {
    throw new Error(".env format error")
}

if (process.env.RELAYER_KEY == null) {
    throw new Error(".env RELAYER_KEY not found")
}

const NET = "solana-mainnet";
let SOLANA_EMITTER_CHAIN: number;
let CORE_BRIDGE_PID;
let TOKEN_BRIDGE_PID;
let WORMHOLE_URL: string[];
let NET_TO_WORMHOLE_CHAIN_ID;
let WORMHOLE_CHAIN_ID_TO_NET;
let NET_TO_EMITTER;
let PENDING_URL;
let OMNISWAP_PID;
let SOLANA_URL;
let NET_TO_RPC;
let NET_TO_CONTRACT;
let NET_TO_DEFAULT_FROM_BLOCK;
let SODIAMOND;
let BENEFICIARY;
let LOOKUP_TABLE_KEY;

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
    NET_TO_RPC = {
        "bsc-test": ["https://rpc.ankr.com/bsc_testnet_chapel"]
    }
    NET_TO_CONTRACT = {
        "bsc-test": "0x84B7cA95aC91f8903aCb08B27F5b41A4dE2Dc0fc"
    }
    NET_TO_DEFAULT_FROM_BLOCK = {
        "bsc-test": 34075043
    }
    NET_TO_EMITTER = {
        "goerli": "0xF890982f9310df57d00f659cf4fd87e65adEd8d7",
        "bsc-test": "0x9dcF9D205C9De35334D646BeE44b2D2859712A09",
        "polygon-test": "0x377D55a7928c046E18eEbb61977e714d2a76472a",
        "avax-test": "0x61E44E506Ca5659E6c0bba9b678586fA2d729756",
        "optimism-test": "0xC7A204bDBFe983FCD8d8E61D02b475D4073fF97e",
        "arbitrum-test": "0x23908A62110e21C04F3A4e011d24F901F911744A",
        "aptos-testnet": "0x0000000000000000000000000000000000000000000000000000000000000002",
        // todo! fix
        "sui-testnet": "0x6fb10cdb7aa299e9a4308752dadecb049ff55a892de92992a1edbd7912b3d6da",
        "base-test": "0xA31aa3FDb7aF7Db93d18DDA4e19F811342EDF780",
        "solana-testnet": "0x3b26409f8aaded3f5ddca184695aa6a0fa829b0c85caf84856324896d214ca98"
    }
    CORE_BRIDGE_PID = new PublicKey("3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5");
    TOKEN_BRIDGE_PID = new PublicKey("DZnkkTmCiFWfYTfT41X3Rd1kDgozqzxWaHqsw6W4x2oe");
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    SOLANA_URL = ["https://sparkling-wild-hexagon.solana-devnet.discover.quiknode.pro/2129a56170ae922c0d50ec36a09a6f683ab5a466/"];
    OMNISWAP_PID = new PublicKey("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY");
    // OMNISWAP_PID base58decode
    SODIAMOND = "0x3636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843"
    BENEFICIARY = "vQkE51MXJiwqtbwf562XWChNKZTgh6L2jHPpupoCKjS";
    LOOKUP_TABLE_KEY = new PublicKey("ESxWFjHVo2oes1eAQiwkAUHNTTUT9Xm5zsSrE7QStYX8")
} else {
    WORMHOLE_URL = [
        "https://api.wormholescan.io",
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
    NET_TO_RPC = {
        "bsc-main": ["https://bsc-dataseed1.ninicoin.io"],
        "polygon-main": ["https://polygon-mainnet.g.alchemy.com/v2/woLOizgiyajLQII9XoReQhCgdgW2G2oL"],
        "avax-main": ["https://api.snowtrace.io/api"],
        "mainnet": ["https://eth.llamarpc.com"],
    }
    NET_TO_DEFAULT_FROM_BLOCK = {
        "bsc-main": 33108007,
        "polygon-main": 49407175,
        "avax-main": 37191237,
        "mainnet": 18476135,
    }
    NET_TO_CONTRACT = {
        "bsc-main": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "polygon-main": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "avax-main": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
        "mainnet": "0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    }
    NET_TO_EMITTER = {
        "mainnet": "0x3ee18B2214AFF97000D974cf647E7C347E8fa585",
        "bsc-main": "0xB6F6D86a8f9879A9c87f643768d9efc38c1Da6E7",
        "polygon-main": "0x5a58505a96D1dbf8dF91cB21B54419FC36e93fdE",
        "avax-main": "0x0e082F06FF657D94310cB8cE8B0D9a04541d8052",
        "optimism-main": "0x1D68124e65faFC907325e3EDbF8c4d84499DAa8b",
        "arbitrum-main": "0x0b2402144Bb366A632D14B83F244D2e0e21bD39c",
        "aptos-mainnet": "0x0000000000000000000000000000000000000000000000000000000000000002",
        "sui-mainnet": "0xccceeb29348f71bdd22ffef43a2a19c1f5b5e17c5cca5411529120182672ade5",
        "base-main": "0x8d2de8d2f73F1F4cAB472AC9A881C9b123C79627",
        "solana-mainnet": "0xec7372995d5cc8732397fb0ad35c0121e0eaa90d26f828a534cab54391b3a4f5",
    }
    CORE_BRIDGE_PID = new PublicKey("worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth");
    TOKEN_BRIDGE_PID = new PublicKey("wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb");
    SOLANA_EMITTER_CHAIN = 1;
    PENDING_URL = "https://crossswap.coming.chat/v1/getUnSendTransferFromWormhole"
    SOLANA_URL = [
        // "https://solana-mainnet.g.alchemy.com/v2/rXqEm4i3ls_fF0BvJKdxUcVofs-6J9gj",
        // "https://solana-mainnet.g.alchemy.com/v2/7D-QdovVWLr7utZ-hNhEJU0cUwotpY_l",
        "https://api.mainnet-beta.solana.com"
    ];
    OMNISWAP_PID = new PublicKey("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY");
    // OMNISWAP_PID base58decode
    SODIAMOND = "0x3636a3d9e02dccb121118909a4c7fcfbb292b61c774638ce0b093c2441bfa843"
    BENEFICIARY = "8LC49giae4hkSV6bS5dXP9G7jwvVAtShDsGQrKKycQc3";
    LOOKUP_TABLE_KEY = new PublicKey("8K1NLm2WvUT9inQGsRjF3vrq5wUMtRbPRcWgNpUNNBFC")
}
WORMHOLE_CHAIN_ID_TO_NET = Object.keys(NET_TO_WORMHOLE_CHAIN_ID).reduce((returnValue, key) => {
    const value = NET_TO_WORMHOLE_CHAIN_ID[key];
    returnValue[value] = key;
    return returnValue;
}, {})
const fromBlockDict = new PersistentDictionary("./cache/latestFromBlock.json");
const hasPostVaa = new Map<string, boolean>();

function getRandomWormholeUrl() {
    const randomIndex: number = Math.floor(Math.random() * WORMHOLE_URL.length);
    return WORMHOLE_URL[randomIndex]
}

function getRandomSolanaUrl() {
    const randomIndex: number = Math.floor(Math.random() * SOLANA_URL.length);
    return SOLANA_URL[randomIndex]
}

function remove0x(addr) {
    if (addr.startsWith("0x")) {
        addr = addr.substring(2);
    }
    return addr
}

function formatEmitterAddress(addr) {
    addr = remove0x(addr);
    while (addr.length < 64) {
        addr = "0" + addr;
    }
    return addr
}


async function getSignedVaaByWormhole(
    sequence,
    emitterChainId
): Promise<Buffer> {
    const wormholeUrl = getRandomWormholeUrl()
    const srcNet = WORMHOLE_CHAIN_ID_TO_NET[emitterChainId]
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

function getRandomItem<T>(items: T[]): T | undefined {
    if (items.length === 0) {
        return undefined;
    }

    const randomIndex = Math.floor(Math.random() * items.length);
    return items[randomIndex];
}

function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function getPendingDataFromEvm(net) {
    /*
    struct TransferWithPayload {
        // PayloadID uint8 = 3
        uint8 payloadID;
        // Amount being transferred (big-endian uint256)
        uint256 amount;
        // Address of the token. Left-zero-padded if shorter than 32 bytes
        bytes32 tokenAddress;
        // Chain ID of the token
        uint16 tokenChain;
        // Address of the recipient. Left-zero-padded if shorter than 32 bytes
        bytes32 to;
        // Chain ID of the recipient
        uint16 toChain;
        // Address of the message sender. Left-zero-padded if shorter than 32 bytes
        bytes32 fromAddress;
        // An arbitrary payload
        bytes payload;
    }
    */
    const url: string = getRandomItem(NET_TO_RPC[net])
    const provider = new ethers.providers.JsonRpcProvider(url);
    const contractAddress = NET_TO_CONTRACT[net];
    const defaultValue = NET_TO_DEFAULT_FROM_BLOCK[net];
    let fromBlock = fromBlockDict.get(net, defaultValue);
    const latestBlock = await provider.getBlockNumber();
    const data = [];
    while (fromBlock <= latestBlock) {
        const curBlock = fromBlock;
        const toBlock = Math.min(fromBlock + 1000, latestBlock);
        logWithTimestamp(`Query log fromBlock:${fromBlock} toBlock:${toBlock} latestBlock:${latestBlock}`);
        const logs = await queryRelayEventByGetLogs(provider, contractAddress, fromBlock, toBlock);
        fromBlock = toBlock + 1;
        fromBlockDict.set(net, fromBlock);
        if (logs.length == 0) {
            continue
        }
        for (const log of logs) {
            const txReceipt = await provider.getTransactionReceipt(log["transactionHash"]);
            const wormholeLog = txReceipt.logs.find(element => element.topics[0] == "0x6eb224fb001ed210e379b335e35efe88672a8ce935d981a6896b27ffdf52a3b2");
            const wormholeLogData = Buffer.from(remove0x(wormholeLog.data), "hex");
            const sequence = wormholeLogData.readUintBE(26, 6);
            const toChain = wormholeLogData.readUintBE(160 + 99, 2);
            if (toChain == 1) {
                data.push({
                    "chainName": net,
                    "extrinsicHash": log["transactionHash"],
                    "srcWormholeChainId": NET_TO_WORMHOLE_CHAIN_ID[net],
                    "dstWormholeChainId": 1,
                    "sequence": sequence,
                    "blockTimestamp": 1695210280,
                    "fromBlock": curBlock
                })
            }
        }
        if (data.length > 0) {
            return data;
        }
    }
    logWithTimestamp(`Pending latest block, sleep 3s`);
    await sleep(3000);
    return data;
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
        let data = response.data["record"];
        data.sort((x0, x1) => x0["sequence"] - x1["sequence"]);
        data = data.filter((x) => x["dstWormholeChainId"].toString() == dstWormholeChainId.toString())
        return data;
    } catch (error) {
        return [];
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
    ix: TransactionInstruction
) => {

    const blockhash = (await connection.getLatestBlockhash()).blockhash

    const lookup_table = (await connection.getAddressLookupTable(LOOKUP_TABLE_KEY)).value

    const ix0 = ComputeBudgetProgram.setComputeUnitLimit({units: 1200_000});
    const message0 = new TransactionMessage(
        {
            payerKey: payer.publicKey,
            instructions: [ix0, ix],
            recentBlockhash: blockhash,
        }
    ).compileToV0Message([lookup_table]);
    const tx = new VersionedTransaction(message0)
    tx.sign([payer]);
    return await connection.sendTransaction(tx);
}

async function processVaaWithoutSwap(
    connection: Connection,
    payer: Keypair,
    dstSoDiamond,
    vaa: Buffer,
    emitterChainId,
    sequence,
    extrinsicHash,
    skipVerify: boolean,
    hasKey
) {
    try {
        logWithTimestamp(`RedeemNativeWithoutSwap...`)
        const ix = await createCompleteSoSwapNativeWithoutSwap(
            connection,
            OMNISWAP_PID,
            payer,
            TOKEN_BRIDGE_PID,
            CORE_BRIDGE_PID,
            vaa,
            BENEFICIARY,
            skipVerify
        );
        const dstTx = await sendAndConfirmIx(connection, payer, ix);
        logWithTimestamp(`RedeemNativeWithoutSwap for emitterChainId:${emitterChainId}, sequence:${sequence} success: ${dstTx}`)
        recordGas(extrinsicHash, dstTx);
        return true;
    } catch (error) {
        if (JSON.stringify(error).includes("vaa. Error Code: AccountNotInitialized")) {
            hasPostVaa.set(hasKey, false)
        }
        logWithTimestamp(`RedeemNativeWithoutSwap for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${JSON.stringify(error)}`)
    }

    try {
        logWithTimestamp(`RedeemWrappedWithoutSwap...`)
        const ix = await createCompleteSoSwapWrappedWithoutSwap(
            connection,
            OMNISWAP_PID,
            payer,
            TOKEN_BRIDGE_PID,
            CORE_BRIDGE_PID,
            vaa,
            BENEFICIARY,
            skipVerify
        );
        const dstTx = await sendAndConfirmIx(connection, payer, ix);
        logWithTimestamp(`RedeemWrappedWithoutSwap for emitterChainId:${emitterChainId}, sequence:${sequence} success: ${dstTx}`)
        recordGas(extrinsicHash, dstTx);
        return true;
    } catch (error) {
        if (JSON.stringify(error).includes("vaa. Error Code: AccountNotInitialized")) {
            hasPostVaa.set(hasKey, false)
        }
        logWithTimestamp(`RedeemWrappedWithoutSwap for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${JSON.stringify(error)}`)
    }
}

async function processVaa(
    connection: Connection,
    payer: Keypair,
    dstSoDiamond,
    vaa: Buffer,
    emitterChainId,
    sequence,
    extrinsicHash,
    skipVerify: boolean
): Promise<boolean> {
    let payload: ParsedOmniswapPayload;
    try {
        payload = parseVaaToOmniswapPayload(vaa);
        if (payload.dstMaxGasPrice !== 1) {
            logWithTimestamp(`Parse signed vaa for emitterChainId:${emitterChainId} sequence:${sequence} dstMaxGasPrice ${payload.dstMaxGasPrice}!=1000000000000`)
            return false;
        }
        if (payload.to.toString("hex") !== remove0x(dstSoDiamond)) {
            logWithTimestamp(`Parse signed vaa for emitterChainId:${emitterChainId} sequence:${sequence} dstSoDiamond:${payload.to.toString("hex")}!=${dstSoDiamond}`)
            return false;
        }
    } catch (error) {
        logWithTimestamp(`Parse signed vaa for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${error}`)
        return false;
    }
    if (payload.soReceiver == "") {
        logWithTimestamp(`emitterChainId:${emitterChainId}, sequence:${sequence} not soReceiver`)
        return false;
    }
    const hasKey = `${sequence}@${emitterChainId}`;
    if (!hasPostVaa.has(hasKey) || !hasPostVaa.get(hasKey)) {
        const maxRetries = 3;
        try {
            const payAddress = payer.publicKey.toString();
            logWithTimestamp(`PostVaaSolana...`)
            const result = await postVaaSolanaWithRetry(
                connection,
                async (transaction) => {
                    transaction.partialSign(payer);
                    return transaction;
                },
                CORE_BRIDGE_PID,
                payAddress,
                vaa,
                maxRetries
            );
            logWithTimestamp(`PostVaaSolana for emitterChainId:${emitterChainId}, sequence:${sequence} finish, result: ${JSON.stringify(result)}`)
        } catch (error) {
            logWithTimestamp(`PostVaaSolana for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${JSON.stringify(error)}`)
        }
        hasPostVaa.set(hasKey, true)
    }

    if (skipVerify || payload.swapDataList.length === 0) {
        await processVaaWithoutSwap(
            connection,
            payer,
            dstSoDiamond,
            vaa,
            emitterChainId,
            sequence,
            extrinsicHash,
            skipVerify,
            hasKey
        );
    } else if (payload.swapDataList.length === 1) {
        try {
            logWithTimestamp(`RedeemNativeWithSwap...`)
            const ix = await createCompleteSoSwapNativeWithWhirlpool(
                connection,
                OMNISWAP_PID,
                payer,
                TOKEN_BRIDGE_PID,
                CORE_BRIDGE_PID,
                vaa,
                BENEFICIARY,
            );
            const dstTx = await sendAndConfirmIx(connection, payer, ix);
            logWithTimestamp(`RedeemNativeWithSwap for emitterChainId:${emitterChainId}, sequence:${sequence} success: ${dstTx}`)
            recordGas(extrinsicHash, dstTx);
            return true;
        } catch (error) {
            if (JSON.stringify(error).includes("vaa. Error Code: AccountNotInitialized")) {
                hasPostVaa.set(hasKey, false)
            }
            logWithTimestamp(`RedeemNativeWithSwap for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${JSON.stringify(error)}`)
            if (JSON.stringify(error).includes("AmountOutBelowMinimum")) {
                await processVaaWithoutSwap(
                    connection,
                    payer,
                    dstSoDiamond,
                    vaa,
                    emitterChainId,
                    sequence,
                    extrinsicHash,
                    skipVerify,
                    hasKey
                );
            }
        }

        try {
            logWithTimestamp(`RedeemWrappedWithSwap...`)
            const ix = await createCompleteSoSwapWrappedWithWhirlpool(
                connection,
                OMNISWAP_PID,
                payer,
                TOKEN_BRIDGE_PID,
                CORE_BRIDGE_PID,
                vaa,
                BENEFICIARY,
            );
            const dstTx = await sendAndConfirmIx(connection, payer, ix);
            logWithTimestamp(`RedeemWrappedWithSwap for emitterChainId:${emitterChainId}, sequence:${sequence} success: ${dstTx}`)
            recordGas(extrinsicHash, dstTx);
            return true;
        } catch (error) {
            if (JSON.stringify(error).includes("vaa. Error Code: AccountNotInitialized")) {
                hasPostVaa.set(hasKey, false)
            }
            logWithTimestamp(`RedeemWrappedWithSwap for emitterChainId:${emitterChainId}, sequence:${sequence} error: ${JSON.stringify(error)}`)
            if (JSON.stringify(error).includes("AmountOutBelowMinimum")) {
                await processVaaWithoutSwap(
                    connection,
                    payer,
                    dstSoDiamond,
                    vaa,
                    emitterChainId,
                    sequence,
                    extrinsicHash,
                    skipVerify,
                    hasKey
                );
            }
        }
    }


    return false;
}

function recordGas(
    srcTx,
    dstTx,
) {
    const data = [
        {srcTx: srcTx, dstTx: dstTx},
    ];
    const fileExists = fs.existsSync(GAS_FILE);

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
        .catch(() => {
        });
}

export interface ProcessInfo {
    lastTimestamp: number;
    count: number,
}

async function processV2(
    dstWormholeChainId,
    dstSoDiamond,
) {
    let payer: Keypair = Keypair.fromSecretKey(Uint8Array.from(JSON.parse(process.env.RELAYER_KEY)));
    const hasProcess = new Map<string, ProcessInfo>();
    const pendingInterval = 30;
    let lastPendingTime = 0;
    while (true) {
        const connection = new Connection(
            getRandomSolanaUrl(),
            "confirmed"
        );
        const currentTimeStamp: number = Math.floor(Date.now() / 1000);
        if (currentTimeStamp < lastPendingTime + pendingInterval) {
            continue;
        } else {
            lastPendingTime = currentTimeStamp;
        }
        let pendingData;
        try {
            // @ts-ignore
            if (NET === "solana-testnet") {
                pendingData = await getPendingDataFromEvm("bsc-test");
            } else {
                pendingData = await getPendingData(dstWormholeChainId);
            }
            logWithTimestamp(`Get signed vaa length: ${pendingData.length}`)
        } catch (error) {
            logWithTimestamp(`Get pending data error: ${error}`)
            continue
        }

        for (const d of pendingData) {
            let vaa;
            try {
                vaa = await getSignedVaaByWormhole(d["sequence"], d["srcWormholeChainId"])
                if (vaa == null) {
                    fromBlockDict.set(d["chainName"], d["fromBlock"]);
                    logWithTimestamp(`Waiting vaa for emitterChainId: ${d["srcWormholeChainId"]}, sequence:${d["sequence"]}`);
                    continue;
                }
            } catch (error) {
                logWithTimestamp(`Get signed vaa for: emitterChainId: ${d["srcWormholeChainId"]}, sequence:${d["sequence"]} error: ${error}`);
                continue
            }
            const hasKey = `${d["sequence"]}@${d["srcWormholeChainId"]}`;

            if (hasProcess.has(hasKey)) {
                const processInfo = hasProcess.get(hasKey);
                if (currentTimeStamp <= processInfo.lastTimestamp + 3 * 60) {
                    logWithTimestamp(`emitterChainId:${d["srcWormholeChainId"]} sequence:${d["sequence"]} inner 3min has process, pending...`);
                    continue
                } else if (processInfo.count >= 5) {
                    logWithTimestamp(`emitterChainId:${d["srcWormholeChainId"]} sequence:${d["sequence"]} has retry 5th, refuse`);
                    continue
                } else {
                    hasProcess.set(hasKey, {
                        lastTimestamp: currentTimeStamp,
                        count: processInfo.count + 1
                    })
                }
            } else {
                hasProcess.set(hasKey, {
                    lastTimestamp: currentTimeStamp,
                    count: 0
                })
            }

            const skipVerify = false;
            await processVaa(connection, payer, dstSoDiamond, vaa, d["srcWormholeChainId"], d["sequence"], d["extrinsicHash"], skipVerify);
        }
    }
}


async function main() {
    while (true) {
        try {
            logWithTimestamp(`Start solana relayer ${NET} ....`)
            await processV2(SOLANA_EMITTER_CHAIN, SODIAMOND);
        } catch (error) {
            logWithTimestamp(`Restart solana relayer`);
        }
    }

}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
