import {Omniswap} from "./types/omniswap";
import IDL from "./idl/omniswap.json";
import {Program, Provider} from "@coral-xyz/anchor";
import {ASSOCIATED_TOKEN_PROGRAM_ID, getOrCreateAssociatedTokenAccount, TOKEN_PROGRAM_ID} from "@solana/spl-token"
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

export class PersistentDictionary {
    private data: Record<string, any>;
    private filename: string;

    constructor(filename: string) {
        const directory = path.dirname(filename);
        if (!fs.existsSync(directory)) {
            fs.mkdirSync(directory, { recursive: true });
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

export interface ParsedOmniswapPayload extends ParsedTokenTransferVaa, WormholeData {
}


export function parseVaaToWormholePayload(vaa: Buffer): ParsedOmniswapPayload {
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
    // index += len;

    return {
        dstMaxGasPrice: dstMaxGasPrice,
        dstMaxGas: dstMaxGas,
        soTransactionId,
        soReceiver,
        soReceivingAssetId,
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

export async function createRedeemNativeTransferWithPayloadInstruction(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = parseVaaToWormholePayload(wormholeMessage);

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

    return program.methods
        .redeemNativeTransferWithPayload([...parsed.hash])
        .accounts({
            payer: tokenBridgeAccounts.payer,
            payerTokenAccount: (await getOrCreateAssociatedTokenAccount(
                connection,
                payer,
                mint,
                new PublicKey(payAddress)
            )).address,
            config: deriveRedeemerConfigKey(programId),
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            mint,
            recipientTokenAccount,
            recipient,
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
            rent: tokenBridgeAccounts.rent
        })
        .instruction();
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

export async function createRedeemWrappedTransferWithPayloadInstruction(
    connection: Connection,
    programId: PublicKeyInitData,
    payer: Keypair,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: Buffer
): Promise<TransactionInstruction> {
    const payAddress = payer.publicKey.toString();
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = parseVaaToWormholePayload(wormholeMessage);

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

    return program.methods
        .redeemWrappedTransferWithPayload([...parsed.hash])
        .accounts({
            payer: tokenBridgeAccounts.payer,
            payerTokenAccount: (await getOrCreateAssociatedTokenAccount(
                connection,
                payer,
                wrappedMint,
                new PublicKey(payer)
            )).address,
            config: deriveRedeemerConfigKey(programId),
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            tokenBridgeWrappedMint: tokenBridgeAccounts.tokenBridgeWrappedMint,
            recipientTokenAccount: (await getOrCreateAssociatedTokenAccount(
                connection,
                payer,
                wrappedMint,
                recipient
            )).address,
            recipient,
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
            associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
            rent: tokenBridgeAccounts.rent
        })
        .instruction();
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
