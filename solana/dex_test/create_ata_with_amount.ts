import { PublicKey } from "@solana/web3.js";
import { getAssociatedTokenAddressSync } from "@solana/spl-token";
import * as fs from "fs";
import BN from "bn.js";

const ATA_JSON_TEMPLATE = '{"account":{"data":["bSzl7WjOignQep8J48sLWXRN+yidilz09ipUuZGo1wAMjph4T4MwT0YUgNeGtHvaBFkU0iG0rHd0ApevtnFTNQEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","base64"],"executable":false,"lamports":2039280,"owner":"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA","rentEpoch":0},"pubkey":"GbMB98t6YfVxn3Pbu54EyUkuLqdaERLANvyghtrzSf6e"}';

// usage: ts-node create_ata_with_amount <mint> <owner> <decimals> <amount>
function main() {
  const mint = process.argv[2];
  const mintPubkey = new PublicKey(mint);
  const owner = process.argv[3];
  const ownerPubkey = new PublicKey(owner);
  const decimals = parseInt(process.argv[4]);
  const amount = parseInt(process.argv[5]);

  const amountU64 = new BN(amount).mul(new BN(10).pow(new BN(decimals)));

  const ataPubkey = getAssociatedTokenAddressSync(mintPubkey, ownerPubkey);

  const ataJson = JSON.parse(ATA_JSON_TEMPLATE);
  ataJson.pubkey = ataPubkey.toBase58();
  const ataBuffer = Buffer.from(ataJson.account.data[0], "base64");
  ataBuffer.set(mintPubkey.toBuffer(), 0);
  ataBuffer.set(ownerPubkey.toBuffer(), 32);
  ataBuffer.set(amountU64.toBuffer("le", 8), 64);
  ataJson.account.data[0] = ataBuffer.toString("base64");

  fs.writeFileSync(`${ataPubkey.toBase58()}.json`, JSON.stringify(ataJson, null, 0));  
}

main();