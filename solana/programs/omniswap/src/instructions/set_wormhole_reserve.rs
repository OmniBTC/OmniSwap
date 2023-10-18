use anchor_lang::prelude::*;

use crate::{error::SoSwapError, state::SoFeeConfig};

#[derive(Accounts)]
pub struct SetWormholeReserve<'info> {
	#[account(mut)]
	pub payer: Signer<'info>,

	#[account(
		mut,
		seeds = [SoFeeConfig::SEED_PREFIX],
		bump,
		constraint = payer.key() == config.owner || payer.key() == config.beneficiary @ SoSwapError::OwnerOnly
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
