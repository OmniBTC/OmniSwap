use anchor_lang::prelude::*;

use crate::{
	error::SoSwapError,
	state::{ForeignContract, PriceManager},
};

#[derive(Accounts)]
#[instruction(chain: u16)]
pub struct SetPriceManager<'info> {
	#[account(mut)]
	/// Owner of the program set in the [`PriceManager`] account. Signer for
	/// updating [`PriceManager`] account.
	pub owner: Signer<'info>,

	#[account(
		mut,
		has_one = owner @ SoSwapError::OwnerOnly,
		seeds = [
			ForeignContract::SEED_PREFIX,
			&chain.to_le_bytes()[..],
			PriceManager::SEED_PREFIX
		],
		bump
	)]
	/// Price Manager account.
	pub price_manager: Box<Account<'info, PriceManager>>,

	/// Clock used for price manager.
	pub clock: Sysvar<'info, Clock>,
}

pub fn handler(ctx: Context<SetPriceManager>, _chain: u16, new_price_ratio: u64) -> Result<()> {
	let price_manager = &mut ctx.accounts.price_manager;
	price_manager.current_price_ratio = new_price_ratio;
	price_manager.last_update_timestamp = ctx.accounts.clock.unix_timestamp as u64;

	// Done.
	Ok(())
}
