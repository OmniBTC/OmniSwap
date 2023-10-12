use anchor_lang::prelude::*;

use crate::context::SetWormholeReserve;

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
