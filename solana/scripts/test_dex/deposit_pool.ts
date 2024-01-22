import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import {
    buildWhirlpoolClient,
    IncreaseLiquidityInput,
    increaseLiquidityQuoteByInputToken,
    ORCA_WHIRLPOOL_PROGRAM_ID,
    PDAUtil,
    PriceMath,
    Whirlpool,
    WhirlpoolContext
} from "@orca-so/whirlpools-sdk";
import {DecimalUtil, Percentage} from "@orca-so/common-sdk";
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

export interface TokenDefinition {
    symbol: string,
    mint: PublicKey,
    decimals: number,
}

interface IncreaseLiquidityQuote {
    lower_tick_index: number,
    upper_tick_index: number,
    quote: IncreaseLiquidityInput
}

function get_increase_liquidity_quote(
    whirlpool: Whirlpool,
    lower_price: Decimal,
    upper_price: Decimal,
    token_input: TokenDefinition,
    amount_in: Decimal,
    acceptable_slippage: Decimal,
    token_a: TokenDefinition,
    token_b: TokenDefinition,
): IncreaseLiquidityQuote {
    const whirlpool_data = whirlpool.getData();
    //const token_a = whirlpool.getTokenAInfo();
    //const token_b = whirlpool.getTokenBInfo(); // waiting for bugfix
    const tick_spacing = whirlpool_data.tickSpacing;

    console.log("mint", token_a.mint.toBase58(), token_b.mint.toBase58());
    console.log("decimals", token_a.decimals, token_b.decimals);

    const lower_tick_index = PriceMath.priceToInitializableTickIndex(lower_price, token_a.decimals, token_b.decimals, tick_spacing);
    const upper_tick_index = PriceMath.priceToInitializableTickIndex(upper_price, token_a.decimals, token_b.decimals, tick_spacing);
    console.log("lower & upper tick_index", lower_tick_index, upper_tick_index);

    // get quote
    const quote = increaseLiquidityQuoteByInputToken(
        token_input.mint,
        amount_in,
        lower_tick_index,
        upper_tick_index,
        Percentage.fromDecimal(acceptable_slippage),
        whirlpool
    );

    console.log("tokenA max input", DecimalUtil.fromBN(quote.tokenMaxA, token_a.decimals).toString());
    console.log("tokenB max input", DecimalUtil.fromBN(quote.tokenMaxB, token_b.decimals).toString());
    console.log("liquidity", quote.liquidityAmount.toString());
    return {lower_tick_index, upper_tick_index, quote};
}

async function open_position(
    ctx: WhirlpoolContext,
    whirlpool: Whirlpool,
    quote: IncreaseLiquidityQuote,
) {
    // get tx
    const {positionMint: position_mint, tx} = await whirlpool.openPosition(
        quote.lower_tick_index,
        quote.upper_tick_index,
        quote.quote
    );

    // execute transaction
    const signature = await tx.buildAndExecute();
    console.log("open_position signature", signature);
    console.log("position NFT", position_mint.toBase58());
    await ctx.connection.confirmTransaction(signature);
}

async function main() {
    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);

    const ORCA_WHIRLPOOLS_CONFIG = new PublicKey("FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR");
    const SOL = {mint: new PublicKey("So11111111111111111111111111111111111111112"), decimals: 9, symbol: "SOL"};
    const USDC = {mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"), decimals: 6, symbol: "USDC"};
    const BSC = {mint: new PublicKey("xxtdhpCgop5gZSeCkRRHqiVu7hqEC9MKkd1xMRUZqrz"), decimals: 8, symbol: "BSC"}
    const TEST = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "TEST"}
    const tickSpacing = 128;

    // get pool
    const pool_pda = PDAUtil.getWhirlpool(
        ctx.program.programId,
        ORCA_WHIRLPOOLS_CONFIG,
        SOL.mint,
        USDC.mint,
        tickSpacing
    ).publicKey;

    console.log("pool_pda", pool_pda.toBase58());

    const whirlpool = await client.getPool(pool_pda);

    // deposit usdc
    const quote = get_increase_liquidity_quote(
        whirlpool,
        new Decimal(100),
        new Decimal(10000), // price range
        SOL, // input token
        new Decimal(0.001 ),  // est input token
        new Decimal(10),        // slippage
        SOL,  // tokenA
        USDC, // tokenB
    );


    await open_position(ctx, whirlpool, quote);
}

main();

/*
SAMPLE OUTPUT:

$ ts-node dex_test/deposit_pool.ts
wallet 4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9
pool_pda b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV
mint 281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
decimals 9 6
lower & upper tick_index -135168 -123904
InRange
tokenA max input 5004.999999991
tokenB max input 9.811571
liquidity 28622479977
open_position signature 3xfQR3tWWuVYUwb5dJmBGqBop8TPRub9N6UgiaGtrViEwC9m7ASozkQ1Y2XZXjsU9icqbKdfcokzzQLZdfnQeaoZ
position NFT F6RF5FzPjNQs9b18A1Lvd7G7xA68m8oQZSw4CzMxkAtE


https://solscan.io/tx/3xfQR3tWWuVYUwb5dJmBGqBop8TPRub9N6UgiaGtrViEwC9m7ASozkQ1Y2XZXjsU9icqbKdfcokzzQLZdfnQeaoZ?cluster=devnet
*/
