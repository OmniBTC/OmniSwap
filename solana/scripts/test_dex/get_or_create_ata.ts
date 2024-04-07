import {Connection, Keypair, PublicKey} from "@solana/web3.js";
import { getOrCreateAssociatedTokenAccount } from "@solana/spl-token"
import * as fs from 'fs';
import * as path from 'path';


// export ANCHOR_PROVIDER_URL=""
const ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
const ANCHOR_WALLET = process.env.ANCHOR_WALLET;

const connection = new Connection(ANCHOR_PROVIDER_URL);
const defaultPath = path.join(process.env.HOME, '.config/solana/id.json');
const rawKey = JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
const keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
async function main(mint_key: string, user_address: string) {
    let local_keypair
    if (ANCHOR_WALLET === undefined || ANCHOR_WALLET === "") {
        local_keypair = keypair;
    } else {
        const rawKey = new Uint8Array(JSON.parse(ANCHOR_WALLET));
        local_keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
    }

    const user_pubkey = new PublicKey(user_address);
    const mint_pubkey = new PublicKey(mint_key)

    const associatedTokenAccount = await getOrCreateAssociatedTokenAccount(
        connection,
        local_keypair,
        mint_pubkey,
        user_pubkey,
        false,
        "processed"
    )

    console.log(associatedTokenAccount.address.toBase58())
}

main(process.argv[2], process.argv[3]);