import { postVaaSolana } from "@certusone/wormhole-sdk";
import { Connection, Keypair } from "@solana/web3.js";
import path from "path";
import fs from "fs";
import {assert} from "chai";


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

    const tx = await postVaaSolana(
        new Connection(ANCHOR_PROVIDER_URL, "processed"),
        async (transaction) => {
            transaction.partialSign(local_keypair);
            return transaction;
        },
        wormhole_program,
        local_keypair.publicKey.toString(),
        Buffer.from(signed_vaa, "hex")
    );

}

main(
    "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5",
    "01000000000100b0ebb8232182198b50246f7ba2d2bbcfe2ccb029757bc5261ccc35e4190590d209d9d58ee6a0594e117743baead5bbcfa4bb82f8b13fb3ced1585d12ba4c57b000653795ba0000000000040000000000000000000000009dcf9d205c9de35334d646bee44b2d2859712a0900000000000013ac0f0300000000000000000000000000000000000000000000000000000000000f42403b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea70001dc3779efc394bf8f4ddc09c41bad9f8aae8345431d4b17a20b99c9ac209c2a80000100000000000000000000000084b7ca95ac91f8903acb08b27f5b41a4de2dc0fc010102deac20493294b88e30b66848a5977de2a6a10001e8031bdd3682a07005e6674b7d69cc2038e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938203b442cb3912157f13a933d0134282d032b5ffecd01a2dbf1b7790608df002ea7"
);