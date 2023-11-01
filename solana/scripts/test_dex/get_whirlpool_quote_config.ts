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
const ANCHOR_WALLET = process.env.ANCHOR_WALLET;
const connection = new Connection(ANCHOR_PROVIDER_URL);

const defaultPath = path.join(process.env.HOME, '.config/solana/id.json');
const rawKey = JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
const keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
const default_wallet = new Wallet(keypair);

const rent_ta = async () => { return connection.getMinimumBalanceForRentExemption(AccountLayout.span) }

async function main(
    whirlpool_address: string,
    token_mint_in: string,
    amount_in: string
) {
    let local_wallet
    if (ANCHOR_WALLET === undefined || ANCHOR_WALLET === "") {
        local_wallet = default_wallet;
    } else {
        const rawKey = new Uint8Array(JSON.parse(ANCHOR_WALLET));
        const keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
        local_wallet = new Wallet(keypair);
    }

    const ctx = WhirlpoolContext.from(
        connection,
        local_wallet,
        ORCA_WHIRLPOOL_PROGRAM_ID
    );
    const client = buildWhirlpoolClient(ctx);
    const acountFetcher = buildDefaultAccountFetcher(connection);

    const whirlpool = await client.getPool(whirlpool_address);
    const token_a = whirlpool.getTokenAInfo();
    const token_b = whirlpool.getTokenBInfo();

    // acceptable slippage is 1.0% (10/1000)
    const default_slippage = Percentage.fromFraction(10, 1000);
    const input_token_mint = new PublicKey(token_mint_in);

    // get swap quote
    const shift_decimals = input_token_mint.equals(token_a.mint) ? token_a.decimals : token_b.decimals;
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
    //     estimatedAmountIn = DecimalUtil.fromBN(quote.estimatedAmountIn, token_a.decimals).toString()
    //     estimatedAmountOut = DecimalUtil.fromBN(quote.estimatedAmountOut, token_b.decimals).toString()
    //
    //     console.log("estimatedAmountIn",  estimatedAmountIn, "TokenA");
    //     console.log("estimatedAmountOut", estimatedAmountOut, "TokenB");
    // } else {
    //     estimatedAmountIn = DecimalUtil.fromBN(quote.estimatedAmountIn, token_b.decimals).toString()
    //     estimatedAmountOut = DecimalUtil.fromBN(quote.estimatedAmountOut, token_a.decimals).toString()
    //
    //     console.log("estimatedAmountIn", estimatedAmountIn, "TokenB");
    //     console.log("estimatedAmountOut", estimatedAmountOut, "TokenA");
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
    quote_config["whirlpool"] = whirlpool_address
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

main(process.argv[2], process.argv[3], process.argv[4]);

/*
SAMPLE OUTPUT

$ ts-node scripts/test_dex/get_whirlpool_quote_config.ts b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV 281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS 100
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
  "tick_array_1": "CXmxVvENVutfAmmHUSVNatgcidiu26uSXuCK8ufvqfxp",
  "tick_array_2": "CXmxVvENVutfAmmHUSVNatgcidiu26uSXuCK8ufvqfxp",
  "oracle": "44xQG1Fgv5k3Us1s5Mcg6MQiQV2oSeocBRwo7hZvKdRo",
  "is_a_to_b": true,
  "amount_in": "100000000000",
  "estimated_amount_out": "210498",
  "min_amount_out": "208413"
}

*/