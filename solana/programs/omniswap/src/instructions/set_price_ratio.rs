use anchor_lang::prelude::*;

use crate::context::SetPriceManager;

pub fn handler(
    ctx: Context<SetPriceManager>,
    _chain: u16,
    new_price_ratio: u64,
) -> Result<()> {
    let price_manager = &mut ctx.accounts.price_manager;
    price_manager.current_price_ratio = new_price_ratio;
    price_manager.last_update_timestamp = ctx.accounts.clock.unix_timestamp as u64;

    // Done.
    Ok(())
}