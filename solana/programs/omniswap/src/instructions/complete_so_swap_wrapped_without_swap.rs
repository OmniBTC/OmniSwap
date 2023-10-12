use anchor_lang::prelude::*;
use wormhole_anchor_sdk::token_bridge;

use crate::{
	context::CompleteSoSwapWrappedWithoutSwap, error::SoSwapError,
	state::redeemer_config::RedeemerConfig,
};

pub fn handler(
	ctx: Context<CompleteSoSwapWrappedWithoutSwap>,
	_vaa_hash: [u8; 32],
	skip_verify_soswap_message: bool,
) -> Result<()> {
	// The Token Bridge program's claim account is only initialized when
	// a transfer is redeemed (and the boolean value `true` is written as
	// its data).
	//
	// The Token Bridge program will automatically fail if this transfer
	// is redeemed again. But we choose to short-circuit the failure as the
	// first evaluation of this instruction.
	require!(ctx.accounts.token_bridge_claim.data_is_empty(), SoSwapError::AlreadyRedeemed);

	if skip_verify_soswap_message && ctx.accounts.payer.key() == ctx.accounts.config.owner {
		return complete_transfer(&ctx)
	}

	// The intended recipient must agree with the recipient.
	// TODO: dst swap
	let soswap_message = ctx.accounts.vaa.message().data();
	require!(*soswap_message != Default::default(), SoSwapError::DeserializeSoSwapMessageFail);
	require!(
		ctx.accounts.recipient.key().to_bytes() == soswap_message.recipient(),
		SoSwapError::InvalidRecipient
	);

	complete_transfer(&ctx)
}

fn complete_transfer(ctx: &Context<CompleteSoSwapWrappedWithoutSwap>) -> Result<()> {
	// These seeds are used to:
	// 1.  Redeem Token Bridge program's
	//     complete_transfer_wrapped_with_payload.
	// 2.  Transfer tokens to recipient.
	// 3.  Close tmp_token_account.
	let config_seeds = &[RedeemerConfig::SEED_PREFIX.as_ref(), &[ctx.accounts.config.bump]];

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
