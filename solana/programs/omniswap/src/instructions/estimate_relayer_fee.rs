use anchor_lang::prelude::*;
use spl_math::uint::U256;
use wormhole_anchor_sdk::wormhole;

use crate::{
	constants::RAY,
	cross::*,
	SoSwapError,
	state::{ForeignContract, PriceManager, SoFeeConfig}
};

#[derive(Accounts)]
#[instruction(chain: u16)]
pub struct EstimateRelayerFee<'info> {
	#[account(
		seeds = [SoFeeConfig::SEED_PREFIX],
		bump,
	)]
	/// SoFee Config account. Read-only.
	pub fee_config: Box<Account<'info, SoFeeConfig>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&chain.to_le_bytes()[..]
		],
		bump,
	)]
	/// Foreign contract account. Read-only.
	pub foreign_contract: Box<Account<'info, ForeignContract>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&chain.to_le_bytes()[..],
			PriceManager::SEED_PREFIX
		],
		bump
	)]
	/// Price Manager account. Read-only.
	pub price_manager: Box<Account<'info, PriceManager>>,

	/// Wormhole bridge data.
	/// Query bridge.config.fee
	pub wormhole_bridge: Box<Account<'info, wormhole::BridgeData>>,
}

pub fn handler(
	ctx: Context<EstimateRelayerFee>,
	chain_id: u16,
	so_data: Vec<u8>,
	wormhole_data: Vec<u8>,
	swap_data_dst: Vec<u8>,
) -> Result<(u64, u64, u128)> {
	let parsed_so_data = NormalizedSoData::decode_normalized_so_data(&so_data)?;
	let parsed_wormhole_data =
		NormalizedWormholeData::decode_normalized_wormhole_data(&wormhole_data)?;
	let parsed_swap_data_dst = NormalizedSwapData::decode_normalized_swap_data(&swap_data_dst)?;

	let estimate_reserve = U256::from(ctx.accounts.fee_config.estimate_reserve);

	let ratio = ctx.accounts.price_manager.current_price_ratio;

	let dst_max_gas = ctx.accounts.foreign_contract.estimate_complete_soswap_gas(
		&NormalizedSoData::encode_normalized_so_data(&parsed_so_data),
		&parsed_wormhole_data,
		&NormalizedSwapData::encode_normalized_swap_data(&parsed_swap_data_dst),
	);

	let dst_fee = parsed_wormhole_data
		.dst_max_gas_price_in_wei_for_relayer
		.checked_mul(dst_max_gas)
		.unwrap();

	let one = U256::from(RAY);
	let mut src_fee = dst_fee
		.checked_mul(U256::from(ratio))
		.unwrap()
		.checked_div(one)
		.unwrap()
		.checked_mul(estimate_reserve)
		.unwrap()
		.checked_div(one)
		.unwrap();

	// Solana decimals = 9
	if chain_id == 22 {
		// Aptos chain, decimals=8
		// decimal * 10
		src_fee = src_fee.checked_mul(10u64.into()).unwrap();
	} else {
		// Evm chain, decimals=18
		// decimal / 1e9
		src_fee = src_fee.checked_div(1_000_000_000u64.into()).unwrap();
	};

	let mut consume_value = ctx.accounts.wormhole_bridge.config.fee;

	let src_fee = src_fee.as_u64();
	consume_value += src_fee;

	require!(
		dst_max_gas < U256::from(u128::MAX),
		SoSwapError::UnexpectValue
	);

	Ok((src_fee, consume_value, dst_max_gas.as_u128()))
}
