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
    soReceivingAssetId: Buffer
}

export interface SwapData {
    swapCallTo: Buffer;
    swapSendingAssetId: Buffer;
    swapReceivingAssetId: Buffer;
    swapCallData: Buffer;
}

export interface SwapDataList {
    swapDataList: SwapData[]
}

export interface ParsedOmniswapPayload extends ParsedTokenTransferVaa, WormholeData, SwapDataList {
}


export function parseVaaToOmniswapPayload(vaa: Buffer): ParsedOmniswapPayload {
    const tokenTransfer = parseTokenTransferVaa(vaa);

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
    let soReceivingAssetId = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
    index += len;

    if (index < vaa.length) {
        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        index += len;
    }

    let swapDataList = [];
    while (index < vaa.length) {
        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapCallTo = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapSendingAssetId = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
        let swapReceivingAssetId = tokenTransfer.tokenTransferPayload.subarray(index, index + len);
        index += len;

        len = tokenTransfer.tokenTransferPayload.readUint8(index);
        index += 1;
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
    vaa: ParsedOmniswapPayload,
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
    vaa: ParsedOmniswapPayload,
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

    const recipient = new PublicKey(parsed.soReceiver);
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


export async function getQuoteConfig(
    connection: Connection,
    payer: Keypair,
    parsed: ParsedOmniswapPayload
): Promise<{ [key: string]: any }> {
    const ctx = WhirlpoolContext.from(
        connection,
        new Wallet(payer),
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);
    const acountFetcher = buildDefaultAccountFetcher(connection);


    assert.strictEqual(parsed.swapDataList.length, 1, "swapDataList !== 1");

    // get pool
    const pool = parsed.swapDataList[0].swapCallTo.toString("ascii");

    const whirlpool = await client.getPool(pool);

    // acceptable slippage is 1.0% (10/1000)
    const default_slippage = Percentage.fromFraction(100, 1000);

    const input_token_mint = new PublicKey(parsed.swapDataList[0].swapSendingAssetId)
    const shift_decimals = await getTokenDecimal(connection, input_token_mint);

    let amount_in = Number(parsed.amount);
    if (shift_decimals > 8) {
        amount_in = amount_in * Math.pow(10, shift_decimals - 8);
    }

    const shift_amount_in = DecimalUtil.toBN(new Decimal(amount_in), shift_decimals)

    const quote = await swapQuoteByInputToken(
        whirlpool,
        input_token_mint,
        shift_amount_in,
        default_slippage,
        ctx.program.programId,
        acountFetcher,
    );

    const quote_config = {}
    const whirlpool_data = whirlpool.getData();

    const rent_ta = async () => { return connection.getMinimumBalanceForRentExemption(AccountLayout.span) }

    const token_owner_account_a = await resolveOrCreateATA(
        connection,
        payer.publicKey,
        whirlpool_data.tokenMintA,
        rent_ta,
    );

    const token_owner_account_b = await resolveOrCreateATA(
        connection,
        payer.publicKey,
        whirlpool_data.tokenMintB,
        rent_ta,
    );

    const oracle_pda = await PDAUtil.getOracle(
        ctx.program.programId,
        whirlpool.getAddress()
    );

    quote_config["whirlpool_program"] = ORCA_WHIRLPOOL_PROGRAM_ID.toString()
    quote_config["whirlpool"] = pool
    quote_config["token_mint_a"] = whirlpool_data.tokenMintA
    quote_config["token_mint_b"] = whirlpool_data.tokenMintB
    quote_config["token_owner_account_a"] = token_owner_account_a.address
    quote_config["token_owner_account_b"] = token_owner_account_b.address
    quote_config["token_vault_a"] = whirlpool_data.tokenVaultA
    quote_config["token_vault_b"] = whirlpool_data.tokenVaultB
    quote_config["tick_array_0"] = quote.tickArray0.toString()
    quote_config["tick_array_1"] = quote.tickArray1.toString()
    quote_config["tick_array_2"] = quote.tickArray2.toString()
    quote_config["oracle"] = oracle_pda.publicKey.toString()
    quote_config["is_a_to_b"] = quote.aToB
    quote_config["amount_in"] = DecimalUtil.fromBN(quote.estimatedAmountIn)
    quote_config["estimated_amount_out"] = DecimalUtil.fromBN(quote.estimatedAmountOut)
    quote_config["min_amount_out"] = DecimalUtil.fromBN(quote.otherAmountThreshold)

    return quote_config;
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

    const quote_config = await getQuoteConfig(connection, payer, parsed);

    const bridgeToken = new PublicKey(parsed.swapDataList[0].swapSendingAssetId);
    const recipientBridgeTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, bridgeToken, recipient)).address;
    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, mint, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, mint, new PublicKey(beneficiary))).address;


    return program.methods
        .completeSoSwapNativeWithWhirlpool([...parsed.hash])
        .accounts({
            payer: tokenBridgeAccounts.payer,
            config: deriveRedeemerConfigKey(programId),
            feeConfig: deriveSoFeeConfigKey(programId),
            beneficiaryTokenAccount,
            whirlpoolProgram: quote_config["whirlpool_program"],
            whirlpoolAccount: quote_config["whirlpool"],
            whirlpoolTokenOwnerAccountA: quote_config["token_owner_account_a"],
            whirlpoolTokenVaultA: quote_config["token_vault_a"],
            whirlpoolTokenOwnerAccountB: quote_config["token_owner_account_b"],
            whirlpoolTokenVaultB: quote_config["token_vault_b"],
            whirlpoolTickArray0: quote_config["tick_array_0"],
            whirlpoolTickArray1: quote_config["tick_array_1"],
            whirlpoolTickArray2: quote_config["tick_array_2"],
            whirlpoolOracle: quote_config["oracle"],
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
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

    const recipient = new PublicKey(parsed.soReceiver);
    const recipientTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, wrappedMint, recipient)).address;
    const beneficiaryTokenAccount = (await getOrCreateAssociatedTokenAccount(connection, payer, wrappedMint, new PublicKey(beneficiary))).address;

    return program.methods
        .completeSoSwapWrappedWithWhirlpool([...parsed.hash], false)
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
