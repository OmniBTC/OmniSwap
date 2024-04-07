import { postVaaSolana } from "@certusone/wormhole-sdk";
import { Connection, Keypair } from "@solana/web3.js";
import path from "path";
import fs from "fs";


// export ANCHOR_PROVIDER_URL=""
const ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
const ANCHOR_WALLET = process.env.ANCHOR_WALLET;

const defaultPath = path.join(process.env.HOME, '.config/solana/id.json');
const rawKey = JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
const keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
async function main(
    wormhole_program: string,
    signed_vaa: string
) {
    let local_keypair
    if (ANCHOR_WALLET === undefined || ANCHOR_WALLET === "") {
        local_keypair = keypair;
    } else {
        const rawKey = new Uint8Array(JSON.parse(ANCHOR_WALLET));
        local_keypair = Keypair.fromSecretKey(Uint8Array.from(rawKey));
    }

    const resp = await postVaaSolana(
        new Connection(ANCHOR_PROVIDER_URL, "processed"),
        async (transaction) => {
            transaction.partialSign(local_keypair);
            return transaction;
        },
        wormhole_program,
        local_keypair.publicKey.toString(),
        Buffer.from(signed_vaa, "hex")
    );

    console.log("LegacyVerifySignatures: ", resp[0].signature)
    console.log("LegacyPostVaa:", resp[1].signature)
}

main(process.argv[2], process.argv[3]);