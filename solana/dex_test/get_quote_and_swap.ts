import {Connection, PublicKey} from "@solana/web3.js";
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

// export ANCHOR_PROVIDER_URL=""
const ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
const connection = new Connection(ANCHOR_PROVIDER_URL);
const local_wallet = Wallet.local();
console.log("wallet", local_wallet.publicKey.toBase58());

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
    const MYCOIN = {mint: new PublicKey("281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS"), decimals: 9, symbol: "MYCOIN"}

    const whirlpool = await client.getPool(test_usdc_pool_pda);

    // get swap quote
    const mycoin_amount_in = new Decimal(10);
    const usdc_amount_in = new Decimal(1);

    const quote = await swapQuoteByInputToken(
        whirlpool,
        MYCOIN.mint,
        // USDC.mint,
        DecimalUtil.toBN(mycoin_amount_in, MYCOIN.decimals), //  (MYCOIN to lamports)
        // DecimalUtil.toBN(usdc_amount_in, USDC.decimals), //  (USDC to lamports)
        Percentage.fromFraction(10, 1000), // acceptable slippage is 1.0% (10/1000)
        ctx.program.programId,
        acountFetcher,
    );

    // print quote
    console.log("aToB", quote.aToB);
    if (quote.aToB) {
        console.log("estimatedAmountIn", DecimalUtil.fromBN(quote.estimatedAmountIn, MYCOIN.decimals).toString(), "MYCOIN");
        console.log("estimatedAmountOut", DecimalUtil.fromBN(quote.estimatedAmountOut, USDC.decimals).toString(), "USDC");
    } else {
        console.log("estimatedAmountIn", DecimalUtil.fromBN(quote.estimatedAmountIn, USDC.decimals).toString(), "USDC");
        console.log("estimatedAmountOut", DecimalUtil.fromBN(quote.estimatedAmountOut, MYCOIN.decimals).toString(), "MYCOIN");
    }

    // execute transaction
    const tx = await whirlpool.swap(quote);
    const signature = await tx.buildAndExecute();
    console.log("signature", signature);
    ctx.connection.confirmTransaction(signature, "confirmed");
}

main();

/*
SAMPLE OUTPUT

$ ts-node dex_test/get_quote_and_swap.ts
wallet 4q2wPZMys1zCoAVpNmhgmofb6YM9MqLXmV25LdtEMAf9
aToB true
estimatedAmountIn 500 MYCOIN
estimatedAmountOut 1.102338 USDC
signature 4DiK7S1w7pADhbAHgnF8anpGNuCg9n5C5ost7z2A8XcQtrNk69M63s1PuGCcbLdQTtYqoWSuDYKirAgJQxGqRB24

https://solscan.io/tx/4DiK7S1w7pADhbAHgnF8anpGNuCg9n5C5ost7z2A8XcQtrNk69M63s1PuGCcbLdQTtYqoWSuDYKirAgJQxGqRB24?cluster=devnet

*/