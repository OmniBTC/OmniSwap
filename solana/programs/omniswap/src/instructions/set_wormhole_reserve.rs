use anchor_lang::prelude::*;

use crate::{error::SoSwapError, state::SoFeeConfig};

#[derive(Accounts)]
pub struct SetWormholeReserve<'info> {
	#[account(mut)]
	/// Whoever initializes the config will be the owner of the program. Signer
	/// for creating the [`SenderConfig`],[`RedeemerConfig`] and [`SoFeeConfig`] accounts.
	pub owner: Signer<'info>,

	#[account(
		mut,
		has_one = owner @ SoSwapError::OwnerOnly,
		seeds = [SoFeeConfig::SEED_PREFIX],
		bump
	)]
	/// Sender Config account.
	pub config: Box<Account<'info, SoFeeConfig>>,
}

pub fn handler(
	ctx: Context<SetWormholeReserve>,
	actual_reserve: u64,
	estimate_reserve: u64,
) -> Result<()> {
	let config = &mut ctx.accounts.config;
	config.actual_reserve = actual_reserve;
	config.estimate_reserve = estimate_reserve;

	// Done.
	Ok(())
}
