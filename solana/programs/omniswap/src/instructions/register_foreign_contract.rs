use anchor_lang::prelude::*;
use wormhole_anchor_sdk::wormhole;

use crate::{context::RegisterForeignContract, error::SoSwapError};

pub fn handler(
	ctx: Context<RegisterForeignContract>,
	chain: u16,
	address: [u8; 32],
	normalized_dst_base_gas_le: [u8; 32],
	normalized_dst_gas_per_bytes_le: [u8; 32],
	price_manager_owner: Pubkey,
	init_price_ratio: u64,
) -> Result<()> {
	// Foreign emitter cannot share the same Wormhole Chain ID as the
	// Solana Wormhole program's. And cannot register a zero address.
	require!(
		chain > 0 && chain != wormhole::CHAIN_ID_SOLANA && !address.iter().all(|&x| x == 0),
		SoSwapError::InvalidForeignContract,
	);

	// Save the emitter info into the ForeignEmitter account.
	let emitter = &mut ctx.accounts.foreign_contract;
	emitter.chain = chain;
	emitter.address = address;
	emitter.token_bridge_foreign_endpoint = ctx.accounts.token_bridge_foreign_endpoint.key();
	emitter.normalized_dst_base_gas = normalized_dst_base_gas_le;
	emitter.normalized_dst_gas_per_bytes = normalized_dst_gas_per_bytes_le;

	let price_manager = &mut ctx.accounts.price_manager;
	price_manager.owner = price_manager_owner;
	price_manager.current_price_ratio = init_price_ratio;
	price_manager.last_update_timestamp = ctx.accounts.clock.unix_timestamp as u64;

	// Done.
	Ok(())
}
