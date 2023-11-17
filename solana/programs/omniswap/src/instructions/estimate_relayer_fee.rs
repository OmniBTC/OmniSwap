use anchor_lang::prelude::*;
use wormhole_anchor_sdk::wormhole;

use super::relayer_fee::EstRelayerFee;
use crate::{
	cross::*,
	state::{ForeignContract, PriceManager, SoFeeConfig},
};

#[derive(Accounts)]
#[instruction(
	so_data: Vec<u8>,
	wormhole_data: Vec<u8>,
)]
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
			&NormalizedWormholeData::parse_chain_id(wormhole_data.as_slice())?.to_le_bytes()[..]
		],
		bump,
	)]
	/// Foreign contract account. Read-only.
	pub foreign_contract: Box<Account<'info, ForeignContract>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&NormalizedWormholeData::parse_chain_id(wormhole_data.as_slice())?.to_le_bytes()[..],
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

impl<'info> EstRelayerFee<'info> for Context<'_, '_, '_, '_, EstimateRelayerFee<'info>> {
	fn fee_config(&self) -> &Account<'info, SoFeeConfig> {
		self.accounts.fee_config.as_ref()
	}

	fn price_manager(&self) -> &Account<'info, PriceManager> {
		self.accounts.price_manager.as_ref()
	}

	fn foreign_contract(&self) -> &Account<'info, ForeignContract> {
		self.accounts.foreign_contract.as_ref()
	}

	fn wormhole_bridge(&self) -> &Account<'info, wormhole::BridgeData> {
		self.accounts.wormhole_bridge.as_ref()
	}
}

pub fn handler(
	ctx: Context<EstimateRelayerFee>,
	so_data: Vec<u8>,
	wormhole_data: Vec<u8>,
	swap_data_dst: Vec<u8>,
) -> Result<(u64, u64, u128)> {
	let parsed_so_data = NormalizedSoData::decode_compact_so_data(&so_data)?;
	let parsed_wormhole_data =
		NormalizedWormholeData::decode_compact_wormhole_data(&wormhole_data)?;
	let parsed_swap_data_dst = NormalizedSwapData::decode_normalized_swap_data(&swap_data_dst)?;

	EstRelayerFee::estimate_fee(&ctx, &parsed_so_data, &parsed_wormhole_data, &parsed_swap_data_dst)
}
