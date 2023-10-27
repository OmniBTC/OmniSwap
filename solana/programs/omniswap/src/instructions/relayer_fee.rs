use anchor_lang::{
	prelude::*, solana_program::account_info::AccountInfo, system_program::Transfer,
};
use spl_math::uint::U256;
use wormhole_anchor_sdk::wormhole::{BridgeData, CHAIN_ID_SOLANA};

use crate::{
	cross::{NormalizedSoData, NormalizedSwapData, NormalizedWormholeData},
	error::SoSwapError,
	ForeignContract, PriceManager, SoFeeConfig, RAY,
};

pub trait CheckRelayerFee<'info> {
	fn fee_config(&self) -> &Account<'info, SoFeeConfig>;
	fn price_manager(&self) -> &Account<'info, PriceManager>;
	fn foreign_contract(&self) -> &Account<'info, ForeignContract>;
	fn wormhole_bridge(&self) -> &Account<'info, BridgeData>;
	fn system_program(&self) -> AccountInfo<'info>;
	fn fee_collector(&self) -> AccountInfo<'info>;
	fn payer(&self) -> AccountInfo<'info>;
	fn charge_relayer_fee(&self, relayer_fee: u64) -> Result<()> {
		// Pay fee
		anchor_lang::system_program::transfer(
			CpiContext::new(
				self.system_program(),
				Transfer { from: self.payer(), to: self.fee_collector() },
			),
			relayer_fee,
		)
	}

	fn check_wormhole_data(&self, parsed_wormhole_data: &NormalizedWormholeData) -> Result<u16> {
		let recipient_chain = parsed_wormhole_data.dst_wormhole_chain_id;

		require!(
			recipient_chain > 0 &&
				recipient_chain != CHAIN_ID_SOLANA &&
				!parsed_wormhole_data.dst_so_diamond.iter().all(|&x| x == 0) &&
				parsed_wormhole_data.dst_so_diamond == self.foreign_contract().address.to_vec(),
			SoSwapError::InvalidRecipient,
		);

		Ok(recipient_chain)
	}
}

pub fn check_relayer_fee<'info, S: CheckRelayerFee<'info>>(
	ctx: &S,
	parsed_wormhole_data: &NormalizedWormholeData,
	parsed_so_data: &NormalizedSoData,
	parsed_swap_data_dst: &Vec<NormalizedSwapData>,
) -> Result<(bool, u64, u64, U256)> {
	let actual_reserve = U256::from(S::fee_config(ctx).actual_reserve);

	let ratio = S::price_manager(ctx).current_price_ratio;

	let dst_max_gas = S::foreign_contract(ctx).estimate_complete_soswap_gas(
		&NormalizedSoData::encode_normalized_so_data(parsed_so_data),
		parsed_wormhole_data,
		&NormalizedSwapData::encode_normalized_swap_data(parsed_swap_data_dst),
	);

	let dst_fee = parsed_wormhole_data
		.dst_max_gas_price_in_wei_for_relayer
		.checked_mul(dst_max_gas)
		.unwrap();
	let recipient_chain = parsed_wormhole_data.dst_wormhole_chain_id;

	let one = U256::from(RAY);
	let mut src_fee = dst_fee
		.checked_mul(U256::from(ratio))
		.unwrap()
		.checked_div(one)
		.unwrap()
		.checked_mul(actual_reserve)
		.unwrap()
		.checked_div(one)
		.unwrap();

	// Solana decimals = 9
	if recipient_chain == 22 {
		// Aptos chain, decimals=8
		// decimal * 10
		src_fee = src_fee.checked_mul(10u64.into()).unwrap();
	} else {
		// Evm chain, decimals=18
		// decimal / 1e9
		src_fee = src_fee.checked_div(1_000_000_000u64.into()).unwrap();
	};

	let mut consume_value = S::wormhole_bridge(ctx).config.fee;

	let src_fee = src_fee.as_u64();
	consume_value += src_fee;

	let mut flag = false;

	let wormhole_fee = parsed_wormhole_data.wormhole_fee.as_u64();
	if consume_value <= wormhole_fee {
		flag = true;
	};

	Ok((flag, src_fee, consume_value, dst_max_gas))
}

pub trait EstRelayerFee<'info> {
	fn fee_config(&self) -> &Account<'info, SoFeeConfig>;
	fn price_manager(&self) -> &Account<'info, PriceManager>;
	fn foreign_contract(&self) -> &Account<'info, ForeignContract>;
	fn wormhole_bridge(&self) -> &Account<'info, BridgeData>;

	fn estimate_fee(
		&self,
		parsed_so_data: &NormalizedSoData,
		parsed_wormhole_data: &NormalizedWormholeData,
		parsed_swap_data_dst: &Vec<NormalizedSwapData>,
	) -> Result<(u64, u64, u128)> {
		let recipient_chain = parsed_wormhole_data.dst_wormhole_chain_id;

		let estimate_reserve = U256::from(self.fee_config().estimate_reserve);

		let ratio = self.price_manager().current_price_ratio;

		let dst_max_gas = self.foreign_contract().estimate_complete_soswap_gas(
			&NormalizedSoData::encode_normalized_so_data(parsed_so_data),
			parsed_wormhole_data,
			&NormalizedSwapData::encode_normalized_swap_data(parsed_swap_data_dst),
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
		if recipient_chain == 22 {
			// Aptos chain, decimals=8
			// decimal * 10
			src_fee = src_fee.checked_mul(10u64.into()).unwrap();
		} else {
			// Evm chain, decimals=18
			// decimal / 1e9
			src_fee = src_fee.checked_div(1_000_000_000u64.into()).unwrap();
		};

		let consume_value = self.wormhole_bridge().config.fee;

		let src_fee = src_fee.as_u64();

		require!(dst_max_gas < U256::from(u128::MAX), SoSwapError::UnexpectValue);

		msg!(
			"[EstimateRelayerFee]: relayer_fee={}, wormhole_fee={}, dst_max_gas={}, dst_chain={}",
			src_fee,
			consume_value,
			dst_max_gas,
			recipient_chain
		);

		Ok((src_fee, consume_value, dst_max_gas.as_u128()))
	}
}
