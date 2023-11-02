import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import {
  ORCA_WHIRLPOOL_PROGRAM_ID,
  PDAUtil,
  PoolUtil,
  PriceMath,
  WhirlpoolContext,
  WhirlpoolIx
} from "@orca-so/whirlpools-sdk";
import {TransactionBuilder, resolveOrCreateATA} from "@orca-so/common-sdk";
import * as prompt from "prompt";
import {Wallet} from "@coral-xyz/anchor";
import path from "path";
import fs from "fs";

// export ANCHOR_PROVIDER_URL=""
const ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
const connection = new Connection(ANCHOR_PROVIDER_URL);
const defaultPath = path.join(process.env.HOME, '.config/solana/id.json');
const rawKey = JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
const keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
const local_wallet = new Wallet(keypair);
console.log("wallet", local_wallet.publicKey.toBase58());

const ORCA_WHIRLPOOLS_CONFIG = new PublicKey("FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR");
const SOL = {mint: new PublicKey("So11111111111111111111111111111111111111112"), decimals: 9, symbol: "SOL"};
const USDC = {mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"), decimals: 6, symbol: "USDC"};
const TEST = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "TEST"}
const BSC = {mint: new PublicKey("xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"), decimals: 8, symbol: "BSC"}
const FEE_TIER_U128 = new PublicKey("G319n1BPjeXjAfheDxYe8KWZM7FQhQCJerWRK2nZYtiJ");

async function main() {
    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );

    console.log("create Whirlpool...");

    const whirlpoolsConfigPubkey = ORCA_WHIRLPOOLS_CONFIG;
    const feeTierPubkey = FEE_TIER_U128;
    const tokenMint0Pubkey = BSC.mint;
    const tokenMint1Pubkey = SOL.mint;

    const [tokenMintAAddress, tokenMintBAddress] = PoolUtil.orderMints(
        tokenMint0Pubkey,
        tokenMint1Pubkey
    );
    if (tokenMintAAddress.toString() !== tokenMint0Pubkey.toBase58()) {
        console.log("token order is inverted due to order restriction");
    }

    const tokenMintAPubkey = new PublicKey(tokenMintAAddress);
    const tokenMintBPubkey = new PublicKey(tokenMintBAddress);

    const feeTier = await ctx.fetcher.getFeeTier(feeTierPubkey);
    const tickSpacing = feeTier.tickSpacing;

    const pda = PDAUtil.getWhirlpool(
        ctx.program.programId,
        whirlpoolsConfigPubkey,
        tokenMintAPubkey,
        tokenMintBPubkey,
        tickSpacing
    );
    const tokenVaultAKeypair = Keypair.generate();
    const tokenVaultBKeypair = Keypair.generate();

    const mintA = await ctx.fetcher.getMintInfo(tokenMintAPubkey);
    const mintB = await ctx.fetcher.getMintInfo(tokenMintBPubkey);

    let initTickIndex, initPrice;
    while (true) {
        initTickIndex = Number.parseInt((await prompt.get(["initTickIndex"])).initTickIndex);
        initPrice = PriceMath.tickIndexToPrice(
            initTickIndex,
            mintA.decimals,
            mintB.decimals,
        );

        console.log(`is InitPrice ${initPrice.toFixed(6)} OK ? (if it is OK, enter OK)`);
        const ok = (await prompt.get("OK")).OK;
        if (ok === "OK") break;
    }

    const initSqrtPrice = PriceMath.tickIndexToSqrtPriceX64(initTickIndex);

    console.log(
        "setting...",
        "\n\twhirlpoolsConfig", whirlpoolsConfigPubkey.toBase58(),
        "\n\ttokenMintA", tokenMintAPubkey.toBase58(),
        "\n\ttokenMintB", tokenMintBPubkey.toBase58(),
        "\n\ttickSpacing", tickSpacing,
        "\n\tinitPrice", initPrice.toFixed(mintB.decimals), "B/A",
        "\n\ttokenVaultA(gen)", tokenVaultAKeypair.publicKey.toBase58(),
        "\n\ttokenVaultB(gen)", tokenVaultBKeypair.publicKey.toBase58(),
    );
    console.log("\nif the above is OK, enter YES");
    const yesno = (await prompt.get("yesno")).yesno;
    if (yesno !== "YES") {
        console.log("stopped");
        return;
    }

    const builder = new TransactionBuilder(ctx.connection, ctx.wallet);
    builder.addInstruction(WhirlpoolIx.initializePoolIx(
        ctx.program,
        {
            whirlpoolPda: pda,
            funder: ctx.wallet.publicKey,
            whirlpoolsConfig: whirlpoolsConfigPubkey,
            tokenMintA: tokenMintAPubkey,
            tokenMintB: tokenMintBPubkey,
            tickSpacing,
            feeTierKey: feeTierPubkey,
            tokenVaultAKeypair,
            tokenVaultBKeypair,
            initSqrtPrice,
        }));

    const sig = await builder.buildAndExecute();
    console.log("tx:", sig);
    console.log("whirlpool address:", pda.publicKey.toBase58());
}

main();

/*

SAMPLE EXECUTION LOG

wallet 4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9
create Whirlpool...
prompt: initTickIndex:  -110000
is InitPrice 0.016710 OK ? (if it is OK, enter OK)
prompt: OK:  
prompt: initTickIndex:  -150000
is InitPrice 0.000306 OK ? (if it is OK, enter OK)
prompt: OK:  
prompt: initTickIndex:  -130000
is InitPrice 0.002261 OK ? (if it is OK, enter OK)
prompt: OK:  OK
setting... 
    whirlpoolsConfig FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR 
    tokenMintA 281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS 
    tokenMintB 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU 
    tickSpacing 128 
    initPrice 0.002261 B/A 
    tokenVaultA(gen) 3dycP3pym3q6DgUpZRviaavaScwrrCuC6QyLhiLfSXge 
    tokenVaultB(gen) 969UqMJSqvgxmNuAWZx91PAnLJU825qJRAAcEVQMWASg

if the above is OK, enter YES
prompt: yesno:  YES
tx: CKS8PRSFQ1sG2vUbzdpgA7hPvARDSyhcrTdcsMCHx1Ne8D62iD5vTQfJrHR4qD57ugh2LzFBPZdQnL4rkkR1K9K
whirlpool address: b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV

*/