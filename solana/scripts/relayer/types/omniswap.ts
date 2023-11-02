export type Omniswap = {
  "version": "0.3.0",
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
          "name": "feeConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "SoFee Config account"
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
          "name": "beneficiary",
          "type": "publicKey"
        },
        {
          "name": "redeemerProxy",
          "type": "publicKey"
        },
        {
          "name": "actualReserve",
          "type": "u64"
        },
        {
          "name": "estimateReserve",
          "type": "u64"
        },
        {
          "name": "soFeeByRay",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setWormholeReserve",
      "docs": [
        "Set relayer fee scale factor"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "actualReserve",
          "type": "u64"
        },
        {
          "name": "estimateReserve",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setSoFee",
      "docs": [
        "Set so fee"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "soFeeByRay",
          "type": "u64"
        }
      ]
    },
    {
      "name": "registerForeignContract",
      "docs": [
        "This instruction registers a new foreign contract (from another",
        "network) and saves the emitter information in a ForeignEmitter account",
        "and price ratio information in a PriceManager account.",
        "This instruction is owner-only, meaning that only the owner of the",
        "program (defined in the [Config] account) can add and update foreign",
        "contracts.",
        "",
        "# Arguments",
        "",
        "* `ctx`     - `RegisterForeignContract` context",
        "* `chain`   - Wormhole Chain ID",
        "* `address` - Wormhole Emitter Address. Left-zero-padded if shorter than 32 bytes",
        "* `normalized_dst_base_gas_le` - Normalized target chain minimum consumption of gas",
        "* `normalized_dst_gas_per_bytes_le` - Normalized target chain gas per bytes",
        "* `price_manager` - Who can update current_price_ratio",
        "* `init_price_ratio` - Current price ratio"
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
          "name": "priceManager",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Price manager account. Create this account if an emitter has not been",
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
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock used for price manager."
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
        },
        {
          "name": "normalizedDstBaseGasLe",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "normalizedDstGasPerBytesLe",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "priceManagerOwner",
          "type": "publicKey"
        },
        {
          "name": "initPriceRatio",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setPriceRatio",
      "docs": [
        "Set the target chain price ratio",
        "Note: the owner of PriceManager can be overwrite by register_foreign_contract"
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Owner of the program set in the [`PriceManager`] account. Signer for",
            "updating [`PriceManager`] account."
          ]
        },
        {
          "name": "priceManager",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Price Manager account."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock used for price manager."
          ]
        }
      ],
      "args": [
        {
          "name": "chain",
          "type": "u16"
        },
        {
          "name": "newPriceRatio",
          "type": "u64"
        }
      ]
    },
    {
      "name": "soSwapNativeWithoutSwap",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "completeSoSwapNativeWithoutSwap",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
        },
        {
          "name": "skipVerifySoswapMessage",
          "type": "bool"
        }
      ]
    },
    {
      "name": "soSwapWrappedWithoutSwap",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "completeSoSwapWrappedWithoutSwap",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
        },
        {
          "name": "skipVerifySoswapMessage",
          "type": "bool"
        }
      ]
    },
    {
      "name": "estimateRelayerFee",
      "accounts": [
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign contract account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data.",
            "Query bridge.config.fee"
          ]
        }
      ],
      "args": [
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "swapDataDst",
          "type": "bytes"
        }
      ],
      "returns": {
        "defined": "(u64,u64,u128)"
      }
    },
    {
      "name": "soSwapNativeWithWhirlpool",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
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
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "soSwapWrappedWithWhirlpool",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
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
      "args": []
    },
    {
      "name": "completeSoSwapNativeWithWhirlpool",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
          ]
        },
        {
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
            "Recipient associated token account.",
            "If swap ok, transfer the receiving token to this account"
          ]
        },
        {
          "name": "recipientBridgeTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account.",
            "If swap failed, transfer the bridge token to this account"
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
      "name": "completeSoSwapWrappedWithWhirlpool",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
          ]
        },
        {
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
            "Recipient associated token account.",
            "If swap ok, transfer the receiving token to this account"
          ]
        },
        {
          "name": "recipientBridgeTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account.",
            "If swap failed, transfer the bridge token to this account"
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
    },
    {
      "name": "setRedeemProxy",
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "newProxy",
          "type": "publicKey"
        }
      ]
    },
    {
      "name": "soSwapPostCrossRequest",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "The requester"
          ]
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account"
          ]
        },
        {
          "name": "request",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign contract account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data.",
            "Query bridge.config.fee"
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
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapDataSrc",
          "type": "bytes"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "swapDataDst",
          "type": "bytes"
        }
      ],
      "returns": "u64"
    },
    {
      "name": "soSwapClosePendingRequest",
      "docs": [
        "Close the pending cross request.",
        "The remaining lamports will be refunded to the requester"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "The requester or proxy"
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account."
          ]
        },
        {
          "name": "request",
          "isMut": true,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "wrapSol",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "wrapSolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false
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
          "name": "amountToBeWrapped",
          "type": "u64"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "crossRequest",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "The SenderConfig address."
            ],
            "type": "publicKey"
          },
          {
            "name": "payer",
            "docs": [
              "The requester."
            ],
            "type": "publicKey"
          },
          {
            "name": "nonce",
            "docs": [
              "The SenderConfig nonce."
            ],
            "type": "u64"
          },
          {
            "name": "soData",
            "docs": [
              "The cross data."
            ],
            "type": "bytes"
          },
          {
            "name": "swapDataSrc",
            "type": "bytes"
          },
          {
            "name": "wormholeData",
            "type": "bytes"
          },
          {
            "name": "swapDataDst",
            "type": "bytes"
          }
        ]
      }
    },
    {
      "name": "soFeeConfig",
      "docs": [
        "The so fee of cross token"
      ],
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
            "name": "beneficiary",
            "docs": [
              "The recipient of [relayer_fee + so_fee]."
            ],
            "type": "publicKey"
          },
          {
            "name": "soFee",
            "docs": [
              "SoFee by RAY"
            ],
            "type": "u64"
          },
          {
            "name": "actualReserve",
            "docs": [
              "Actual relayer fee scale factor"
            ],
            "type": "u64"
          },
          {
            "name": "estimateReserve",
            "docs": [
              "Estimate relayer fee scale factor"
            ],
            "type": "u64"
          }
        ]
      }
    },
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
              "Emitter address. Cannot be zero address.",
              "Left-zero-padded if shorter than 32 bytes"
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
          },
          {
            "name": "normalizedDstBaseGas",
            "docs": [
              "Normalized target chain minimum consumption of gas"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "normalizedDstGasPerBytes",
            "docs": [
              "Normalized target chain gas per bytes"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          }
        ]
      }
    },
    {
      "name": "priceManager",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Who can update current_price_ratio"
            ],
            "type": "publicKey"
          },
          {
            "name": "currentPriceRatio",
            "docs": [
              "The currnet price ratio of native coins"
            ],
            "type": "u64"
          },
          {
            "name": "lastUpdateTimestamp",
            "type": "u64"
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
            "name": "proxy",
            "docs": [
              "Proxy account"
            ],
            "type": "publicKey"
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
            "name": "nonce",
            "docs": [
              "Used for cross request."
            ],
            "type": "u64"
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
    },
    {
      "code": 6026,
      "name": "InvalidDataLength",
      "msg": "InvalidDataLength"
    },
    {
      "code": 6027,
      "name": "DeserializeSoSwapMessageFail",
      "msg": "DeserializeSoSwapMessageFail"
    },
    {
      "code": 6028,
      "name": "InvalidBeneficiary",
      "msg": "InvalidBeneficiary"
    },
    {
      "code": 6029,
      "name": "CheckFeeFail",
      "msg": "CheckFeeFail"
    },
    {
      "code": 6030,
      "name": "UnexpectValue",
      "msg": "UnexpectValue"
    },
    {
      "code": 6031,
      "name": "InvalidCallData",
      "msg": "InvalidCallData"
    },
    {
      "code": 6032,
      "name": "InvalidProxy",
      "msg": "InvalidProxy"
    }
  ]
};

export const IDL: Omniswap = {
  "version": "0.3.0",
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
          "name": "feeConfig",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "SoFee Config account"
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
          "name": "beneficiary",
          "type": "publicKey"
        },
        {
          "name": "redeemerProxy",
          "type": "publicKey"
        },
        {
          "name": "actualReserve",
          "type": "u64"
        },
        {
          "name": "estimateReserve",
          "type": "u64"
        },
        {
          "name": "soFeeByRay",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setWormholeReserve",
      "docs": [
        "Set relayer fee scale factor"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "actualReserve",
          "type": "u64"
        },
        {
          "name": "estimateReserve",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setSoFee",
      "docs": [
        "Set so fee"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "soFeeByRay",
          "type": "u64"
        }
      ]
    },
    {
      "name": "registerForeignContract",
      "docs": [
        "This instruction registers a new foreign contract (from another",
        "network) and saves the emitter information in a ForeignEmitter account",
        "and price ratio information in a PriceManager account.",
        "This instruction is owner-only, meaning that only the owner of the",
        "program (defined in the [Config] account) can add and update foreign",
        "contracts.",
        "",
        "# Arguments",
        "",
        "* `ctx`     - `RegisterForeignContract` context",
        "* `chain`   - Wormhole Chain ID",
        "* `address` - Wormhole Emitter Address. Left-zero-padded if shorter than 32 bytes",
        "* `normalized_dst_base_gas_le` - Normalized target chain minimum consumption of gas",
        "* `normalized_dst_gas_per_bytes_le` - Normalized target chain gas per bytes",
        "* `price_manager` - Who can update current_price_ratio",
        "* `init_price_ratio` - Current price ratio"
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
          "name": "priceManager",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Price manager account. Create this account if an emitter has not been",
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
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock used for price manager."
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
        },
        {
          "name": "normalizedDstBaseGasLe",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "normalizedDstGasPerBytesLe",
          "type": {
            "array": [
              "u8",
              32
            ]
          }
        },
        {
          "name": "priceManagerOwner",
          "type": "publicKey"
        },
        {
          "name": "initPriceRatio",
          "type": "u64"
        }
      ]
    },
    {
      "name": "setPriceRatio",
      "docs": [
        "Set the target chain price ratio",
        "Note: the owner of PriceManager can be overwrite by register_foreign_contract"
      ],
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "Owner of the program set in the [`PriceManager`] account. Signer for",
            "updating [`PriceManager`] account."
          ]
        },
        {
          "name": "priceManager",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Price Manager account."
          ]
        },
        {
          "name": "clock",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Clock used for price manager."
          ]
        }
      ],
      "args": [
        {
          "name": "chain",
          "type": "u16"
        },
        {
          "name": "newPriceRatio",
          "type": "u64"
        }
      ]
    },
    {
      "name": "soSwapNativeWithoutSwap",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "completeSoSwapNativeWithoutSwap",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
        },
        {
          "name": "skipVerifySoswapMessage",
          "type": "bool"
        }
      ]
    },
    {
      "name": "soSwapWrappedWithoutSwap",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "completeSoSwapWrappedWithoutSwap",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
        },
        {
          "name": "skipVerifySoswapMessage",
          "type": "bool"
        }
      ]
    },
    {
      "name": "estimateRelayerFee",
      "accounts": [
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign contract account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data.",
            "Query bridge.config.fee"
          ]
        }
      ],
      "args": [
        {
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "swapDataDst",
          "type": "bytes"
        }
      ],
      "returns": {
        "defined": "(u64,u64,u128)"
      }
    },
    {
      "name": "soSwapNativeWithWhirlpool",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
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
          "name": "tokenBridgeCustodySigner",
          "isMut": false,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "soSwapWrappedWithWhirlpool",
      "docs": [
        "Precondition: request has been posted"
      ],
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
          "name": "request",
          "isMut": true,
          "isSigner": false
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
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "beneficiaryAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
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
      "args": []
    },
    {
      "name": "completeSoSwapNativeWithWhirlpool",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
          ]
        },
        {
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
            "Recipient associated token account.",
            "If swap ok, transfer the receiving token to this account"
          ]
        },
        {
          "name": "recipientBridgeTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account.",
            "If swap failed, transfer the bridge token to this account"
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
      "name": "completeSoSwapWrappedWithWhirlpool",
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
            "Redeemer Config account. Acts as the Token Bridge redeemer, which signs",
            "for the complete transfer instruction. Read-only."
          ]
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "beneficiaryTokenAccount",
          "isMut": true,
          "isSigner": false
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
          "name": "whirlpoolProgram",
          "isMut": false,
          "isSigner": false
        },
        {
          "name": "whirlpoolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountA",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultA",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTokenOwnerAccountB",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Payer's associated token account."
          ]
        },
        {
          "name": "whirlpoolTokenVaultB",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray0",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray1",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolTickArray2",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "whirlpoolOracle",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Oracle is currently unused and will be enabled on subsequent updates"
          ]
        },
        {
          "name": "unwrapSolAccount",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false,
          "isOptional": true
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false,
          "isOptional": true
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
            "Recipient associated token account.",
            "If swap ok, transfer the receiving token to this account"
          ]
        },
        {
          "name": "recipientBridgeTokenAccount",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Recipient associated token account.",
            "If swap failed, transfer the bridge token to this account"
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
    },
    {
      "name": "setRedeemProxy",
      "accounts": [
        {
          "name": "owner",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account."
          ]
        }
      ],
      "args": [
        {
          "name": "newProxy",
          "type": "publicKey"
        }
      ]
    },
    {
      "name": "soSwapPostCrossRequest",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "The requester"
          ]
        },
        {
          "name": "config",
          "isMut": true,
          "isSigner": false,
          "docs": [
            "Sender Config account"
          ]
        },
        {
          "name": "request",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "feeConfig",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "SoFee Config account. Read-only."
          ]
        },
        {
          "name": "foreignContract",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Foreign contract account. Read-only."
          ]
        },
        {
          "name": "priceManager",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Price Manager account. Read-only."
          ]
        },
        {
          "name": "wormholeBridge",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Wormhole bridge data.",
            "Query bridge.config.fee"
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
          "name": "soData",
          "type": "bytes"
        },
        {
          "name": "swapDataSrc",
          "type": "bytes"
        },
        {
          "name": "wormholeData",
          "type": "bytes"
        },
        {
          "name": "swapDataDst",
          "type": "bytes"
        }
      ],
      "returns": "u64"
    },
    {
      "name": "soSwapClosePendingRequest",
      "docs": [
        "Close the pending cross request.",
        "The remaining lamports will be refunded to the requester"
      ],
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true,
          "docs": [
            "The requester or proxy"
          ]
        },
        {
          "name": "recipient",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "config",
          "isMut": false,
          "isSigner": false,
          "docs": [
            "Redeemer Config account."
          ]
        },
        {
          "name": "request",
          "isMut": true,
          "isSigner": false
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
      "args": []
    },
    {
      "name": "wrapSol",
      "accounts": [
        {
          "name": "payer",
          "isMut": true,
          "isSigner": true
        },
        {
          "name": "wrapSolAccount",
          "isMut": true,
          "isSigner": false
        },
        {
          "name": "wsolMint",
          "isMut": false,
          "isSigner": false
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
          "name": "amountToBeWrapped",
          "type": "u64"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "crossRequest",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "The SenderConfig address."
            ],
            "type": "publicKey"
          },
          {
            "name": "payer",
            "docs": [
              "The requester."
            ],
            "type": "publicKey"
          },
          {
            "name": "nonce",
            "docs": [
              "The SenderConfig nonce."
            ],
            "type": "u64"
          },
          {
            "name": "soData",
            "docs": [
              "The cross data."
            ],
            "type": "bytes"
          },
          {
            "name": "swapDataSrc",
            "type": "bytes"
          },
          {
            "name": "wormholeData",
            "type": "bytes"
          },
          {
            "name": "swapDataDst",
            "type": "bytes"
          }
        ]
      }
    },
    {
      "name": "soFeeConfig",
      "docs": [
        "The so fee of cross token"
      ],
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
            "name": "beneficiary",
            "docs": [
              "The recipient of [relayer_fee + so_fee]."
            ],
            "type": "publicKey"
          },
          {
            "name": "soFee",
            "docs": [
              "SoFee by RAY"
            ],
            "type": "u64"
          },
          {
            "name": "actualReserve",
            "docs": [
              "Actual relayer fee scale factor"
            ],
            "type": "u64"
          },
          {
            "name": "estimateReserve",
            "docs": [
              "Estimate relayer fee scale factor"
            ],
            "type": "u64"
          }
        ]
      }
    },
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
              "Emitter address. Cannot be zero address.",
              "Left-zero-padded if shorter than 32 bytes"
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
          },
          {
            "name": "normalizedDstBaseGas",
            "docs": [
              "Normalized target chain minimum consumption of gas"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          },
          {
            "name": "normalizedDstGasPerBytes",
            "docs": [
              "Normalized target chain gas per bytes"
            ],
            "type": {
              "array": [
                "u8",
                32
              ]
            }
          }
        ]
      }
    },
    {
      "name": "priceManager",
      "type": {
        "kind": "struct",
        "fields": [
          {
            "name": "owner",
            "docs": [
              "Who can update current_price_ratio"
            ],
            "type": "publicKey"
          },
          {
            "name": "currentPriceRatio",
            "docs": [
              "The currnet price ratio of native coins"
            ],
            "type": "u64"
          },
          {
            "name": "lastUpdateTimestamp",
            "type": "u64"
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
            "name": "proxy",
            "docs": [
              "Proxy account"
            ],
            "type": "publicKey"
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
            "name": "nonce",
            "docs": [
              "Used for cross request."
            ],
            "type": "u64"
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
    },
    {
      "code": 6026,
      "name": "InvalidDataLength",
      "msg": "InvalidDataLength"
    },
    {
      "code": 6027,
      "name": "DeserializeSoSwapMessageFail",
      "msg": "DeserializeSoSwapMessageFail"
    },
    {
      "code": 6028,
      "name": "InvalidBeneficiary",
      "msg": "InvalidBeneficiary"
    },
    {
      "code": 6029,
      "name": "CheckFeeFail",
      "msg": "CheckFeeFail"
    },
    {
      "code": 6030,
      "name": "UnexpectValue",
      "msg": "UnexpectValue"
    },
    {
      "code": 6031,
      "name": "InvalidCallData",
      "msg": "InvalidCallData"
    },
    {
      "code": 6032,
      "name": "InvalidProxy",
      "msg": "InvalidProxy"
    }
  ]
};
