use anchor_lang::prelude::*;

use crate::{error::SoSwapError, state::SoFeeConfig};

#[derive(Accounts)]
pub struct SetSoFee<'info> {
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

pub fn handler(ctx: Context<SetSoFee>, so_fee_by_ray: u64) -> Result<()> {
	let config = &mut ctx.accounts.config;
	config.so_fee = so_fee_by_ray;

	// Done.
	Ok(())
}
