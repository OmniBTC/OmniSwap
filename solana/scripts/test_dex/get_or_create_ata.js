"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
exports.__esModule = true;
var web3_js_1 = require("@solana/web3.js");
var spl_token_1 = require("@solana/spl-token");
var fs = __importStar(require("fs"));
var path = __importStar(require("path"));
// export ANCHOR_PROVIDER_URL=""
var ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
var ANCHOR_WALLET = process.env.ANCHOR_WALLET;
var connection = new web3_js_1.Connection(ANCHOR_PROVIDER_URL);
var defaultPath = path.join(process.env.HOME, '.config/solana/id.json');
var rawKey = JSON.parse(fs.readFileSync(defaultPath, 'utf-8'));
var keypair = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey));
function main(mint_key, user_address) {
    return __awaiter(this, void 0, void 0, function () {
        var local_keypair, rawKey_1, user_pubkey, mint_pubkey, associatedTokenAccount;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (ANCHOR_WALLET === undefined || ANCHOR_WALLET === "") {
                        local_keypair = keypair;
                    }
                    else {
                        rawKey_1 = new Uint8Array(JSON.parse(ANCHOR_WALLET));
                        local_keypair = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey_1));
                    }
                    user_pubkey = new web3_js_1.PublicKey(user_address);
                    mint_pubkey = new web3_js_1.PublicKey(mint_key);
                    return [4 /*yield*/, (0, spl_token_1.getOrCreateAssociatedTokenAccount)(connection, local_keypair, mint_pubkey, user_pubkey, false, "processed")];
                case 1:
                    associatedTokenAccount = _a.sent();
                    console.log(associatedTokenAccount.address.toBase58());
                    return [2 /*return*/];
            }
        });
    });
}
main(process.argv[2], process.argv[3]);
