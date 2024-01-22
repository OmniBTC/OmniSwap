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
var wormhole_sdk_1 = require("@certusone/wormhole-sdk");
var web3_js_1 = require("@solana/web3.js");
var path_1 = __importDefault(require("path"));
var fs_1 = __importDefault(require("fs"));
// export ANCHOR_PROVIDER_URL=""
var ANCHOR_PROVIDER_URL = process.env.ANCHOR_PROVIDER_URL;
var ANCHOR_WALLET = process.env.ANCHOR_WALLET;
var defaultPath = path_1["default"].join(process.env.HOME, '.config/solana/id.json');
var rawKey = JSON.parse(fs_1["default"].readFileSync(defaultPath, 'utf-8'));
var keypair = web3_js_1.Keypair.fromSecretKey(Uint8Array.from(rawKey));
function main(wormhole_program, signed_vaa) {
    return __awaiter(this, void 0, void 0, function () {
        var local_keypair, rawKey_1, resp;
        var _this = this;
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
                    return [4 /*yield*/, (0, wormhole_sdk_1.postVaaSolana)(new web3_js_1.Connection(ANCHOR_PROVIDER_URL, "processed"), function (transaction) { return __awaiter(_this, void 0, void 0, function () {
                            return __generator(this, function (_a) {
                                transaction.partialSign(local_keypair);
                                return [2 /*return*/, transaction];
                            });
                        }); }, wormhole_program, local_keypair.publicKey.toString(), Buffer.from(signed_vaa, "hex"))];
                case 1:
                    resp = _a.sent();
                    console.log("LegacyVerifySignatures: ", resp[0].signature);
                    console.log("LegacyPostVaa:", resp[1].signature);
                    return [2 /*return*/];
            }
        });
    });
}
main(process.argv[2], process.argv[3]);
