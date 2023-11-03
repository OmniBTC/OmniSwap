use anchor_lang::prelude::*;

use crate::{cross_request::CrossRequest, RedeemerConfig, SoSwapError};

#[derive(Accounts)]
pub struct CloseRequest<'info> {
	#[account(mut)]
	/// The requester or proxy
	pub payer: Signer<'info>,

	#[account(mut)]
	/// CHECK: the requester
	pub recipient: UncheckedAccount<'info>,

	#[account(
		seeds = [RedeemerConfig::SEED_PREFIX],
		bump
	)]
	/// Redeemer Config account.
	pub config: Box<Account<'info, RedeemerConfig>>,

	#[account(mut, close = recipient)]
	pub request: Box<Account<'info, CrossRequest>>,

	/// System program.
	pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<CloseRequest>) -> Result<()> {
	require!(
		ctx.accounts.payer.key() == ctx.accounts.config.proxy ||
			ctx.accounts.payer.key() == ctx.accounts.request.payer,
		SoSwapError::OwnerOnly
	);

	Ok(())
}
