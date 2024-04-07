use anchor_lang::prelude::*;

use crate::{error::SoSwapError, state::RedeemerConfig};

#[derive(Accounts)]
pub struct SetRedeemProxy<'info> {
	#[account(mut)]
	pub owner: Signer<'info>,

	#[account(
		mut,
		seeds = [RedeemerConfig::SEED_PREFIX],
		bump,
		has_one = owner @ SoSwapError::OwnerOnly,
	)]
	/// Sender Config account.
	pub config: Box<Account<'info, RedeemerConfig>>,
}

pub fn handler(ctx: Context<SetRedeemProxy>, new_proxy: Pubkey) -> Result<()> {
	let config = &mut ctx.accounts.config;
	config.proxy = new_proxy;

	// Done.
	Ok(())
}
