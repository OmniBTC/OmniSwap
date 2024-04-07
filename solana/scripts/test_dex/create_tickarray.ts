import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import {
  ORCA_WHIRLPOOL_PROGRAM_ID,
  PDAUtil,
  PriceMath,
  TICK_ARRAY_SIZE,
  TickUtil,
  WhirlpoolContext,
  WhirlpoolIx
} from "@orca-so/whirlpools-sdk";
import {PDA, TransactionBuilder} from "@orca-so/common-sdk";
import * as prompt from "prompt";
import Decimal from "decimal.js";
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
const BSC = {mint: new PublicKey("xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"), decimals: 8, symbol: "BSC"}
const TEST = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "TEST"}
const tickSpacing = 128;

async function main() {
    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );

    console.log("create TickArray...");

    const pool_pda = PDAUtil.getWhirlpool(
        ctx.program.programId,
        ORCA_WHIRLPOOLS_CONFIG,
        SOL.mint,
        USDC.mint,
        tickSpacing
    ).publicKey;

    console.log("pool_pda", pool_pda.toBase58());

    const whirlpool = await ctx.fetcher.getPool(pool_pda);
    const mintA = await ctx.fetcher.getMintInfo(whirlpool.tokenMintA);
    const mintB = await ctx.fetcher.getMintInfo(whirlpool.tokenMintB);

    type TickArrayInfo = {
        pda: PDA,
        startTickIndex: number,
        startPrice: Decimal,
        endPrice: Decimal,
        isCurrent: boolean,
        isInitialized?: boolean,
    }

    const neighboringTickArrayInfos: TickArrayInfo[] = [];
    for (let offset = -6; offset <= +6; offset++) {
        const startTickIndex = TickUtil.getStartTickIndex(whirlpool.tickCurrentIndex, tickSpacing, offset);
        const pda = PDAUtil.getTickArray(ctx.program.programId, pool_pda, startTickIndex);
        const endTickIndex = startTickIndex + tickSpacing * TICK_ARRAY_SIZE;
        const startPrice = PriceMath.tickIndexToPrice(startTickIndex, mintA.decimals, mintB.decimals);
        const endPrice = PriceMath.tickIndexToPrice(endTickIndex, mintA.decimals, mintB.decimals);

        neighboringTickArrayInfos.push({
            pda,
            startTickIndex,
            startPrice,
            endPrice,
            isCurrent: offset == 0,
        });
    }

    const checkInitialized = await ctx.fetcher.getTickArrays(
        neighboringTickArrayInfos.map((info) => info.pda.publicKey),
    );
    checkInitialized.forEach((ta, i) => neighboringTickArrayInfos[i].isInitialized = !!ta);

    console.log("neighring tickarrays...");
    neighboringTickArrayInfos.forEach((ta) => console.log(
        ta.isCurrent ? ">>" : "  ",
        ta.pda.publicKey.toBase58().padEnd(45, " "),
        ta.isInitialized ? "    initialized" : "NOT INITIALIZED",
        "start", ta.startTickIndex.toString().padStart(10, " "),
        "covered range", ta.startPrice.toFixed(mintB.decimals), "-", ta.endPrice.toFixed(mintB.decimals),
    ));

    const select = await prompt.get(["tickArrayPubkey"]);
    const tickArrayPubkey = new PublicKey(select.tickArrayPubkey);
    const which = neighboringTickArrayInfos.filter((ta) => ta.pda.publicKey.equals(tickArrayPubkey))[0];

    const builder = new TransactionBuilder(ctx.connection, ctx.wallet);
    builder.addInstruction(WhirlpoolIx.initTickArrayIx(
        ctx.program,
        {
            funder: ctx.wallet.publicKey,
            whirlpool: pool_pda,
            startTick: which.startTickIndex,
            tickArrayPda: which.pda,
        }));

    const sig = await builder.buildAndExecute();
    console.log("tx:", sig);
    console.log("initialized tickArray address:", tickArrayPubkey.toBase58());
}

main();

/*

SAMPLE EXECUTION LOG
$ ts-node dex_test/create_tickarray.ts
wallet 4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9
create TickArray...
sol_usdc_pool_pda 3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd
neighring tickarrays...
   9z2trMyPEzooFKznKJ2DGtKbS46TZc8wAcE7yJT4jJho  NOT INITIALIZED start     -67584 covered range 1.161477 - 3.582413
   Hh78d6h4uqDQaMxCyLB9CoDHmBiU9VpcDr5RYcYCYV33  NOT INITIALIZED start     -56320 covered range 3.582413 - 11.049448
   CxNYCVtgf725K3vWgYWHRi3zW3nsw5EWDTgwpSmbMCRw  NOT INITIALIZED start     -45056 covered range 11.049448 - 34.080460
   6D4rupXqDz58EmK8rW66uwCHmKW4Sj5dhAst697iVSx       initialized start     -33792 covered range 34.080460 - 105.116358
   6R1vSHAU7z2erkdyLxBbB7pz3ouH4YBa6unpw6qn576s      initialized start     -22528 covered range 105.116358 - 324.216530
   4VtMPANnJPYAGzQvAUYt5iqPGU2e2e1ocCkyggVye2MJ      initialized start     -11264 covered range 324.216530 - 999.999999
>> 8t5izcQTgegkwLQwUmVxAgmf7Q7yxcsabrC3WDb9tGvd      initialized start          0 covered range 999.999999 - 3084.358468
   A2yU1ThpKGqbucshh9RwpjjvEzdnMsR3mYdjCif7PAQu      initialized start      11264 covered range 3084.358468 - 9513.267160
   ERC4Q2gh5xFeu2HbQKsNSqaNqixyVzLup11By7kd1Xfb  NOT INITIALIZED start      22528 covered range 9513.267160 - 29342.326124
   9AS7Eyx8UaS2w4G3L7gruPKPrTJ2P5VP4g11RUDQjnvp  NOT INITIALIZED start      33792 covered range 29342.326124 - 90502.252058
   BaHasMcNYTdRRLTEUx5VBYXAnqxVFB6fSC9witshLakw  NOT INITIALIZED start      45056 covered range 90502.252058 - 279141.387522
   4YKpTmdFhBb2LwrfhfHD95LGZW7qphMpcJJVp5vaEUJc  NOT INITIALIZED start      56320 covered range 279141.387522 - 860972.102414
   H159wLaVHKAeMvU8QefVz8NxETBiRfVg9AF5NFFkZg7K  NOT INITIALIZED start      67584 covered range 860972.102414 - 2655546.594922
prompt: tickArrayPubkey:  ERC4Q2gh5xFeu2HbQKsNSqaNqixyVzLup11By7kd1Xfb
tx: 5mkPcVKoGouCdUtkN6BCtAudg2Rqn46EBXCTEDAQAmTJJwM13i6TaZThpa7AmXUfRKjNiaYNp9F23Q2DUHuaisC4
initialized tickArray address: ERC4Q2gh5xFeu2HbQKsNSqaNqixyVzLup11By7kd1Xfb

*/