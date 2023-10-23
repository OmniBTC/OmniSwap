import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import {
    buildDefaultAccountFetcher,
    buildWhirlpoolClient,
    ORCA_WHIRLPOOL_PROGRAM_ID, PDAUtil,
    swapQuoteByInputToken,
    WhirlpoolContext
} from "@orca-so/whirlpools-sdk";
import {DecimalUtil, Percentage, resolveOrCreateATA} from "@orca-so/common-sdk";
import {AccountLayout} from "@solana/spl-token";

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

const rent_ta = async () => { return connection.getMinimumBalanceForRentExemption(AccountLayout.span) }

async function main(
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
    const input_token_mint = new PublicKey(token_mint_in);

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

    const token_owner_account_a = await resolveOrCreateATA(
        connection,
        local_wallet.publicKey,
        whirlpool_data.tokenMintA,
        rent_ta,
    );

    const token_owner_account_b = await resolveOrCreateATA(
        connection,
        local_wallet.publicKey,
        whirlpool_data.tokenMintB,
        rent_ta,
    );

    const oracle_pda = await PDAUtil.getOracle(
        ctx.program.programId,
        whirlpool.getAddress()
    );

    quote_config["whirlpool_program"] = ORCA_WHIRLPOOL_PROGRAM_ID.toString()
    quote_config["whirlpool"] = test_usdc_pool_pda
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

    console.log(JSON.stringify(quote_config, null, 2))
}

main(process.argv[2], process.argv[3]);

/*
SAMPLE OUTPUT

$ ts-node dex_test/get_test_usdc_quote_config.ts 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU 10
{
  "whirlpool_program": "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
  "whirlpool": "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV",
  "token_mint_a": "281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS",
  "token_mint_b": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
  "token_owner_account_a": "7CxzRURXNEYJU5D2oqFdtg25RcVLkwCbaNJnC8RXZwEP",
  "token_owner_account_b": "68DjnBuZ6UtM6dGoTGhu2rqV5ZSowsPGgv2AWD1xuGB4",
  "token_vault_a": "3dycP3pym3q6DgUpZRviaavaScwrrCuC6QyLhiLfSXge",
  "token_vault_b": "969UqMJSqvgxmNuAWZx91PAnLJU825qJRAAcEVQMWASg",
  "tick_array_0": "CXmxVvENVutfAmmHUSVNatgcidiu26uSXuCK8ufvqfxp",
  "tick_array_1": "A3hkPb9EgHCTY6QiduwCLojmY9HzMBZW5LXANqSUYmgk",
  "tick_array_2": "A3hkPb9EgHCTY6QiduwCLojmY9HzMBZW5LXANqSUYmgk",
  "oracle": "44xQG1Fgv5k3Us1s5Mcg6MQiQV2oSeocBRwo7hZvKdRo",
  "is_a_to_b": false,
  "amount_in": "10000000",
  "estimated_amount_out": "3708721560268",
  "min_amount_out": "3672001544819"
}

*/