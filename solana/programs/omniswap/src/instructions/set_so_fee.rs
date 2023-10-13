use anchor_lang::prelude::*;

use crate::context::SetSoFee;

pub fn handler(ctx: Context<SetSoFee>, so_fee_by_ray: u64) -> Result<()> {
	let config = &mut ctx.accounts.config;
	config.so_fee = so_fee_by_ray;

	// Done.
	Ok(())
}
