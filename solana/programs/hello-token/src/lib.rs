use anchor_lang::prelude::*;

pub use context::*;
pub use error::*;
pub use message::*;
pub use state::*;

pub mod context;
pub mod error;
pub mod message;
pub mod state;

declare_id!("EvTsJYjLKCK1iMX9aExiYEBxdNBGgY8FQ7NFRd2jJNk5");

#[program]
pub mod hello_token {
    use super::*;
    use wormhole_anchor_sdk::{token_bridge, wormhole};

    /// This instruction can be used to generate your program's config.
    /// And for convenience, we will store Wormhole-related PDAs in the
    /// config so we can verify these accounts with a simple == constraint.
    pub fn initialize(
        ctx: Context<Initialize>,
        relayer_fee: u32,
        relayer_fee_precision: u32,
    ) -> Result<()> {
        require!(
            relayer_fee < relayer_fee_precision,
            HelloTokenError::InvalidRelayerFee,
        );

        // Initialize program's sender config
        let sender_config = &mut ctx.accounts.sender_config;

        // Set the owner of the sender config (effectively the owner of the
        // program).
        sender_config.owner = ctx.accounts.owner.key();
        sender_config.bump = *ctx
            .bumps
            .get("sender_config")
            .ok_or(HelloTokenError::BumpNotFound)?;

        // Set Token Bridge related addresses.
        {
            let token_bridge = &mut sender_config.token_bridge;
            token_bridge.config = ctx.accounts.token_bridge_config.key();
            token_bridge.authority_signer = ctx.accounts.token_bridge_authority_signer.key();
            token_bridge.custody_signer = ctx.accounts.token_bridge_custody_signer.key();
            token_bridge.emitter = ctx.accounts.token_bridge_emitter.key();
            token_bridge.sequence = ctx.accounts.token_bridge_sequence.key();
            token_bridge.wormhole_bridge = ctx.accounts.wormhole_bridge.key();
            token_bridge.wormhole_fee_collector = ctx.accounts.wormhole_fee_collector.key();
        }

        // Initialize program's redeemer config
        let redeemer_config = &mut ctx.accounts.redeemer_config;

        // Set the owner of the redeemer config (effectively the owner of the
        // program).
        redeemer_config.owner = ctx.accounts.owner.key();
        redeemer_config.bump = *ctx
            .bumps
            .get("redeemer_config")
            .ok_or(HelloTokenError::BumpNotFound)?;
        redeemer_config.relayer_fee = relayer_fee;
        redeemer_config.relayer_fee_precision = relayer_fee_precision;

        // Set Token Bridge related addresses.
        {
            let token_bridge = &mut redeemer_config.token_bridge;
            token_bridge.config = ctx.accounts.token_bridge_config.key();
            token_bridge.custody_signer = ctx.accounts.token_bridge_custody_signer.key();
            token_bridge.mint_authority = ctx.accounts.token_bridge_mint_authority.key();
        }

        // Done.
        Ok(())
    }

    /// This instruction registers a new foreign contract (from another
    /// network) and saves the emitter information in a ForeignEmitter account.
    /// This instruction is owner-only, meaning that only the owner of the
    /// program (defined in the [Config] account) can add and update foreign
    /// contracts.
    ///
    /// # Arguments
    ///
    /// * `ctx`     - `RegisterForeignContract` context
    /// * `chain`   - Wormhole Chain ID
    /// * `address` - Wormhole Emitter Address
    pub fn register_foreign_contract(
        ctx: Context<RegisterForeignContract>,
        chain: u16,
        address: [u8; 32],
    ) -> Result<()> {
        // Foreign emitter cannot share the same Wormhole Chain ID as the
        // Solana Wormhole program's. And cannot register a zero address.
        require!(
            chain > 0 && chain != wormhole::CHAIN_ID_SOLANA && !address.iter().all(|&x| x == 0),
            HelloTokenError::InvalidForeignContract,
        );

        // Save the emitter info into the ForeignEmitter account.
        let emitter = &mut ctx.accounts.foreign_contract;
        emitter.chain = chain;
        emitter.address = address;
        emitter.token_bridge_foreign_endpoint = ctx.accounts.token_bridge_foreign_endpoint.key();

        // Done.
        Ok(())
    }

    pub fn update_relayer_fee(
        ctx: Context<UpdateRelayerFee>,
        relayer_fee: u32,
        relayer_fee_precision: u32,
    ) -> Result<()> {
        require!(
            relayer_fee < relayer_fee_precision,
            HelloTokenError::InvalidRelayerFee,
        );

        let config = &mut ctx.accounts.config;
        config.relayer_fee = relayer_fee;
        config.relayer_fee_precision = relayer_fee_precision;

        // Done.
        Ok(())
    }

    pub fn send_native_tokens_with_payload(
        ctx: Context<SendNativeTokensWithPayload>,
        batch_id: u32,
        amount: u64,
        recipient_address: [u8; 32],
        recipient_chain: u16,
    ) -> Result<()> {
        // Token Bridge program truncates amounts to 8 decimals, so there will
        // be a residual amount if decimals of SPL is >8. We need to take into
        // account how much will actually be bridged.
        let truncated_amount = token_bridge::truncate_amount(amount, ctx.accounts.mint.decimals);
        require!(truncated_amount > 0, HelloTokenError::ZeroBridgeAmount);
        if truncated_amount != amount {
            msg!(
                "SendNativeTokensWithPayload :: truncating amount {} to {}",
                amount,
                truncated_amount
            );
        }

        require!(
            recipient_chain > 0
                && recipient_chain != wormhole::CHAIN_ID_SOLANA
                && !recipient_address.iter().all(|&x| x == 0),
            HelloTokenError::InvalidRecipient,
        );

        // These seeds are used to:
        // 1.  Sign the Sender Config's token account to delegate approval
        //     of truncated_amount.
        // 2.  Sign Token Bridge program's transfer_native instruction.
        // 3.  Close tmp_token_account.
        let config_seeds = &[
            SenderConfig::SEED_PREFIX.as_ref(),
            &[ctx.accounts.config.bump],
        ];

        // First transfer tokens from payer to tmp_token_account.
        anchor_spl::token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token::Transfer {
                    from: ctx.accounts.from_token_account.to_account_info(),
                    to: ctx.accounts.tmp_token_account.to_account_info(),
                    authority: ctx.accounts.payer.to_account_info(),
                },
            ),
            truncated_amount,
        )?;

        // Delegate spending to Token Bridge program's authority signer.
        anchor_spl::token::approve(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token::Approve {
                    to: ctx.accounts.tmp_token_account.to_account_info(),
                    delegate: ctx.accounts.token_bridge_authority_signer.to_account_info(),
                    authority: ctx.accounts.config.to_account_info(),
                },
                &[&config_seeds[..]],
            ),
            truncated_amount,
        )?;

        // Serialize HelloTokenMessage as encoded payload for Token Bridge
        // transfer.
        let payload = HelloTokenMessage::Hello {
            recipient: recipient_address,
        }
            .try_to_vec()?;

        // Bridge native token with encoded payload.
        token_bridge::transfer_native_with_payload(
            CpiContext::new_with_signer(
                ctx.accounts.token_bridge_program.to_account_info(),
                token_bridge::TransferNativeWithPayload {
                    payer: ctx.accounts.payer.to_account_info(),
                    config: ctx.accounts.token_bridge_config.to_account_info(),
                    from: ctx.accounts.tmp_token_account.to_account_info(),
                    mint: ctx.accounts.mint.to_account_info(),
                    custody: ctx.accounts.token_bridge_custody.to_account_info(),
                    authority_signer: ctx.accounts.token_bridge_authority_signer.to_account_info(),
                    custody_signer: ctx.accounts.token_bridge_custody_signer.to_account_info(),
                    wormhole_bridge: ctx.accounts.wormhole_bridge.to_account_info(),
                    wormhole_message: ctx.accounts.wormhole_message.to_account_info(),
                    wormhole_emitter: ctx.accounts.token_bridge_emitter.to_account_info(),
                    wormhole_sequence: ctx.accounts.token_bridge_sequence.to_account_info(),
                    wormhole_fee_collector: ctx.accounts.wormhole_fee_collector.to_account_info(),
                    clock: ctx.accounts.clock.to_account_info(),
                    sender: ctx.accounts.config.to_account_info(),
                    rent: ctx.accounts.rent.to_account_info(),
                    system_program: ctx.accounts.system_program.to_account_info(),
                    token_program: ctx.accounts.token_program.to_account_info(),
                    wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
                },
                &[
                    &config_seeds[..],
                    &[
                        SEED_PREFIX_BRIDGED,
                        &ctx.accounts
                            .token_bridge_sequence
                            .next_value()
                            .to_le_bytes()[..],
                        &[*ctx
                            .bumps
                            .get("wormhole_message")
                            .ok_or(HelloTokenError::BumpNotFound)?],
                    ],
                ],
            ),
            batch_id,
            truncated_amount,
            ctx.accounts.foreign_contract.address,
            recipient_chain,
            payload,
            &ctx.program_id.key(),
        )?;

        // Finish instruction by closing tmp_token_account.
        anchor_spl::token::close_account(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            anchor_spl::token::CloseAccount {
                account: ctx.accounts.tmp_token_account.to_account_info(),
                destination: ctx.accounts.payer.to_account_info(),
                authority: ctx.accounts.config.to_account_info(),
            },
            &[&config_seeds[..]],
        ))
    }

    pub fn redeem_native_transfer_with_payload(
        ctx: Context<RedeemNativeTransferWithPayload>,
        _vaa_hash: [u8; 32],
    ) -> Result<()> {
        // The Token Bridge program's claim account is only initialized when
        // a transfer is redeemed (and the boolean value `true` is written as
        // its data).
        //
        // The Token Bridge program will automatically fail if this transfer
        // is redeemed again. But we choose to short-circuit the failure as the
        // first evaluation of this instruction.
        require!(
            ctx.accounts.token_bridge_claim.data_is_empty(),
            HelloTokenError::AlreadyRedeemed
        );

        // The intended recipient must agree with the recipient.
        let HelloTokenMessage::Hello { recipient } = ctx.accounts.vaa.message().data();
        require!(
            ctx.accounts.recipient.key().to_bytes() == *recipient,
            HelloTokenError::InvalidRecipient
        );

        // These seeds are used to:
        // 1.  Redeem Token Bridge program's
        //     complete_transfer_native_with_payload.
        // 2.  Transfer tokens to relayer if he exists.
        // 3.  Transfer remaining tokens to recipient.
        // 4.  Close tmp_token_account.
        let config_seeds = &[
            RedeemerConfig::SEED_PREFIX.as_ref(),
            &[ctx.accounts.config.bump],
        ];

        // Redeem the token transfer.
        token_bridge::complete_transfer_native_with_payload(CpiContext::new_with_signer(
            ctx.accounts.token_bridge_program.to_account_info(),
            token_bridge::CompleteTransferNativeWithPayload {
                payer: ctx.accounts.payer.to_account_info(),
                config: ctx.accounts.token_bridge_config.to_account_info(),
                vaa: ctx.accounts.vaa.to_account_info(),
                claim: ctx.accounts.token_bridge_claim.to_account_info(),
                foreign_endpoint: ctx.accounts.token_bridge_foreign_endpoint.to_account_info(),
                to: ctx.accounts.tmp_token_account.to_account_info(),
                redeemer: ctx.accounts.config.to_account_info(),
                custody: ctx.accounts.token_bridge_custody.to_account_info(),
                mint: ctx.accounts.mint.to_account_info(),
                custody_signer: ctx.accounts.token_bridge_custody_signer.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                token_program: ctx.accounts.token_program.to_account_info(),
                wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
            },
            &[&config_seeds[..]],
        ))?;

        let amount = token_bridge::denormalize_amount(
            ctx.accounts.vaa.data().amount(),
            ctx.accounts.mint.decimals,
        );

        // If this instruction were executed by a relayer, send some of the
        // token amount (determined by the relayer fee) to the payer's token
        // account.
        if ctx.accounts.payer.key() != ctx.accounts.recipient.key() {
            // Does the relayer have an aassociated token account already? If
            // not, he needs to create one.
            require!(
                !ctx.accounts.payer_token_account.data_is_empty(),
                HelloTokenError::NonExistentRelayerAta
            );

            let relayer_amount = ctx.accounts.config.compute_relayer_amount(amount);

            // Pay the relayer if there is anything for him.
            if relayer_amount > 0 {
                anchor_spl::token::transfer(
                    CpiContext::new_with_signer(
                        ctx.accounts.token_program.to_account_info(),
                        anchor_spl::token::Transfer {
                            from: ctx.accounts.tmp_token_account.to_account_info(),
                            to: ctx.accounts.payer_token_account.to_account_info(),
                            authority: ctx.accounts.config.to_account_info(),
                        },
                        &[&config_seeds[..]],
                    ),
                    relayer_amount,
                )?;
            }

            msg!(
                "RedeemNativeTransferWithPayload :: relayed by {:?}",
                ctx.accounts.payer.key()
            );

            // Transfer tokens from tmp_token_account to recipient.
            anchor_spl::token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    anchor_spl::token::Transfer {
                        from: ctx.accounts.tmp_token_account.to_account_info(),
                        to: ctx.accounts.recipient_token_account.to_account_info(),
                        authority: ctx.accounts.config.to_account_info(),
                    },
                    &[&config_seeds[..]],
                ),
                amount - relayer_amount,
            )?;
        } else {
            // Transfer tokens from tmp_token_account to recipient.
            anchor_spl::token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    anchor_spl::token::Transfer {
                        from: ctx.accounts.tmp_token_account.to_account_info(),
                        to: ctx.accounts.recipient_token_account.to_account_info(),
                        authority: ctx.accounts.config.to_account_info(),
                    },
                    &[&config_seeds[..]],
                ),
                amount,
            )?;
        }

        // Finish instruction by closing tmp_token_account.
        anchor_spl::token::close_account(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            anchor_spl::token::CloseAccount {
                account: ctx.accounts.tmp_token_account.to_account_info(),
                destination: ctx.accounts.payer.to_account_info(),
                authority: ctx.accounts.config.to_account_info(),
            },
            &[&config_seeds[..]],
        ))
    }

    pub fn send_wrapped_tokens_with_payload(
        ctx: Context<SendWrappedTokensWithPayload>,
        batch_id: u32,
        amount: u64,
        recipient_address: [u8; 32],
        recipient_chain: u16,
    ) -> Result<()> {
        require!(amount > 0, HelloTokenError::ZeroBridgeAmount);
        require!(
            recipient_chain > 0
                && recipient_chain != wormhole::CHAIN_ID_SOLANA
                && !recipient_address.iter().all(|&x| x == 0),
            HelloTokenError::InvalidRecipient,
        );

        // These seeds are used to:
        // 1.  Sign the Sender Config's token account to delegate approval
        //     of amount.
        // 2.  Sign Token Bridge program's transfer_wrapped instruction.
        // 3.  Close tmp_token_account.
        let config_seeds = &[
            SenderConfig::SEED_PREFIX.as_ref(),
            &[ctx.accounts.config.bump],
        ];

        // First transfer tokens from payer to tmp_token_account.
        anchor_spl::token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token::Transfer {
                    from: ctx.accounts.from_token_account.to_account_info(),
                    to: ctx.accounts.tmp_token_account.to_account_info(),
                    authority: ctx.accounts.payer.to_account_info(),
                },
            ),
            amount,
        )?;

        // Delegate spending to Token Bridge program's authority signer.
        anchor_spl::token::approve(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token::Approve {
                    to: ctx.accounts.tmp_token_account.to_account_info(),
                    delegate: ctx.accounts.token_bridge_authority_signer.to_account_info(),
                    authority: ctx.accounts.config.to_account_info(),
                },
                &[&config_seeds[..]],
            ),
            amount,
        )?;

        // Serialize HelloTokenMessage as encoded payload for Token Bridge
        // transfer.
        let payload = HelloTokenMessage::Hello {
            recipient: recipient_address,
        }
            .try_to_vec()?;

        // Bridge wrapped token with encoded payload.
        token_bridge::transfer_wrapped_with_payload(
            CpiContext::new_with_signer(
                ctx.accounts.token_bridge_program.to_account_info(),
                token_bridge::TransferWrappedWithPayload {
                    payer: ctx.accounts.payer.to_account_info(),
                    config: ctx.accounts.token_bridge_config.to_account_info(),
                    from: ctx.accounts.tmp_token_account.to_account_info(),
                    from_owner: ctx.accounts.config.to_account_info(),
                    wrapped_mint: ctx.accounts.token_bridge_wrapped_mint.to_account_info(),
                    wrapped_metadata: ctx.accounts.token_bridge_wrapped_meta.to_account_info(),
                    authority_signer: ctx.accounts.token_bridge_authority_signer.to_account_info(),
                    wormhole_bridge: ctx.accounts.wormhole_bridge.to_account_info(),
                    wormhole_message: ctx.accounts.wormhole_message.to_account_info(),
                    wormhole_emitter: ctx.accounts.token_bridge_emitter.to_account_info(),
                    wormhole_sequence: ctx.accounts.token_bridge_sequence.to_account_info(),
                    wormhole_fee_collector: ctx.accounts.wormhole_fee_collector.to_account_info(),
                    clock: ctx.accounts.clock.to_account_info(),
                    sender: ctx.accounts.config.to_account_info(),
                    rent: ctx.accounts.rent.to_account_info(),
                    system_program: ctx.accounts.system_program.to_account_info(),
                    token_program: ctx.accounts.token_program.to_account_info(),
                    wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
                },
                &[
                    &config_seeds[..],
                    &[
                        SEED_PREFIX_BRIDGED,
                        &ctx.accounts
                            .token_bridge_sequence
                            .next_value()
                            .to_le_bytes()[..],
                        &[*ctx
                            .bumps
                            .get("wormhole_message")
                            .ok_or(HelloTokenError::BumpNotFound)?],
                    ],
                ],
            ),
            batch_id,
            amount,
            ctx.accounts.foreign_contract.address,
            recipient_chain,
            payload,
            &ctx.program_id.key(),
        )?;

        // Finish instruction by closing tmp_token_account.
        anchor_spl::token::close_account(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            anchor_spl::token::CloseAccount {
                account: ctx.accounts.tmp_token_account.to_account_info(),
                destination: ctx.accounts.payer.to_account_info(),
                authority: ctx.accounts.config.to_account_info(),
            },
            &[&config_seeds[..]],
        ))
    }

    pub fn redeem_wrapped_transfer_with_payload(
        ctx: Context<RedeemWrappedTransferWithPayload>,
        _vaa_hash: [u8; 32],
    ) -> Result<()> {
        // The Token Bridge program's claim account is only initialized when
        // a transfer is redeemed (and the boolean value `true` is written as
        // its data).
        //
        // The Token Bridge program will automatically fail if this transfer
        // is redeemed again. But we choose to short-circuit the failure as the
        // first evaluation of this instruction.
        require!(
            ctx.accounts.token_bridge_claim.data_is_empty(),
            HelloTokenError::AlreadyRedeemed
        );

        // The intended recipient must agree with the recipient.
        let HelloTokenMessage::Hello { recipient } = ctx.accounts.vaa.message().data();
        require!(
            ctx.accounts.recipient.key().to_bytes() == *recipient,
            HelloTokenError::InvalidRecipient
        );

        // These seeds are used to:
        // 1.  Redeem Token Bridge program's
        //     complete_transfer_wrapped_with_payload.
        // 2.  Transfer tokens to relayer if he exists.
        // 3.  Transfer remaining tokens to recipient.
        // 4.  Close tmp_token_account.
        let config_seeds = &[
            RedeemerConfig::SEED_PREFIX.as_ref(),
            &[ctx.accounts.config.bump],
        ];

        // Redeem the token transfer.
        token_bridge::complete_transfer_wrapped_with_payload(CpiContext::new_with_signer(
            ctx.accounts.token_bridge_program.to_account_info(),
            token_bridge::CompleteTransferWrappedWithPayload {
                payer: ctx.accounts.payer.to_account_info(),
                config: ctx.accounts.token_bridge_config.to_account_info(),
                vaa: ctx.accounts.vaa.to_account_info(),
                claim: ctx.accounts.token_bridge_claim.to_account_info(),
                foreign_endpoint: ctx.accounts.token_bridge_foreign_endpoint.to_account_info(),
                to: ctx.accounts.tmp_token_account.to_account_info(),
                redeemer: ctx.accounts.config.to_account_info(),
                wrapped_mint: ctx.accounts.token_bridge_wrapped_mint.to_account_info(),
                wrapped_metadata: ctx.accounts.token_bridge_wrapped_meta.to_account_info(),
                mint_authority: ctx.accounts.token_bridge_mint_authority.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                token_program: ctx.accounts.token_program.to_account_info(),
                wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
            },
            &[&config_seeds[..]],
        ))?;

        let amount = ctx.accounts.vaa.data().amount();

        // If this instruction were executed by a relayer, send some of the
        // token amount (determined by the relayer fee) to the payer's token
        // account.
        if ctx.accounts.payer.key() != ctx.accounts.recipient.key() {
            // Does the relayer have an aassociated token account already? If
            // not, he needs to create one.
            require!(
                !ctx.accounts.payer_token_account.data_is_empty(),
                HelloTokenError::NonExistentRelayerAta
            );

            let relayer_amount = ctx.accounts.config.compute_relayer_amount(amount);

            // Pay the relayer if there is anything for him.
            if relayer_amount > 0 {
                anchor_spl::token::transfer(
                    CpiContext::new_with_signer(
                        ctx.accounts.token_program.to_account_info(),
                        anchor_spl::token::Transfer {
                            from: ctx.accounts.tmp_token_account.to_account_info(),
                            to: ctx.accounts.payer_token_account.to_account_info(),
                            authority: ctx.accounts.config.to_account_info(),
                        },
                        &[&config_seeds[..]],
                    ),
                    relayer_amount,
                )?;
            }

            msg!(
                "RedeemWrappedTransferWithPayload :: relayed by {:?}",
                ctx.accounts.payer.key()
            );

            // Transfer tokens from tmp_token_account to recipient.
            anchor_spl::token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    anchor_spl::token::Transfer {
                        from: ctx.accounts.tmp_token_account.to_account_info(),
                        to: ctx.accounts.recipient_token_account.to_account_info(),
                        authority: ctx.accounts.config.to_account_info(),
                    },
                    &[&config_seeds[..]],
                ),
                amount - relayer_amount,
            )?;
        } else {
            // Transfer tokens from tmp_token_account to recipient.
            anchor_spl::token::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.token_program.to_account_info(),
                    anchor_spl::token::Transfer {
                        from: ctx.accounts.tmp_token_account.to_account_info(),
                        to: ctx.accounts.recipient_token_account.to_account_info(),
                        authority: ctx.accounts.config.to_account_info(),
                    },
                    &[&config_seeds[..]],
                ),
                amount,
            )?;
        }

        // Finish instruction by closing tmp_token_account.
        anchor_spl::token::close_account(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            anchor_spl::token::CloseAccount {
                account: ctx.accounts.tmp_token_account.to_account_info(),
                destination: ctx.accounts.payer.to_account_info(),
                authority: ctx.accounts.config.to_account_info(),
            },
            &[&config_seeds[..]],
        ))
    }
}
