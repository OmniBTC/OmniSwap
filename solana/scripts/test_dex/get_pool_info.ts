import {Connection, PublicKey} from "@solana/web3.js";
import {buildDefaultAccountFetcher, ORCA_WHIRLPOOL_PROGRAM_ID, PDAUtil} from "@orca-so/whirlpools-sdk";

const ORCA_WHIRLPOOLS_CONFIG = new PublicKey("FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR");
const SOL = {mint: new PublicKey("So11111111111111111111111111111111111111112"), decimals: 9, symbol: "SOL"};
const USDC = {mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"), decimals: 6, symbol: "USDC"};
const tickSpacing = 128;

const sol_usdc_pool_pda = "3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd";
const test_usdc_pool_pda = "b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV";
const bsc_test_pool_pda = "AxoxjuJnpvTeqmwwjJLnuMuYLGNP1kg3orMjSuj3KBmc"
const sol_bsc_pool_pda = "6TLSV3E9aTNzJtY4DejLdhGb4wkTfM65gA3cwMESFrpY"

function get_sol_usdc_pool() {
    const SOL_USDC_128_PDA = PDAUtil.getWhirlpool(
        ORCA_WHIRLPOOL_PROGRAM_ID,
        ORCA_WHIRLPOOLS_CONFIG,
        SOL.mint,
        USDC.mint,
        tickSpacing
    ).publicKey;
    console.log("address", SOL_USDC_128_PDA.toBase58());

    return SOL_USDC_128_PDA
}

async function main() {
    // export ANCHOR_PROVIDER_URL=""
    const ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
    const connection = new Connection(ANCHOR_PROVIDER_URL);

    const acountFetcher = buildDefaultAccountFetcher(connection);
    const pool = await acountFetcher.getPool(
        sol_usdc_pool_pda
    );
    console.log("sol_usdc_pool", pool);
}

main();

/*
SAMPLE EXECUTION LOG

$ ts-node dex_test/get_pool_info.ts
address 3kWvtnrDnxesGYFy86mNs14S1oUQmB2X175SrT94bvzd
sol_usdc_pool {
  whirlpoolsConfig: PublicKey [PublicKey(FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR)] {
    _bn: <BN: d9336a3df48f361e5706e69c3cb6b6d91774e47935c8526de5a0f59f215a236a>
  },
  whirlpoolBump: [ 254 ],
  tickSpacing: 128,
  tickSpacingSeed: [ 128, 0 ],
  feeRate: 4000,
  protocolFeeRate: 300,
  liquidity: <BN: 0>,
  sqrtPrice: <BN: 10000000000000000>,
  tickCurrentIndex: 0,
  protocolFeeOwedA: <BN: 0>,
  protocolFeeOwedB: <BN: 0>,
  tokenMintA: PublicKey [PublicKey(So11111111111111111111111111111111111111112)] {
    _bn: <BN: 69b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f00000000001>
  },
  tokenVaultA: PublicKey [PublicKey(G6rs95KiZxNekVNgKeGLBNB7fbzky8RGSauJ9CcGqw2j)] {
    _bn: <BN: e05f9702196468204784b2632cda5e732b5956c19de74887485ab959db5f540c>
  },
  feeGrowthGlobalA: <BN: 0>,
  tokenMintB: PublicKey [PublicKey(4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU)] {
    _bn: <BN: 3b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7>
  },
  tokenVaultB: PublicKey [PublicKey(C3YnZddhChWqZaFLTRNzoziHs2GoyMh2dhPVk8mJQRVP)] {
    _bn: <BN: a417a869602877018b5bbfc45bc9dfb914f86a726114bfb8d405a1921e3a8836>
  },
  feeGrowthGlobalB: <BN: 0>,
  rewardLastUpdatedTimestamp: <BN: 0>,
  rewardInfos: [
    {
      mint: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      vault: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      authority: [PublicKey [PublicKey(3otH3AHWqkqgSVfKFkrxyDqd2vK6LcaqigHrFEmWcGuo)]],
      emissionsPerSecondX64: <BN: 0>,
      growthGlobalX64: <BN: 0>
    },
    {
      mint: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      vault: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      authority: [PublicKey [PublicKey(3otH3AHWqkqgSVfKFkrxyDqd2vK6LcaqigHrFEmWcGuo)]],
      emissionsPerSecondX64: <BN: 0>,
      growthGlobalX64: <BN: 0>
    },
    {
      mint: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      vault: [PublicKey [PublicKey(11111111111111111111111111111111)]],
      authority: [PublicKey [PublicKey(3otH3AHWqkqgSVfKFkrxyDqd2vK6LcaqigHrFEmWcGuo)]],
      emissionsPerSecondX64: <BN: 0>,
      growthGlobalX64: <BN: 0>
    }
  ]
}
*/
