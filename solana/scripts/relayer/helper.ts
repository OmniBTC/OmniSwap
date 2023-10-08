import {Omniswap} from "./types/omniswap";
import IDL from "./idl/omniswap.json";
import {Program, Provider} from "@coral-xyz/anchor";
import {
    Connection,
    PublicKey,
    PublicKeyInitData,
    SystemProgram,
    SYSVAR_RENT_PUBKEY,
    TransactionInstruction
} from "@solana/web3.js";
import {ChainId, isBytes, ParsedTokenTransferVaa, parseTokenTransferVaa, SignedVaa} from "@certusone/wormhole-sdk";
import {
    CompleteTransferNativeWithPayloadCpiAccounts,
    CompleteTransferWrappedWithPayloadCpiAccounts,
    deriveAddress
} from "@certusone/wormhole-sdk/lib/cjs/solana";
import {getAssociatedTokenAddressSync, TOKEN_PROGRAM_ID,} from "@solana/spl-token";
import {
    deriveCustodyKey,
    deriveCustodySignerKey,
    deriveEndpointKey, deriveMintAuthorityKey,
    deriveRedeemerAccountKey,
    deriveTokenBridgeConfigKey, deriveWrappedMetaKey, deriveWrappedMintKey
} from "@certusone/wormhole-sdk/lib/cjs/solana/tokenBridge";
import {deriveClaimKey, derivePostedVaaKey} from "@certusone/wormhole-sdk/lib/cjs/solana/wormhole";

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
    payer: PublicKeyInitData,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: SignedVaa | ParsedTokenTransferVaa
): Promise<TransactionInstruction> {
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = isBytes(wormholeMessage)
        ? parseTokenTransferVaa(wormholeMessage)
        : wormholeMessage;

    const mint = new PublicKey(parsed.tokenAddress);

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, mint);
    const tokenBridgeAccounts = getCompleteTransferNativeWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payer,
        parsed,
        tmpTokenAccount
    );

    const recipient = new PublicKey(parsed.tokenTransferPayload.subarray(1, 33));
    const recipientTokenAccount = getAssociatedTokenAddressSync(mint, recipient);

    return program.methods
        .redeemNativeTransferWithPayload([...parsed.hash])
        .accounts({
            config: deriveRedeemerConfigKey(programId),
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            tmpTokenAccount,
            recipientTokenAccount,
            recipient,
            payerTokenAccount: getAssociatedTokenAddressSync(
                mint,
                new PublicKey(payer)
            ),
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            ...tokenBridgeAccounts,
        })
        .instruction();
}

// Temporary
export function getCompleteTransferNativeWithPayloadCpiAccounts(
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    payer: PublicKeyInitData,
    vaa: SignedVaa | ParsedTokenTransferVaa,
    toTokenAccount: PublicKeyInitData
): CompleteTransferNativeWithPayloadCpiAccounts {
    const parsed = isBytes(vaa) ? parseTokenTransferVaa(vaa) : vaa;
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
    payer: PublicKeyInitData,
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    wormholeMessage: SignedVaa | ParsedTokenTransferVaa
): Promise<TransactionInstruction> {
    const program = createHelloTokenProgramInterface(connection, programId);

    const parsed = isBytes(wormholeMessage)
        ? parseTokenTransferVaa(wormholeMessage)
        : wormholeMessage;

    const wrappedMint = deriveWrappedMintKey(
        tokenBridgeProgramId,
        parsed.tokenChain,
        parsed.tokenAddress
    );

    const tmpTokenAccount = deriveTmpTokenAccountKey(programId, wrappedMint);
    const tokenBridgeAccounts = getCompleteTransferWrappedWithPayloadCpiAccounts(
        tokenBridgeProgramId,
        wormholeProgramId,
        payer,
        parsed,
        tmpTokenAccount
    );

    const recipient = new PublicKey(parsed.tokenTransferPayload.subarray(1, 33));
    const recipientTokenAccount = getAssociatedTokenAddressSync(
        wrappedMint,
        recipient
    );

    return program.methods
        .redeemWrappedTransferWithPayload([...parsed.hash])
        .accounts({
            config: deriveRedeemerConfigKey(programId),
            foreignContract: deriveForeignContractKey(programId, parsed.emitterChain as ChainId),
            tmpTokenAccount,
            recipientTokenAccount,
            recipient,
            payerTokenAccount: getAssociatedTokenAddressSync(
                wrappedMint,
                new PublicKey(payer)
            ),
            tokenBridgeProgram: new PublicKey(tokenBridgeProgramId),
            ...tokenBridgeAccounts,
        })
        .instruction();
}

// Temporary
export function getCompleteTransferWrappedWithPayloadCpiAccounts(
    tokenBridgeProgramId: PublicKeyInitData,
    wormholeProgramId: PublicKeyInitData,
    payer: PublicKeyInitData,
    vaa: SignedVaa | ParsedTokenTransferVaa,
    toTokenAccount: PublicKeyInitData
): CompleteTransferWrappedWithPayloadCpiAccounts {
    const parsed = isBytes(vaa) ? parseTokenTransferVaa(vaa) : vaa;
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
