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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
exports.__esModule = true;
var web3_js_1 = require("@solana/web3.js");
var whirlpools_sdk_1 = require("@orca-so/whirlpools-sdk");
var common_sdk_1 = require("@orca-so/common-sdk");
var spl_token_1 = require("@solana/spl-token");
var decimal_js_1 = __importDefault(require("decimal.js"));
var anchor_1 = require("@coral-xyz/anchor");
var path_1 = __importDefault(require("path"));
var fs_1 = __importDefault(require("fs"));
// export ANCHOR_PROVIDER_URL=""
var ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
var ANCHOR_WALLET = process.env.ANCHOR_WALLET;
var connection = new web3_js_1.Connection(ANCHOR_PROVIDER_URL);
var defaultPath = path_1["default"].join(process.env.HOME, '.config/solana/id.json');
var rawKey = JSON.parse(fs_1["default"].readFileSync(defaultPath, 'utf-8'));
var keypair = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey));
var default_wallet = new anchor_1.Wallet(keypair);
var rent_ta = function () { return __awaiter(void 0, void 0, void 0, function () { return __generator(this, function (_a) {
    return [2 /*return*/, connection.getMinimumBalanceForRentExemption(spl_token_1.AccountLayout.span)];
}); }); };
function main(whirlpool_address, token_mint_in, amount_in) {
    return __awaiter(this, void 0, void 0, function () {
        var local_wallet, rawKey_1, keypair_1, ctx, client, acountFetcher, whirlpool, token_a, token_b, default_slippage, input_token_mint, shift_decimals, shift_amount_in, quote, quote_config, whirlpool_data, token_owner_account_a, token_owner_account_b, oracle_pda;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (ANCHOR_WALLET === undefined || ANCHOR_WALLET === "") {
                        local_wallet = default_wallet;
                    }
                    else {
                        rawKey_1 = new Uint8Array(JSON.parse(ANCHOR_WALLET));
                        keypair_1 = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey_1));
                        local_wallet = new anchor_1.Wallet(keypair_1);
                    }
                    ctx = whirlpools_sdk_1.WhirlpoolContext.from(connection, local_wallet, whirlpools_sdk_1.ORCA_WHIRLPOOL_PROGRAM_ID);
                    client = (0, whirlpools_sdk_1.buildWhirlpoolClient)(ctx);
                    acountFetcher = (0, whirlpools_sdk_1.buildDefaultAccountFetcher)(connection);
                    return [4 /*yield*/, client.getPool(whirlpool_address)];
                case 1:
                    whirlpool = _a.sent();
                    token_a = whirlpool.getTokenAInfo();
                    token_b = whirlpool.getTokenBInfo();
                    default_slippage = common_sdk_1.Percentage.fromFraction(10, 1000);
                    input_token_mint = new web3_js_1.PublicKey(token_mint_in);
                    shift_decimals = input_token_mint.equals(token_a.mint) ? token_a.decimals : token_b.decimals;
                    shift_amount_in = common_sdk_1.DecimalUtil.toBN(new decimal_js_1["default"](amount_in), shift_decimals);
                    return [4 /*yield*/, (0, whirlpools_sdk_1.swapQuoteByInputToken)(whirlpool, input_token_mint, shift_amount_in, default_slippage, ctx.program.programId, acountFetcher)];
                case 2:
                    quote = _a.sent();
                    quote_config = {};
                    whirlpool_data = whirlpool.getData();
                    return [4 /*yield*/, (0, common_sdk_1.resolveOrCreateATA)(connection, local_wallet.publicKey, whirlpool_data.tokenMintA, rent_ta)];
                case 3:
                    token_owner_account_a = _a.sent();
                    return [4 /*yield*/, (0, common_sdk_1.resolveOrCreateATA)(connection, local_wallet.publicKey, whirlpool_data.tokenMintB, rent_ta)];
                case 4:
                    token_owner_account_b = _a.sent();
                    return [4 /*yield*/, whirlpools_sdk_1.PDAUtil.getOracle(ctx.program.programId, whirlpool.getAddress())];
                case 5:
                    oracle_pda = _a.sent();
                    quote_config["whirlpool_program"] = whirlpools_sdk_1.ORCA_WHIRLPOOL_PROGRAM_ID.toString();
                    quote_config["whirlpool"] = whirlpool_address;
                    quote_config["token_mint_a"] = whirlpool_data.tokenMintA;
                    quote_config["token_mint_b"] = whirlpool_data.tokenMintB;
                    quote_config["token_owner_account_a"] = token_owner_account_a.address;
                    quote_config["token_owner_account_b"] = token_owner_account_b.address;
                    quote_config["token_vault_a"] = whirlpool_data.tokenVaultA;
                    quote_config["token_vault_b"] = whirlpool_data.tokenVaultB;
                    quote_config["tick_array_0"] = quote.tickArray0.toString();
                    quote_config["tick_array_1"] = quote.tickArray1.toString();
                    quote_config["tick_array_2"] = quote.tickArray2.toString();
                    quote_config["oracle"] = oracle_pda.publicKey.toString();
                    quote_config["is_a_to_b"] = quote.aToB;
                    quote_config["amount_in"] = common_sdk_1.DecimalUtil.fromBN(quote.estimatedAmountIn);
                    quote_config["estimated_amount_out"] = common_sdk_1.DecimalUtil.fromBN(quote.estimatedAmountOut);
                    quote_config["min_amount_out"] = common_sdk_1.DecimalUtil.fromBN(quote.otherAmountThreshold);
                    console.log(JSON.stringify(quote_config, null, 2));
                    return [2 /*return*/];
            }
        });
    });
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
