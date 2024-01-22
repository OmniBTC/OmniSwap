"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const wormhole_sdk_1 = require("@certusone/wormhole-sdk");
const web3_js_1 = require("@solana/web3.js");
const path_1 = __importDefault(require("path"));
const fs_1 = __importDefault(require("fs"));
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        const connection = new web3_js_1.Connection("https://sparkling-wild-hexagon.solana-devnet.discover.quiknode.pro/2129a56170ae922c0d50ec36a09a6f683ab5a466/", "processed");
        const defaultPath = path_1.default.join(process.env.HOME, ".config/solana/id.json");
        const rawKey = JSON.parse(fs_1.default.readFileSync(defaultPath, "utf-8"));
        const wallet = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey));
        const payerAddress = wallet.publicKey.toString();
        const SOL_BRIDGE_ADDRESS = "3u8hJUVTA4jH1wYAyUur7FFZVQ8H635K3tSHHF4ssjQ5";
        const signedVAA = "01000000000100081b53f79da4b1b12dbfaee9ce88a1ec7f4b51cfb38832e9ae37da238f5be26b08fd93d573d500f7974bc463e7cbaa6fc2a3661591567c3c2ec72f52c5354f98006511d13900000000001540440411a170b4842ae7dee4f4a7b7a58bc0a98566e998850a7bb87bf5dc05b9000000000000007a000300000000000000000000000000000000000000000000000000000002540be400bda28aeb93874baba2273db9c92fb7b7fe2f412352e9633c0258978a32620a230015ceda17841d79db34bd17721d2024343b5d9dd0320626958e10f4cf3d800a719e000135fbfedfe4ba06b311b86ae1d2064e08e583e6d550524307fc626648c4718c0c0138e121709ad96bd37a2f87022932336e9a290f62aef3d41dae00b1547c6f1938";
        yield (0, wormhole_sdk_1.postVaaSolana)(connection, (transaction) => __awaiter(this, void 0, void 0, function* () {
            transaction.partialSign(wallet);
            return transaction;
        }), SOL_BRIDGE_ADDRESS, payerAddress, Buffer.from(signedVAA, "hex"));
        console.log("payer: ", payerAddress);
    });
}
// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
