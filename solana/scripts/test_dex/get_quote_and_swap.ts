import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import {
    buildDefaultAccountFetcher,
    buildWhirlpoolClient,
    ORCA_WHIRLPOOL_PROGRAM_ID,
    swapQuoteByInputToken,
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

async function main() {
    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);
    const acountFetcher = buildDefaultAccountFetcher(connection);

    // get pool
    const sol_usdc_pool_pda = "3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd";
    const test_usdc_pool_pda = "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV";
    const SOL = {mint: new PublicKey("So11111111111111111111111111111111111111112"), decimals: 9, symbol: "SOL"};
    const USDC = {mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"), decimals: 6, symbol: "USDC"};
    const TEST = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "TEST"}

    const whirlpool = await client.getPool(test_usdc_pool_pda);

    // get swap quote
    const test_amount_in = new Decimal(10);
    const usdc_amount_in = new Decimal(10);

    const quote = await swapQuoteByInputToken(
        whirlpool,
        // TEST.mint,
        USDC.mint,
        // DecimalUtil.toBN(test_amount_in, TEST.decimals), //  (TEST to lamports)
        DecimalUtil.toBN(usdc_amount_in, USDC.decimals), //  (USDC to lamports)
        Percentage.fromFraction(10, 1000), // acceptable slippage is 1.0% (10/1000)
        ctx.program.programId,
        acountFetcher,
    );

    // print quote
    console.log("aToB", quote.aToB);
    if (quote.aToB) {
        console.log("estimatedAmountIn", DecimalUtil.fromBN(quote.estimatedAmountIn, TEST.decimals).toString(), "TEST");
        console.log("estimatedAmountOut", DecimalUtil.fromBN(quote.estimatedAmountOut, USDC.decimals).toString(), "USDC");
    } else {
        console.log("estimatedAmountIn", DecimalUtil.fromBN(quote.estimatedAmountIn, USDC.decimals).toString(), "USDC");
        console.log("estimatedAmountOut", DecimalUtil.fromBN(quote.estimatedAmountOut, TEST.decimals).toString(), "TEST");
    }

    // execute transaction
    const tx = await whirlpool.swap(quote);
    // const signature = await tx.buildAndExecute();
    // console.log("signature", signature);
    // ctx.connection.confirmTransaction(signature, "confirmed");
}

async function get_test_usdc_quote_config(
    token_mint_in: string,
    amount_in: string
) {
    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);
    const acountFetcher = buildDefaultAccountFetcher(connection);

    // get pool
    const test_usdc_pool_pda = "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV";
    // Token A
    const TEST = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "TEST"}
    // Token B
    const USDC = {mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"), decimals: 6, symbol: "USDC"};

    const whirlpool = await client.getPool(test_usdc_pool_pda);

    // acceptable slippage is 1.0% (10/1000)
    const default_slippage = Percentage.fromFraction(10, 1000);
    const input_token_mint = new PublicKey(token_mint_in)

    // get swap quote
    const shift_decimals = input_token_mint.equals(TEST.mint) ? TEST.decimals : USDC.decimals;
    const shift_amount_in = DecimalUtil.toBN(new Decimal(amount_in), shift_decimals)

    const quote = await swapQuoteByInputToken(
        whirlpool,
        input_token_mint,
        shift_amount_in,
        default_slippage,
        ctx.program.programId,
        acountFetcher,
    );

    // // print quote
    // console.log("aToB", quote.aToB);
    // let estimatedAmountIn ;
    // let estimatedAmountOut ;
    //
    // if (quote.aToB) {
    //     estimatedAmountIn = DecimalUtil.fromBN(quote.estimatedAmountIn, TEST.decimals).toString()
    //     estimatedAmountOut = DecimalUtil.fromBN(quote.estimatedAmountOut, USDC.decimals).toString()
    //
    //     console.log("estimatedAmountIn",  estimatedAmountIn, "TEST");
    //     console.log("estimatedAmountOut", estimatedAmountOut, "USDC");
    // } else {
    //     estimatedAmountIn = DecimalUtil.fromBN(quote.estimatedAmountIn, USDC.decimals).toString()
    //     estimatedAmountOut = DecimalUtil.fromBN(quote.estimatedAmountOut, TEST.decimals).toString()
    //
    //     console.log("estimatedAmountIn", estimatedAmountIn, "USDC");
    //     console.log("estimatedAmountOut", estimatedAmountOut, "TEST");
    // }

    const quote_config = {}

    const whirlpool_data = whirlpool.getData();
    quote_config["whirlpool_program"] = ORCA_WHIRLPOOL_PROGRAM_ID.toString()
    quote_config["whirlpool"] = test_usdc_pool_pda
    quote_config["token_mint_a"] = whirlpool_data.tokenMintA
    quote_config["token_mint_b"] = whirlpool_data.tokenMintB
    quote_config["token_owner_account_a"] = ""
    quote_config["token_owner_account_b"] = ""
    quote_config["token_vault_a"] = whirlpool_data.tokenVaultA
    quote_config["token_vault_b"] = whirlpool_data.tokenVaultB
    quote_config["tick_array_0"] = quote.tickArray0.toString()
    quote_config["tick_array_1"] = quote.tickArray1.toString()
    quote_config["tick_array_2"] = quote.tickArray2.toString()
    quote_config["is_a_to_b"] = quote.aToB
    quote_config["amount_in"] = DecimalUtil.fromBN(quote.estimatedAmountIn)
    quote_config["estimated_amount_out"] = DecimalUtil.fromBN(quote.estimatedAmountOut)
    quote_config["min_amount_out"] = DecimalUtil.fromBN(quote.otherAmountThreshold)

    console.log(JSON.stringify(quote_config))
}


if (process.argv[2] === "get_test_usdc_quote_config") {
    get_test_usdc_quote_config(process.argv[3], process.argv[4])
} else {
    // 默认情况下，执行 main 函数
    main();
}

/*
SAMPLE OUTPUT

$ ts-node dex_test/get_quote_and_swap.ts
wallet 4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9
aToB true
estimatedAmountIn 500 TEST
estimatedAmountOut 1.102338 USDC
signature 4DiK7S1w7pADhbAHgnF8anpGNuCg9n5C5ost7z2A8XcQtrNk69M63s1PuGCcbLdQTtYqoWSuDYKirAgJQxGqRB24

https://solscan.io/tx/4DiK7S1w7pADhbAHgnF8anpGNuCg9n5C5ost7z2A8XcQtrNk69M63s1PuGCcbLdQTtYqoWSuDYKirAgJQxGqRB24?cluster=devnet

*/