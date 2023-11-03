import {Omniswap} from "./types/omniswap";
import IDL from "./idl/omniswap.json";
import {Program, Provider, Wallet} from "@coral-xyz/anchor";
import {
    AccountLayout,
    ASSOCIATED_TOKEN_PROGRAM_ID,
    getOrCreateAssociatedTokenAccount,
    TOKEN_PROGRAM_ID
} from "@solana/spl-token"
import {
    Connection,
    Keypair,
    PublicKey,
    PublicKeyInitData,
    SystemProgram,
    SYSVAR_RENT_PUBKEY,
    TransactionInstruction
} from "@solana/web3.js";
import {ChainId, ParsedTokenTransferVaa, parseTokenTransferVaa} from "@certusone/wormhole-sdk";
import {
    CompleteTransferNativeWithPayloadCpiAccounts,
    CompleteTransferWrappedWithPayloadCpiAccounts,
    deriveAddress
} from "@certusone/wormhole-sdk/lib/cjs/solana";
import {
    deriveCustodyKey,
    deriveCustodySignerKey,
    deriveEndpointKey,
    deriveMintAuthorityKey,
    deriveRedeemerAccountKey,
    deriveTokenBridgeConfigKey,
    deriveWrappedMetaKey,
    deriveWrappedMintKey
} from "@certusone/wormhole-sdk/lib/cjs/solana/tokenBridge";
import {deriveClaimKey, derivePostedVaaKey} from "@certusone/wormhole-sdk/lib/cjs/solana/wormhole";
import * as bs58 from "bs58";
import {ethers} from 'ethers';
import fs from "fs";
import path from 'path';
import Decimal from "decimal.js";
import {
    buildDefaultAccountFetcher,
    buildWhirlpoolClient,
    ORCA_WHIRLPOOL_PROGRAM_ID,
    PDAUtil,
    swapQuoteByInputToken,
    WhirlpoolContext
} from "@orca-so/whirlpools-sdk";
import {DecimalUtil, Percentage, resolveOrCreateATA} from "@orca-so/common-sdk";
import * as assert from "assert";


export class PersistentDictionary {
    private data: Record<string, any>;
    private filename: string;

    constructor(filename: string) {
        const directory = path.dirname(filename);
        if (!fs.existsSync(directory)) {
            fs.mkdirSync(directory, {recursive: true});
        }
        this.filename = filename;
        this.loadDataFromFile();
    }

    private loadDataFromFile() {
        try {
            const fileContent = fs.readFileSync(this.filename, 'utf8');
            this.data = JSON.parse(fileContent);
        } catch (error) {
            this.data = {};
        }
    }

    private saveDataToFile() {
        fs.writeFileSync(this.filename, JSON.stringify(this.data, null, 2), 'utf8');
    }

    get(key: string, defaultValue: any = null): any {
        if (key in this.data) {
            return this.data[key];
        } else {
            this.set(key, defaultValue);
            return defaultValue;
        }
    }

    set(key: string, value: any) {
        this.data[key] = value;
        this.saveDataToFile();
    }

    // delete(key: string) {
    //     delete this.data[key];
    //     this.saveDataToFile();
    // }
    //
    // getAll(): Record<string, any> {
    //     return this.data;
    // }
}

export interface WormholeData {
    dstMaxGasPrice: number;
    dstMaxGas: number,
    soTransactionId: Buffer,
    soReceiver: string,
    soReceivingAssetId: string
}

export interface SwapData {
    swapCallTo: string;
    swapSendingAssetId: string;
    swapReceivingAssetId: string;
    swapCallData: Buffer;
}

export interface SwapDataList {
    swapDataList: SwapData[]
}

export interface ParsedOmniswapPayload extends ParsedTokenTransferVaa, WormholeData, SwapDataList {
}


export function parseVaaToOmniswapPayload(vaa: Buffer): ParsedOmniswapPayload {
    const tokenTransfer = parseTokenTransferVaa(vaa);

    const payloadLen = tokenTransfer.tokenTransferPayload.length;

    let index = 0;

    let len = tokenTransfer.tokenTransferPayload.readUint8(index);
    index += 1;
    let dstMaxGasPrice;
    try {
        dstMaxGasPrice = tokenTransfer.tokenTransferPayload.readUIntBE(index, len);
    } catch (error) {
        dstMaxGasPrice = tokenTransfer.tokenTransferPayload.readUIntBE(index, 5);
    }
    index += len;

    len = tokenTransfer.tokenTransferPayload.readUint8(index);
    index += 1;
    let dstMaxGas;
    try {
        dstMaxGas = tokenTransfer.tokenTransferPayload.readUIntBE(index, len);
    } catch (error) {
        dstMaxGas = tokenTransfer.tokenTransferPayload.readUIntBE(index, 5);
    }
    index += len;

    len = tokenTransfer.tokenTransferPayload.readUint8(index);
    index += 1;
    let soTransactionId = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
    index += len;

    len = tokenTransfer.tokenTransferPayload.readUint8(index);
    index += 1;
    let soReceiver = bs58.encode(tokenTransfer.tokenTransferPayload.subarray(index, index + len));
    index += len;

    len = tokenTransfer.tokenTransferPayload.readUint8(index);
    index += 1;
    let soReceivingAssetId = bs58.encode(tokenTransfer.tokenTransferPayload.subarray(index, index + len));
    index += len;

    if (index < payloadLen) {
        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        index += len;
    }

    let swapDataList = [];
    while (index < payloadLen) {
        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapCallTo = bs58.encode(tokenTransfer.tokenTransferPayload.subarray(index, index + len));
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapSendingAssetId = bs58.encode(tokenTransfer.tokenTransferPayload.subarray(index, index + len));
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapReceivingAssetId = bs58.encode(tokenTransfer.tokenTransferPayload.subarray(index, index + len));
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUIntBE(index, 2);
        index += 2;
        let swapCallData = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
        index += len;
        swapDataList.push(
            {
                swapCallTo,
                swapSendingAssetId,
                swapReceivingAssetId,
                swapCallData
            }
        )
    }

    return {
        dstMaxGasPrice: dstMaxGasPrice,
        dstMaxGas: dstMaxGas,
        soTransactionId,
        soReceiver,
        soReceivingAssetId,
        swapDataList,
        ...tokenTransfer,

    }
}

export async function queryRelayEventByGetLogs(provider: ethers.providers.JsonRpcProvider, contractAddress, fromBlock, toBlock) {
    const filter = {
        address: contractAddress,
        topics: ["0x0f0fd0ad174232a46f92a8d76b425830f45436483106ee965bbe91d3b7d1cd26"],
        fromBlock,
        toBlock
    };
    try {
        return await provider.getLogs(filter);
    } catch (error) {
        return []
    }
}


export function deriveRedeemerConfigKey(programId: PublicKeyInitData) {
    return deriveAddress([Buffer.from("redeemer")], programId);
}

export function deriveSoFeeConfigKey(programId: PublicKeyInitData) {
    return deriveAddress([Buffer.from("so_fee")], programId);
}

export function deriveForeignContractKey(
    programId: PublicKeyInitData,
    chain: ChainId
) {
    return deriveAddress(
        [
            Buffer.from("foreign_contract"),
            (() => {
                const buf = Buffer.alloc(2);
                buf.writeUInt16LE(chain);
                return buf;
            })(),
        ],
        programId
    );
}

export function deriveTmpTokenAccountKey(
    programId: PublicKeyInitData,
    mint: PublicKeyInitData
) {
    return deriveAddress(
        [Buffer.from("tmp"), new PublicKey(mint).toBuffer()],
        programId
    );
}

export function deriveUnwrapSolAccountKey(
    programId: PublicKeyInitData
) {
    return deriveAddress(
        [Buffer.from("unwrap")],
        programId
    );
}

export function createHelloTokenProgramInterface(
    connection: Connection,
    programId: PublicKeyInitData,
    payer?: PublicKeyInitData
): Program<Omniswap> {
    const provider: Provider = {
        connection,
        publicKey: payer == undefined ? undefined : new PublicKey(payer),
    };
    return new Program<Omniswap>(
        IDL as any,
        new PublicKey(programId),
        provider
    );
}

// Temporary
export function getCompleteTransferNativeWithPayloadCpiAccounts(
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    payer: PublicKeyInitData,
    vaa: ParsedOmniswapPayload | ParsedTokenTransferVaa,
    toTokenAccount: PublicKeyInitData
): CompleteTransferNativeWithPayloadCpiAccounts {
    const parsed = vaa;
    const mint = new PublicKey(parsed.tokenAddress);
    const cpiProgramId = new PublicKey(parsed.to);

    return {
        payer: new PublicKey(payer),
        tokenBridgeConfig: deriveTokenBridgeConfigKey(tokenBridgeProgramId),
        vaa: derivePostedVaaKey(wormholeProgramId, parsed.hash),
        tokenBridgeClaim: deriveClaimKey(
            tokenBridgeProgramId,
            parsed.emitterAddress,
            parsed.emitterChain,
            parsed.sequence
        ),
        tokenBridgeForeignEndpoint: deriveEndpointKey(
            tokenBridgeProgramId,
            parsed.emitterChain,
            parsed.emitterAddress
        ),
        toTokenAccount: new PublicKey(toTokenAccount),
        tokenBridgeRedeemer: deriveRedeemerAccountKey(cpiProgramId),
        toFeesTokenAccount: new PublicKey(toTokenAccount),
        tokenBridgeCustody: deriveCustodyKey(tokenBridgeProgramId, mint),
        mint,
        tokenBridgeCustodySigner: deriveCustodySignerKey(tokenBridgeProgramId),
        rent: SYSVAR_RENT_PUBKEY,
        systemProgram: SystemProgram.programId,
        tokenProgram: TOKEN_PROGRAM_ID,
        wormholeProgram: new PublicKey(wormholeProgramId),
    };
}

// Temporary
export function getCompleteTransferWrappedWithPayloadCpiAccounts(
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    payer: PublicKeyInitData,
    vaa: ParsedOmniswapPayload | ParsedTokenTransferVaa,
    toTokenAccount: PublicKeyInitData
): CompleteTransferWrappedWithPayloadCpiAccounts {
    const parsed = vaa;
    const mint = deriveWrappedMintKey(
        tokenBridgeProgramId,
        parsed.tokenChain,
        parsed.tokenAddress
    );
    const cpiProgramId = new PublicKey(parsed.to);
    return {
        payer: new PublicKey(payer),
        tokenBridgeConfig: deriveTokenBridgeConfigKey(tokenBridgeProgramId),
        vaa: derivePostedVaaKey(wormholeProgramId, parsed.hash),
        tokenBridgeClaim: deriveClaimKey(
            tokenBridgeProgramId,
            parsed.emitterAddress,
            parsed.emitterChain,
            parsed.sequence
        ),
        tokenBridgeForeignEndpoint: deriveEndpointKey(
            tokenBridgeProgramId,
            parsed.emitterChain,
            parsed.emitterAddress
        ),
        toTokenAccount: new PublicKey(toTokenAccount),
        tokenBridgeRedeemer: deriveRedeemerAccountKey(cpiProgramId),
        toFeesTokenAccount: new PublicKey(toTokenAccount),
        tokenBridgeWrappedMint: mint,
        tokenBridgeWrappedMeta: deriveWrappedMetaKey(tokenBridgeProgramId, mint),
        tokenBridgeMintAuthority: deriveMintAuthorityKey(tokenBridgeProgramId),
        rent: SYSVAR_RENT_PUBKEY,
        systemProgram: SystemProgram.programId,
        tokenProgram: TOKEN_PROGRAM_ID,
        wormholeProgram: new PublicKey(wormholeProgramId),
    };
}

export async function createCompleteSoSwapNativeWithoutSwap(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer,
    beneficiary: PublicKeyInitData,
    skipVerify: boolean
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    let parsed: ParsedOmniswapPayload | ParsedTokenTransferVaa;
    let recipient: PublicKey;
    let mint: PublicKey;
    let unwrapSolAccount: PublicKey = null;
    let wsolMint: PublicKey = null;
    let recipientAccount: PublicKey = null;
    if (!skipVerify) {
        parsed = parseVaaToOmniswapPayload(wormholeMessage);
        mint = new PublicKey(parsed.tokenAddress);
        if ("soReceiver" in parsed) {
            recipient = new PublicKey(parsed.soReceiver);
            if (parsed.soReceivingAssetId === "11111111111111111111111111111111") {
                unwrapSolAccount = deriveUnwrapSolAccountKey(programId);
                wsolMint = new PublicKey("So11111111111111111111111111111111111111112");
                recipientAccount = recipient;
            }
        }
    } else {
        parsed = parseTokenTransferVaa(wormholeMessage);
        mint = new PublicKey(parsed.tokenAddress);
        recipient = payer.publicKey;
    }

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, mint);
    const tokenBridgeAccounts = getCompleteTransferNativeWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payAddress,
        parsed,
        tmpTokenAccount
    );

    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, mint, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, mint, new PublicKey(beneficiary))).address;

    return program.methods
        .completeSoSwapNativeWithoutSwap([...parsed.hash], skipVerify)
        .accounts({
            payer: tokenBridgeAccounts.payer,
            config: deriveRedeemerConfigKey(programId),
            feeConfig: deriveSoFeeConfigKey(programId),
            beneficiaryTokenAccount,
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            mint,
            recipientTokenAccount,
            tmpTokenAccount,
            unwrapSolAccount,
            wsolMint,
            recipient: recipientAccount,
            wormholeProgram: tokenBridgeAccounts.wormholeProgram,
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            tokenBridgeConfig: tokenBridgeAccounts.tokenBridgeConfig,
            vaa: tokenBridgeAccounts.vaa,
            tokenBridgeClaim: tokenBridgeAccounts.tokenBridgeClaim,
            tokenBridgeForeignEndpoint: tokenBridgeAccounts.tokenBridgeForeignEndpoint,
            tokenBridgeCustody: tokenBridgeAccounts.tokenBridgeCustody,
            tokenBridgeCustodySigner: tokenBridgeAccounts.tokenBridgeCustodySigner,
            systemProgram: tokenBridgeAccounts.systemProgram,
            tokenProgram: tokenBridgeAccounts.tokenProgram,
            associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
            rent: tokenBridgeAccounts.rent,
        })
        .instruction();
}

export async function createCompleteSoSwapWrappedWithoutSwap(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer,
    beneficiary: PublicKeyInitData,
    skipVerify: boolean
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    let parsed: ParsedOmniswapPayload | ParsedTokenTransferVaa;
    let recipient: PublicKey;
    if (!skipVerify) {
        parsed = parseVaaToOmniswapPayload(wormholeMessage);
        if ("soReceiver" in parsed) {
            recipient = new PublicKey(parsed.soReceiver);
        }
    } else {
        parsed = parseTokenTransferVaa(wormholeMessage);
        recipient = payer.publicKey;
    }

    const wrappedMint = deriveWrappedMintKey(
        tokenBridgeProgramId,
        parsed.tokenChain,
        parsed.tokenAddress
    );

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, wrappedMint);
    const tokenBridgeAccounts = getCompleteTransferWrappedWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payAddress,
        parsed,
        tmpTokenAccount
    );

    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, wrappedMint, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, wrappedMint, new PublicKey(beneficiary))).address;

    return program.methods
        .completeSoSwapWrappedWithoutSwap([...parsed.hash], skipVerify)
        .accounts({
            payer: tokenBridgeAccounts.payer,
            config: deriveRedeemerConfigKey(programId),
            feeConfig: deriveSoFeeConfigKey(programId),
            beneficiaryTokenAccount,
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            tokenBridgeWrappedMint: tokenBridgeAccounts.tokenBridgeWrappedMint,
            recipientTokenAccount,
            tmpTokenAccount,
            wormholeProgram: tokenBridgeAccounts.wormholeProgram,
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            tokenBridgeWrappedMeta: tokenBridgeAccounts.tokenBridgeWrappedMeta,
            tokenBridgeConfig: tokenBridgeAccounts.tokenBridgeConfig,
            vaa: tokenBridgeAccounts.vaa,
            tokenBridgeClaim: tokenBridgeAccounts.tokenBridgeClaim,
            tokenBridgeForeignEndpoint: tokenBridgeAccounts.tokenBridgeForeignEndpoint,
            tokenBridgeMintAuthority: tokenBridgeAccounts.tokenBridgeMintAuthority,
            systemProgram: tokenBridgeAccounts.systemProgram,
            tokenProgram: tokenBridgeAccounts.tokenProgram,
            associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
            rent: tokenBridgeAccounts.rent,
        })
        .instruction();
}


const CACHE_DECIMAL = {};

async function getTokenDecimal(
    connection: Connection,
    tokenAddress: PublicKeyInitData,
) {
    const tokenAddressStr = tokenAddress.toString();
    if (tokenAddressStr in CACHE_DECIMAL) {
        return CACHE_DECIMAL[tokenAddressStr];
    } else {
        const tokenInfo = await connection.getTokenSupply(new PublicKey(tokenAddress));
        const decimal = tokenInfo.value.decimals;
        CACHE_DECIMAL[tokenAddressStr] = decimal;
        return decimal;
    }

}


export interface QuoteConfig {
    whirlpoolProgram: string;
    whirlpool: string;
    tokenMintA: PublicKey;
    tokenMintB: PublicKey;
    tokenOwnerAccountA: PublicKey;
    tokenOwnerAccountB: PublicKey;
    tokenVaultA: PublicKey;
    tokenVaultB: PublicKey;
    tickArray0: string;
    tickArray1: string;
    tickArray2: string;
    oracle: string;
    isAToB: boolean;
    amountIn: Decimal;
    estimatedAmountOut: Decimal;
    minAmountOut: Decimal;
}

export async function getQuoteConfig(
    connection: Connection,
    payer: Keypair,
    parsed: ParsedOmniswapPayload
): Promise<QuoteConfig> {
    const ctx = WhirlpoolContext.from(
        connection,
        new Wallet(payer),
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);
    const acountFetcher = buildDefaultAccountFetcher(connection);


    assert.strictEqual(parsed.swapDataList.length, 1, "swapDataList !== 1");

    // get pool
    const pool = parsed.swapDataList[0].swapCallTo;

    const whirlpool = await client.getPool(pool);

    // acceptable slippage is 1.0% (10/1000)
    const default_slippage = Percentage.fromFraction(500, 1000);

    const input_token_mint = new PublicKey(parsed.swapDataList[0].swapSendingAssetId)
    const shift_decimals = await getTokenDecimal(connection, input_token_mint);

    let amount_in = Number(parsed.amount);
    if (shift_decimals > 8) {
        amount_in = amount_in * Math.pow(10, shift_decimals - 8);
    }

    const shift_amount_in = DecimalUtil.toBN(new Decimal(amount_in))

    const quote = await swapQuoteByInputToken(
        whirlpool,
        input_token_mint,
        shift_amount_in,
        default_slippage,
        ctx.program.programId,
        acountFetcher,
    );

    const whirlpool_data = whirlpool.getData();

    const token_owner_account_a = await getOrCreateAssociatedTokenAccount(connection, payer, whirlpool_data.tokenMintA, payer.publicKey)

    const token_owner_account_b = await getOrCreateAssociatedTokenAccount(connection, payer, whirlpool_data.tokenMintB, payer.publicKey)

    const oracle_pda = await PDAUtil.getOracle(
        ctx.program.programId,
        whirlpool.getAddress()
    );

    return {
        whirlpoolProgram: ORCA_WHIRLPOOL_PROGRAM_ID.toString(),
        whirlpool: pool,
        tokenMintA: whirlpool_data.tokenMintA,
        tokenMintB: whirlpool_data.tokenMintB,
        tokenOwnerAccountA: token_owner_account_a.address,
        tokenOwnerAccountB: token_owner_account_b.address,
        tokenVaultA: whirlpool_data.tokenVaultA,
        tokenVaultB: whirlpool_data.tokenVaultB,
        tickArray0: quote.tickArray0.toString(),
        tickArray1: quote.tickArray1.toString(),
        tickArray2: quote.tickArray2.toString(),
        oracle: oracle_pda.publicKey.toString(),
        isAToB: quote.aToB,
        amountIn: DecimalUtil.fromBN(quote.estimatedAmountIn),
        estimatedAmountOut: DecimalUtil.fromBN(quote.estimatedAmountOut),
        minAmountOut: DecimalUtil.fromBN(quote.otherAmountThreshold),
    };
}

export async function createCompleteSoSwapNativeWithWhirlpool(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer,
    beneficiary: PublicKeyInitData
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = parseVaaToOmniswapPayload(wormholeMessage);

    const mint = new PublicKey(parsed.tokenAddress);

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, mint);
    const tokenBridgeAccounts = getCompleteTransferNativeWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payAddress,
        parsed,
        tmpTokenAccount
    );

    const recipient = new PublicKey(parsed.soReceiver);

    const quoteConfig = await getQuoteConfig(connection, payer, parsed);

    let bridgeToken: PublicKey;
    let dstToken: PublicKey;
    if (parsed.swapDataList.length == 0) {
        dstToken = new PublicKey(parsed.soReceiver);
        bridgeToken = new PublicKey(parsed.soReceiver);
    } else {
        dstToken = new PublicKey(parsed.swapDataList[parsed.swapDataList.length - 1].swapReceivingAssetId);
        bridgeToken = new PublicKey(parsed.swapDataList[0].swapSendingAssetId);
    }
    const recipientBridgeTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, bridgeToken, recipient)).address;
    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, dstToken, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, bridgeToken, new PublicKey(beneficiary))).address;

    let unwrapSolAccount: PublicKey;
    let wsolMint: PublicKey;
    let recipientAccount: PublicKey;
    if (parsed.soReceivingAssetId === "11111111111111111111111111111111") {
        unwrapSolAccount = deriveUnwrapSolAccountKey(programId);
        wsolMint = new PublicKey("So11111111111111111111111111111111111111112");
        recipientAccount = recipient;
    } else {
        unwrapSolAccount = null;
        wsolMint = null;
        recipientAccount = null;
    }

    return program.methods
        .completeSoSwapNativeWithWhirlpool([...parsed.hash])
        .accounts({
            payer: tokenBridgeAccounts.payer,
            config: deriveRedeemerConfigKey(programId),
            feeConfig: deriveSoFeeConfigKey(programId),
            beneficiaryTokenAccount,
            whirlpoolProgram: quoteConfig.whirlpoolProgram,
            whirlpoolAccount: quoteConfig.whirlpool,
            whirlpoolTokenOwnerAccountA: quoteConfig.tokenOwnerAccountA,
            whirlpoolTokenVaultA: quoteConfig.tokenVaultA,
            whirlpoolTokenOwnerAccountB: quoteConfig.tokenOwnerAccountB,
            whirlpoolTokenVaultB: quoteConfig.tokenVaultB,
            whirlpoolTickArray0: quoteConfig.tickArray0,
            whirlpoolTickArray1: quoteConfig.tickArray1,
            whirlpoolTickArray2: quoteConfig.tickArray2,
            whirlpoolOracle: quoteConfig.oracle,
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            unwrapSolAccount,
            wsolMint,
            recipient: recipientAccount,
            mint,
            recipientTokenAccount,
            recipientBridgeTokenAccount,
            tmpTokenAccount,
            wormholeProgram: tokenBridgeAccounts.wormholeProgram,
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            tokenBridgeConfig: tokenBridgeAccounts.tokenBridgeConfig,
            vaa: tokenBridgeAccounts.vaa,
            tokenBridgeClaim: tokenBridgeAccounts.tokenBridgeClaim,
            tokenBridgeForeignEndpoint: tokenBridgeAccounts.tokenBridgeForeignEndpoint,
            tokenBridgeCustody: tokenBridgeAccounts.tokenBridgeCustody,
            tokenBridgeCustodySigner: tokenBridgeAccounts.tokenBridgeCustodySigner,
            systemProgram: tokenBridgeAccounts.systemProgram,
            tokenProgram: tokenBridgeAccounts.tokenProgram,
            associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
            rent: tokenBridgeAccounts.rent,
        })
        .instruction();
}

export async function createCompleteSoSwapWrappedWithWhirlpool(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer,
    beneficiary: PublicKeyInitData
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = parseVaaToOmniswapPayload(wormholeMessage);

    const wrappedMint = deriveWrappedMintKey(
        tokenBridgeProgramId,
        parsed.tokenChain,
        parsed.tokenAddress
    );

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, wrappedMint);
    const tokenBridgeAccounts = getCompleteTransferWrappedWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payAddress,
        parsed,
        tmpTokenAccount
    );

    const quoteConfig = await getQuoteConfig(connection, payer, parsed);

    const recipient = new PublicKey(parsed.soReceiver);

    let bridgeToken: PublicKey;
    let dstToken: PublicKey;
    if (parsed.swapDataList.length == 0) {
        dstToken = new PublicKey(parsed.soReceiver);
        bridgeToken = new PublicKey(parsed.soReceiver);
    } else {
        dstToken = new PublicKey(parsed.swapDataList[parsed.swapDataList.length - 1].swapReceivingAssetId);
        bridgeToken = new PublicKey(parsed.swapDataList[0].swapSendingAssetId);
    }
    const recipientBridgeTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, bridgeToken, recipient)).address;
    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, dstToken, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, bridgeToken, new PublicKey(beneficiary))).address;


    let unwrapSolAccount: PublicKey;
    let wsolMint: PublicKey;
    let recipientAccount: PublicKey;
    if (parsed.soReceivingAssetId === "11111111111111111111111111111111") {
        unwrapSolAccount = deriveUnwrapSolAccountKey(programId);
        wsolMint = new PublicKey("So11111111111111111111111111111111111111112");
        recipientAccount = recipient;
    } else {
        unwrapSolAccount = null;
        wsolMint = null;
        recipientAccount = null;
    }

    return program.methods
        .completeSoSwapWrappedWithWhirlpool([...parsed.hash])
        .accounts({
            payer: tokenBridgeAccounts.payer,
            config: deriveRedeemerConfigKey(programId),
            feeConfig: deriveSoFeeConfigKey(programId),
            beneficiaryTokenAccount,
            whirlpoolProgram: quoteConfig.whirlpoolProgram,
            whirlpoolAccount: quoteConfig.whirlpool,
            whirlpoolTokenOwnerAccountA: quoteConfig.tokenOwnerAccountA,
            whirlpoolTokenVaultA: quoteConfig.tokenVaultA,
            whirlpoolTokenOwnerAccountB: quoteConfig.tokenOwnerAccountB,
            whirlpoolTokenVaultB: quoteConfig.tokenVaultB,
            whirlpoolTickArray0: quoteConfig.tickArray0,
            whirlpoolTickArray1: quoteConfig.tickArray1,
            whirlpoolTickArray2: quoteConfig.tickArray2,
            whirlpoolOracle: quoteConfig.oracle,
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            tokenBridgeWrappedMint: tokenBridgeAccounts.tokenBridgeWrappedMint,
            recipientTokenAccount,
            recipientBridgeTokenAccount,
            tmpTokenAccount,
            unwrapSolAccount,
            wsolMint,
            recipient: recipientAccount,
            wormholeProgram: tokenBridgeAccounts.wormholeProgram,
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            tokenBridgeWrappedMeta: tokenBridgeAccounts.tokenBridgeWrappedMeta,
            tokenBridgeConfig: tokenBridgeAccounts.tokenBridgeConfig,
            vaa: tokenBridgeAccounts.vaa,
            tokenBridgeClaim: tokenBridgeAccounts.tokenBridgeClaim,
            tokenBridgeForeignEndpoint: tokenBridgeAccounts.tokenBridgeForeignEndpoint,
            tokenBridgeMintAuthority: tokenBridgeAccounts.tokenBridgeMintAuthority,
            systemProgram: tokenBridgeAccounts.systemProgram,
            tokenProgram: tokenBridgeAccounts.tokenProgram,
            associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
            rent: tokenBridgeAccounts.rent,
        })
        .instruction();
}
