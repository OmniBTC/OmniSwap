export type Omniswap = {
  "version": "0.1.0",
  "name": "omniswap",
  "instructions": [
    {
      "name": "initialize",
      "docs": [
        "This instruction can be used to generate your program's config.",
        "And for convenience, we will store Wormhole-related PDAs in the",
        "config so we can verify these accounts with a simple == constraint."
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Whoever initializes the config will be the owner of the program. Signer",
            "for creating the [`SenderConfig`] and [`RedeemerConfig`] accounts."
          ]
        },
        {
          "name": "senderConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account, which saves program data useful for other",
            "instructions, specifically for outbound transfers. Also saves the payer",
            "of the [`initialize`](crate::initialize) instruction as the program's",
            "owner."
          ]
        },
        {
          "name": "redeemerConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Redeemer Config account, which saves program data useful for other",
            "instructions, specifically for inbound transfers. Also saves the payer",
            "of the [`initialize`](crate::initialize) instruction as the program's",
            "owner."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Token Bridge program needs this account to",
            "invoke the Wormhole program to post messages. Even though it is a",
            "required account for redeeming token transfers, it is not actually",
            "used for completing these transfers."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer for SPL tranfers when it is delegated",
            "spending approval for the SPL token."
          ]
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer for Token Bridge SPL tranfers."
          ]
        },
        {
          "name": "tokenBridgeMintAuthority",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer (SPL mint authority) for Token Bridge",
            "wrapped assets."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data account (a.k.a. its config)."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "that holds data; it is purely just a signer for posting Wormhole",
            "messages on behalf of the Token Bridge program."
          ]
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector account, which requires lamports before the",
            "program can post a message (if there is a fee). Token Bridge program",
            "handles the fee payments."
          ]
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge emitter's sequence account. Like with all Wormhole",
            "emitters, this account keeps track of the sequence number of the last",
            "posted message."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "relayerFee",
          "type": "u32"
        },
        {
          "name": "relayerFeePrecision",
          "type": "u32"
        }
      ]
    },
    {
      "name": "registerForeignContract",
      "docs": [
        "This instruction registers a new foreign contract (from another",
        "network) and saves the emitter information in a ForeignEmitter account.",
        "This instruction is owner-only, meaning that only the owner of the",
        "program (defined in the [Config] account) can add and update foreign",
        "contracts.",
        "",
        "# Arguments",
        "",
        "* `ctx`     - `RegisterForeignContract` context",
        "* `chain`   - Wormhole Chain ID",
        "* `address` - Wormhole Emitter Address"
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Owner of the program set in the [`SenderConfig`] account. Signer for",
            "creating [`ForeignContract`] account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. This program requires that the `owner` specified",
            "in the context equals the pubkey specified in this account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Create this account if an emitter has not been",
            "registered yet for this Wormhole chain ID. If there already is a",
            "contract address saved in this account, overwrite it."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but Token Bridge's PDA allows for multiple",
            "endpoints for each chain. We store the proper endpoint for the",
            "emitter chain."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "chain",
          "type": "u16"
        },
        {
          "name": "address",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    },
    {
      "name": "updateRelayerFee",
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. This program requires that the `owner`",
            "specified in the context equals the pubkey specified in this account.",
            "Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "relayerFee",
          "type": "u32"
        },
        {
          "name": "relayerFeePrecision",
          "type": "u32"
        }
      ]
    },
    {
      "name": "sendNativeTokensWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. Acts as the signer for the Token Bridge token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Send tokens to the contract specified in this",
            "account. Funnily enough, the Token Bridge program does not have any",
            "requirements for outbound transfers for the recipient chain to be",
            "registered. This account provides extra protection against sending",
            "tokens to an unregistered Wormhole chain ID. Read-only."
          ]
        },
        {
          "name": "mint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Mint info. This is the SPL token that will be bridged over to the",
            "foreign contract. Mutable."
          ]
        },
        {
          "name": "fromTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account. We may want to make this a generic",
            "token account in the future."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged out, the token account",
            "will have zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "tokenBridgeCustody",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "account that holds this mint's balance. This account needs to be",
            "unchecked because a token account may not have been created for this",
            "mint yet. Mutable."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "wormholeBridge",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data. Mutable."
          ]
        },
        {
          "name": "wormholeMessage",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "tokens transferred in this account for our program. Mutable."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector. Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock sysvar."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "batchId",
          "type": "u32"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapData",
          "type": "bytes"
        }
      ]
    },
    {
      "name": "redeemNativeTransferWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "payerTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "associated token account. Mutable."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. The registered contract specified in this",
            "account must agree with the target address for the Token Bridge's token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "mint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Mint info. This is the SPL token that will be bridged over from the",
            "foreign contract. This must match the token address specified in the",
            "signed Wormhole message. Read-only."
          ]
        },
        {
          "name": "recipientTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account."
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "transaction."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged in, the tokens will be",
            "transferred to the destination token accounts. This account will have",
            "zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "vaa",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Verified Wormhole message account. The Wormhole program verified",
            "signatures and posted the account data here. Read-only."
          ]
        },
        {
          "name": "tokenBridgeClaim",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "is true if the bridged assets have been claimed. If the transfer has",
            "not been redeemed, this account will not exist yet."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but the PDA allows for multiple endpoints for each",
            "chain! We store the proper endpoint for the emitter chain."
          ]
        },
        {
          "name": "tokenBridgeCustody",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "account that holds this mint's balance."
          ]
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "vaaHash",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    },
    {
      "name": "sendWrappedTokensWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. Acts as the Token Bridge sender PDA. Mutable."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Send tokens to the contract specified in this",
            "account. Funnily enough, the Token Bridge program does not have any",
            "requirements for outbound transfers for the recipient chain to be",
            "registered. This account provides extra protection against sending",
            "tokens to an unregistered Wormhole chain ID. Read-only."
          ]
        },
        {
          "name": "tokenBridgeWrappedMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge wrapped mint info. This is the SPL token that will be",
            "bridged to the foreign contract. The wrapped mint PDA must agree",
            "with the native token's metadata. Mutable."
          ]
        },
        {
          "name": "fromTokenAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeWrappedMeta",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program's wrapped metadata, which stores info",
            "about the token from its native chain:",
            "* Wormhole Chain ID",
            "* Token's native contract address",
            "* Token's native decimals"
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Mutable."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "wormholeBridge",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data. Mutable."
          ]
        },
        {
          "name": "wormholeMessage",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "tokens transferred in this account."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector. Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock sysvar."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "batchId",
          "type": "u32"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapData",
          "type": "bytes"
        }
      ]
    },
    {
      "name": "redeemWrappedTransferWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "payerTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "associated token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. The registered contract specified in this",
            "account must agree with the target address for the Token Bridge's token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "tokenBridgeWrappedMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge wrapped mint info. This is the SPL token that will be",
            "bridged from the foreign contract. The wrapped mint PDA must agree",
            "with the native token's metadata in the wormhole message. Mutable."
          ]
        },
        {
          "name": "recipientTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account."
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "transaction."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged in, the tokens will be",
            "transferred to the destination token accounts. This account will have",
            "zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeWrappedMeta",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program's wrapped metadata, which stores info",
            "about the token from its native chain:",
            "* Wormhole Chain ID",
            "* Token's native contract address",
            "* Token's native decimals"
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "vaa",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Verified Wormhole message account. The Wormhole program verified",
            "signatures and posted the account data here. Read-only."
          ]
        },
        {
          "name": "tokenBridgeClaim",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "is true if the bridged assets have been claimed. If the transfer has",
            "not been redeemed, this account will not exist yet."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but the PDA allows for multiple endpoints for each",
            "chain! We store the proper endpoint for the emitter chain."
          ]
        },
        {
          "name": "tokenBridgeMintAuthority",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "vaaHash",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "foreignContract",
      "docs": [
        "Foreign emitter account data."
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "chain",
            "docs": [
              "Emitter chain. Cannot equal `1` (Solana's Chain ID)."
            ],
            "type": "u16"
          },
          {
            "name": "address",
            "docs": [
              "Emitter address. Cannot be zero address."
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "tokenBridgeForeignEndpoint",
            "docs": [
              "Token Bridge program's foreign endpoint account key."
            ],
            "type": "publicKey"
          }
        ]
      }
    },
    {
      "name": "redeemerConfig",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Program's owner."
            ],
            "type": "publicKey"
          },
          {
            "name": "bump",
            "docs": [
              "PDA bump."
            ],
            "type": "u8"
          },
          {
            "name": "tokenBridge",
            "docs": [
              "Token Bridge program's relevant addresses."
            ],
            "type": {
              "defined": "InboundTokenBridgeAddresses"
            }
          },
          {
            "name": "relayerFee",
            "docs": [
              "Relayer Fee"
            ],
            "type": "u32"
          },
          {
            "name": "relayerFeePrecision",
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "senderConfig",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Program's owner."
            ],
            "type": "publicKey"
          },
          {
            "name": "bump",
            "docs": [
              "PDA bump."
            ],
            "type": "u8"
          },
          {
            "name": "tokenBridge",
            "docs": [
              "Token Bridge program's relevant addresses."
            ],
            "type": {
              "defined": "OutboundTokenBridgeAddresses"
            }
          },
          {
            "name": "finality",
            "docs": [
              "AKA consistency level. u8 representation of Solana's",
              "[Finality](wormhole_anchor_sdk::wormhole::Finality)."
            ],
            "type": "u8"
          }
        ]
      }
    }
  ],
  "types": [
    {
      "name": "InboundTokenBridgeAddresses",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "type": "publicKey"
          },
          {
            "name": "custodySigner",
            "type": "publicKey"
          },
          {
            "name": "mintAuthority",
            "type": "publicKey"
          }
        ]
      }
    },
    {
      "name": "OutboundTokenBridgeAddresses",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "type": "publicKey"
          },
          {
            "name": "authoritySigner",
            "type": "publicKey"
          },
          {
            "name": "custodySigner",
            "type": "publicKey"
          },
          {
            "name": "emitter",
            "type": "publicKey"
          },
          {
            "name": "sequence",
            "type": "publicKey"
          },
          {
            "name": "wormholeBridge",
            "docs": [
              "[BridgeData](wormhole_anchor_sdk::wormhole::BridgeData) address."
            ],
            "type": "publicKey"
          },
          {
            "name": "wormholeFeeCollector",
            "docs": [
              "[FeeCollector](wormhole_anchor_sdk::wormhole::FeeCollector) address."
            ],
            "type": "publicKey"
          }
        ]
      }
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "InvalidWormholeBridge",
      "msg": "InvalidWormholeBridge"
    },
    {
      "code": 6001,
      "name": "InvalidWormholeFeeCollector",
      "msg": "InvalidWormholeFeeCollector"
    },
    {
      "code": 6002,
      "name": "InvalidWormholeEmitter",
      "msg": "InvalidWormholeEmitter"
    },
    {
      "code": 6003,
      "name": "InvalidWormholeSequence",
      "msg": "InvalidWormholeSequence"
    },
    {
      "code": 6004,
      "name": "InvalidSysvar",
      "msg": "InvalidSysvar"
    },
    {
      "code": 6005,
      "name": "OwnerOnly",
      "msg": "OwnerOnly"
    },
    {
      "code": 6006,
      "name": "BumpNotFound",
      "msg": "BumpNotFound"
    },
    {
      "code": 6007,
      "name": "InvalidForeignContract",
      "msg": "InvalidForeignContract"
    },
    {
      "code": 6008,
      "name": "ZeroBridgeAmount",
      "msg": "ZeroBridgeAmount"
    },
    {
      "code": 6009,
      "name": "InvalidTokenBridgeConfig",
      "msg": "InvalidTokenBridgeConfig"
    },
    {
      "code": 6010,
      "name": "InvalidTokenBridgeAuthoritySigner",
      "msg": "InvalidTokenBridgeAuthoritySigner"
    },
    {
      "code": 6011,
      "name": "InvalidTokenBridgeCustodySigner",
      "msg": "InvalidTokenBridgeCustodySigner"
    },
    {
      "code": 6012,
      "name": "InvalidTokenBridgeEmitter",
      "msg": "InvalidTokenBridgeEmitter"
    },
    {
      "code": 6013,
      "name": "InvalidTokenBridgeSequence",
      "msg": "InvalidTokenBridgeSequence"
    },
    {
      "code": 6014,
      "name": "InvalidTokenBridgeSender",
      "msg": "InvalidTokenBridgeSender"
    },
    {
      "code": 6015,
      "name": "InvalidRecipient",
      "msg": "InvalidRecipient"
    },
    {
      "code": 6016,
      "name": "InvalidTransferTokenAccount",
      "msg": "InvalidTransferTokenAccount"
    },
    {
      "code": 6017,
      "name": "InvalidTransferToChain",
      "msg": "InvalidTransferTokenChain"
    },
    {
      "code": 6018,
      "name": "InvalidTransferTokenChain",
      "msg": "InvalidTransferTokenChain"
    },
    {
      "code": 6019,
      "name": "InvalidRelayerFee",
      "msg": "InvalidRelayerFee"
    },
    {
      "code": 6020,
      "name": "InvalidPayerAta",
      "msg": "InvalidPayerAta"
    },
    {
      "code": 6021,
      "name": "InvalidTransferToAddress",
      "msg": "InvalidTransferToAddress"
    },
    {
      "code": 6022,
      "name": "AlreadyRedeemed",
      "msg": "AlreadyRedeemed"
    },
    {
      "code": 6023,
      "name": "InvalidTokenBridgeForeignEndpoint",
      "msg": "InvalidTokenBridgeForeignEndpoint"
    },
    {
      "code": 6024,
      "name": "NonExistentRelayerAta",
      "msg": "NonExistentRelayerAta"
    },
    {
      "code": 6025,
      "name": "InvalidTokenBridgeMintAuthority",
      "msg": "InvalidTokenBridgeMintAuthority"
    }
  ]
};

export const IDL: Omniswap = {
  "version": "0.1.0",
  "name": "omniswap",
  "instructions": [
    {
      "name": "initialize",
      "docs": [
        "This instruction can be used to generate your program's config.",
        "And for convenience, we will store Wormhole-related PDAs in the",
        "config so we can verify these accounts with a simple == constraint."
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Whoever initializes the config will be the owner of the program. Signer",
            "for creating the [`SenderConfig`] and [`RedeemerConfig`] accounts."
          ]
        },
        {
          "name": "senderConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account, which saves program data useful for other",
            "instructions, specifically for outbound transfers. Also saves the payer",
            "of the [`initialize`](crate::initialize) instruction as the program's",
            "owner."
          ]
        },
        {
          "name": "redeemerConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Redeemer Config account, which saves program data useful for other",
            "instructions, specifically for inbound transfers. Also saves the payer",
            "of the [`initialize`](crate::initialize) instruction as the program's",
            "owner."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Token Bridge program needs this account to",
            "invoke the Wormhole program to post messages. Even though it is a",
            "required account for redeeming token transfers, it is not actually",
            "used for completing these transfers."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer for SPL tranfers when it is delegated",
            "spending approval for the SPL token."
          ]
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer for Token Bridge SPL tranfers."
          ]
        },
        {
          "name": "tokenBridgeMintAuthority",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "data; it is purely just a signer (SPL mint authority) for Token Bridge",
            "wrapped assets."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data account (a.k.a. its config)."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "that holds data; it is purely just a signer for posting Wormhole",
            "messages on behalf of the Token Bridge program."
          ]
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector account, which requires lamports before the",
            "program can post a message (if there is a fee). Token Bridge program",
            "handles the fee payments."
          ]
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge emitter's sequence account. Like with all Wormhole",
            "emitters, this account keeps track of the sequence number of the last",
            "posted message."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "relayerFee",
          "type": "u32"
        },
        {
          "name": "relayerFeePrecision",
          "type": "u32"
        }
      ]
    },
    {
      "name": "registerForeignContract",
      "docs": [
        "This instruction registers a new foreign contract (from another",
        "network) and saves the emitter information in a ForeignEmitter account.",
        "This instruction is owner-only, meaning that only the owner of the",
        "program (defined in the [Config] account) can add and update foreign",
        "contracts.",
        "",
        "# Arguments",
        "",
        "* `ctx`     - `RegisterForeignContract` context",
        "* `chain`   - Wormhole Chain ID",
        "* `address` - Wormhole Emitter Address"
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Owner of the program set in the [`SenderConfig`] account. Signer for",
            "creating [`ForeignContract`] account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. This program requires that the `owner` specified",
            "in the context equals the pubkey specified in this account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Create this account if an emitter has not been",
            "registered yet for this Wormhole chain ID. If there already is a",
            "contract address saved in this account, overwrite it."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but Token Bridge's PDA allows for multiple",
            "endpoints for each chain. We store the proper endpoint for the",
            "emitter chain."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "chain",
          "type": "u16"
        },
        {
          "name": "address",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    },
    {
      "name": "updateRelayerFee",
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. This program requires that the `owner`",
            "specified in the context equals the pubkey specified in this account.",
            "Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        }
      ],
      "args": [
        {
          "name": "relayerFee",
          "type": "u32"
        },
        {
          "name": "relayerFeePrecision",
          "type": "u32"
        }
      ]
    },
    {
      "name": "sendNativeTokensWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. Acts as the signer for the Token Bridge token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Send tokens to the contract specified in this",
            "account. Funnily enough, the Token Bridge program does not have any",
            "requirements for outbound transfers for the recipient chain to be",
            "registered. This account provides extra protection against sending",
            "tokens to an unregistered Wormhole chain ID. Read-only."
          ]
        },
        {
          "name": "mint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Mint info. This is the SPL token that will be bridged over to the",
            "foreign contract. Mutable."
          ]
        },
        {
          "name": "fromTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account. We may want to make this a generic",
            "token account in the future."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged out, the token account",
            "will have zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "tokenBridgeCustody",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "account that holds this mint's balance. This account needs to be",
            "unchecked because a token account may not have been created for this",
            "mint yet. Mutable."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "wormholeBridge",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data. Mutable."
          ]
        },
        {
          "name": "wormholeMessage",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "tokens transferred in this account for our program. Mutable."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector. Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock sysvar."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "batchId",
          "type": "u32"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapData",
          "type": "bytes"
        }
      ]
    },
    {
      "name": "redeemNativeTransferWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "payerTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "associated token account. Mutable."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. The registered contract specified in this",
            "account must agree with the target address for the Token Bridge's token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "mint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Mint info. This is the SPL token that will be bridged over from the",
            "foreign contract. This must match the token address specified in the",
            "signed Wormhole message. Read-only."
          ]
        },
        {
          "name": "recipientTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account."
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "transaction."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged in, the tokens will be",
            "transferred to the destination token accounts. This account will have",
            "zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "vaa",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Verified Wormhole message account. The Wormhole program verified",
            "signatures and posted the account data here. Read-only."
          ]
        },
        {
          "name": "tokenBridgeClaim",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "is true if the bridged assets have been claimed. If the transfer has",
            "not been redeemed, this account will not exist yet."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but the PDA allows for multiple endpoints for each",
            "chain! We store the proper endpoint for the emitter chain."
          ]
        },
        {
          "name": "tokenBridgeCustody",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "account that holds this mint's balance."
          ]
        },
        {
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "vaaHash",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    },
    {
      "name": "sendWrappedTokensWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Sender Config account. Acts as the Token Bridge sender PDA. Mutable."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. Send tokens to the contract specified in this",
            "account. Funnily enough, the Token Bridge program does not have any",
            "requirements for outbound transfers for the recipient chain to be",
            "registered. This account provides extra protection against sending",
            "tokens to an unregistered Wormhole chain ID. Read-only."
          ]
        },
        {
          "name": "tokenBridgeWrappedMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge wrapped mint info. This is the SPL token that will be",
            "bridged to the foreign contract. The wrapped mint PDA must agree",
            "with the native token's metadata. Mutable."
          ]
        },
        {
          "name": "fromTokenAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeWrappedMeta",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program's wrapped metadata, which stores info",
            "about the token from its native chain:",
            "* Wormhole Chain ID",
            "* Token's native contract address",
            "* Token's native decimals"
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Mutable."
          ]
        },
        {
          "name": "tokenBridgeAuthoritySigner",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "wormholeBridge",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data. Mutable."
          ]
        },
        {
          "name": "wormholeMessage",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "tokens transferred in this account."
          ]
        },
        {
          "name": "tokenBridgeEmitter",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "tokenBridgeSequence",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wormholeFeeCollector",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Wormhole fee collector. Mutable."
          ]
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock sysvar."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "batchId",
          "type": "u32"
        },
        {
          "name": "amount",
          "type": "u64"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapData",
          "type": "bytes"
        }
      ]
    },
    {
      "name": "redeemWrappedTransferWithPayload",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Payer will pay Wormhole fee to transfer tokens and create temporary",
            "token account."
          ]
        },
        {
          "name": "payerTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "associated token account."
          ]
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign Contract account. The registered contract specified in this",
            "account must agree with the target address for the Token Bridge's token",
            "transfer. Read-only."
          ]
        },
        {
          "name": "tokenBridgeWrappedMint",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Token Bridge wrapped mint info. This is the SPL token that will be",
            "bridged from the foreign contract. The wrapped mint PDA must agree",
            "with the native token's metadata in the wormhole message. Mutable."
          ]
        },
        {
          "name": "recipientTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account."
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "transaction."
          ]
        },
        {
          "name": "tmpTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Program's temporary token account. This account is created before the",
            "instruction is invoked to temporarily take custody of the payer's",
            "tokens. When the tokens are finally bridged in, the tokens will be",
            "transferred to the destination token accounts. This account will have",
            "zero balance and can be closed."
          ]
        },
        {
          "name": "wormholeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole program."
          ]
        },
        {
          "name": "tokenBridgeProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program."
          ]
        },
        {
          "name": "tokenBridgeWrappedMeta",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge program's wrapped metadata, which stores info",
            "about the token from its native chain:",
            "* Wormhole Chain ID",
            "* Token's native contract address",
            "* Token's native decimals"
          ]
        },
        {
          "name": "tokenBridgeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge config. Read-only."
          ]
        },
        {
          "name": "vaa",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Verified Wormhole message account. The Wormhole program verified",
            "signatures and posted the account data here. Read-only."
          ]
        },
        {
          "name": "tokenBridgeClaim",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "is true if the bridged assets have been claimed. If the transfer has",
            "not been redeemed, this account will not exist yet."
          ]
        },
        {
          "name": "tokenBridgeForeignEndpoint",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token Bridge foreign endpoint. This account should really be one",
            "endpoint per chain, but the PDA allows for multiple endpoints for each",
            "chain! We store the proper endpoint for the emitter chain."
          ]
        },
        {
          "name": "tokenBridgeMintAuthority",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "systemProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "System program."
          ]
        },
        {
          "name": "tokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Token program."
          ]
        },
        {
          "name": "associatedTokenProgram",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Associated Token program."
          ]
        },
        {
          "name": "rent",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Rent sysvar."
          ]
        }
      ],
      "args": [
        {
          "name": "vaaHash",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "foreignContract",
      "docs": [
        "Foreign emitter account data."
      ],
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "chain",
            "docs": [
              "Emitter chain. Cannot equal `1` (Solana's Chain ID)."
            ],
            "type": "u16"
          },
          {
            "name": "address",
            "docs": [
              "Emitter address. Cannot be zero address."
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "tokenBridgeForeignEndpoint",
            "docs": [
              "Token Bridge program's foreign endpoint account key."
            ],
            "type": "publicKey"
          }
        ]
      }
    },
    {
      "name": "redeemerConfig",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Program's owner."
            ],
            "type": "publicKey"
          },
          {
            "name": "bump",
            "docs": [
              "PDA bump."
            ],
            "type": "u8"
          },
          {
            "name": "tokenBridge",
            "docs": [
              "Token Bridge program's relevant addresses."
            ],
            "type": {
              "defined": "InboundTokenBridgeAddresses"
            }
          },
          {
            "name": "relayerFee",
            "docs": [
              "Relayer Fee"
            ],
            "type": "u32"
          },
          {
            "name": "relayerFeePrecision",
            "type": "u32"
          }
        ]
      }
    },
    {
      "name": "senderConfig",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Program's owner."
            ],
            "type": "publicKey"
          },
          {
            "name": "bump",
            "docs": [
              "PDA bump."
            ],
            "type": "u8"
          },
          {
            "name": "tokenBridge",
            "docs": [
              "Token Bridge program's relevant addresses."
            ],
            "type": {
              "defined": "OutboundTokenBridgeAddresses"
            }
          },
          {
            "name": "finality",
            "docs": [
              "AKA consistency level. u8 representation of Solana's",
              "[Finality](wormhole_anchor_sdk::wormhole::Finality)."
            ],
            "type": "u8"
          }
        ]
      }
    }
  ],
  "types": [
    {
      "name": "InboundTokenBridgeAddresses",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "type": "publicKey"
          },
          {
            "name": "custodySigner",
            "type": "publicKey"
          },
          {
            "name": "mintAuthority",
            "type": "publicKey"
          }
        ]
      }
    },
    {
      "name": "OutboundTokenBridgeAddresses",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "config",
            "type": "publicKey"
          },
          {
            "name": "authoritySigner",
            "type": "publicKey"
          },
          {
            "name": "custodySigner",
            "type": "publicKey"
          },
          {
            "name": "emitter",
            "type": "publicKey"
          },
          {
            "name": "sequence",
            "type": "publicKey"
          },
          {
            "name": "wormholeBridge",
            "docs": [
              "[BridgeData](wormhole_anchor_sdk::wormhole::BridgeData) address."
            ],
            "type": "publicKey"
          },
          {
            "name": "wormholeFeeCollector",
            "docs": [
              "[FeeCollector](wormhole_anchor_sdk::wormhole::FeeCollector) address."
            ],
            "type": "publicKey"
          }
        ]
      }
    }
  ],
  "errors": [
    {
      "code": 6000,
      "name": "InvalidWormholeBridge",
      "msg": "InvalidWormholeBridge"
    },
    {
      "code": 6001,
      "name": "InvalidWormholeFeeCollector",
      "msg": "InvalidWormholeFeeCollector"
    },
    {
      "code": 6002,
      "name": "InvalidWormholeEmitter",
      "msg": "InvalidWormholeEmitter"
    },
    {
      "code": 6003,
      "name": "InvalidWormholeSequence",
      "msg": "InvalidWormholeSequence"
    },
    {
      "code": 6004,
      "name": "InvalidSysvar",
      "msg": "InvalidSysvar"
    },
    {
      "code": 6005,
      "name": "OwnerOnly",
      "msg": "OwnerOnly"
    },
    {
      "code": 6006,
      "name": "BumpNotFound",
      "msg": "BumpNotFound"
    },
    {
      "code": 6007,
      "name": "InvalidForeignContract",
      "msg": "InvalidForeignContract"
    },
    {
      "code": 6008,
      "name": "ZeroBridgeAmount",
      "msg": "ZeroBridgeAmount"
    },
    {
      "code": 6009,
      "name": "InvalidTokenBridgeConfig",
      "msg": "InvalidTokenBridgeConfig"
    },
    {
      "code": 6010,
      "name": "InvalidTokenBridgeAuthoritySigner",
      "msg": "InvalidTokenBridgeAuthoritySigner"
    },
    {
      "code": 6011,
      "name": "InvalidTokenBridgeCustodySigner",
      "msg": "InvalidTokenBridgeCustodySigner"
    },
    {
      "code": 6012,
      "name": "InvalidTokenBridgeEmitter",
      "msg": "InvalidTokenBridgeEmitter"
    },
    {
      "code": 6013,
      "name": "InvalidTokenBridgeSequence",
      "msg": "InvalidTokenBridgeSequence"
    },
    {
      "code": 6014,
      "name": "InvalidTokenBridgeSender",
      "msg": "InvalidTokenBridgeSender"
    },
    {
      "code": 6015,
      "name": "InvalidRecipient",
      "msg": "InvalidRecipient"
    },
    {
      "code": 6016,
      "name": "InvalidTransferTokenAccount",
      "msg": "InvalidTransferTokenAccount"
    },
    {
      "code": 6017,
      "name": "InvalidTransferToChain",
      "msg": "InvalidTransferTokenChain"
    },
    {
      "code": 6018,
      "name": "InvalidTransferTokenChain",
      "msg": "InvalidTransferTokenChain"
    },
    {
      "code": 6019,
      "name": "InvalidRelayerFee",
      "msg": "InvalidRelayerFee"
    },
    {
      "code": 6020,
      "name": "InvalidPayerAta",
      "msg": "InvalidPayerAta"
    },
    {
      "code": 6021,
      "name": "InvalidTransferToAddress",
      "msg": "InvalidTransferToAddress"
    },
    {
      "code": 6022,
      "name": "AlreadyRedeemed",
      "msg": "AlreadyRedeemed"
    },
    {
      "code": 6023,
      "name": "InvalidTokenBridgeForeignEndpoint",
      "msg": "InvalidTokenBridgeForeignEndpoint"
    },
    {
      "code": 6024,
      "name": "NonExistentRelayerAta",
      "msg": "NonExistentRelayerAta"
    },
    {
      "code": 6025,
      "name": "InvalidTokenBridgeMintAuthority",
      "msg": "InvalidTokenBridgeMintAuthority"
    }
  ]
};
