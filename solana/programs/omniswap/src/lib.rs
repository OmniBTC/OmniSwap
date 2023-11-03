#![allow(unknown_lints)]
#![allow(clippy::result_large_err)]

extern crate core;

use anchor_lang::prelude::*;

pub use constants::*;
pub use error::*;
pub use state::*;

pub mod constants;
pub mod cross;
pub mod dex;
pub mod error;
pub mod instructions;
pub mod message;
pub mod serde;
pub mod state;
pub mod utils;

declare_id!("4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY");

pub use wrap_sol::ID as WrapSOLKey;
mod wrap_sol {
	use super::*;
	declare_id!("So11111111111111111111111111111111111111112");
}

pub use unwrap_sol::ID as UnwrapSOLKey;
mod unwrap_sol {
	use super::*;
	declare_id!("11111111111111111111111111111111");
}

use instructions::*;

#[program]
pub mod omniswap {
	use super::*;

	/// This instruction can be used to generate your program's config.
	/// And for convenience, we will store Wormhole-related PDAs in the
	/// config so we can verify these accounts with a simple == constraint.
	pub fn initialize(
		ctx: Context<Initialize>,
		beneficiary: Pubkey,
		redeemer_proxy: Pubkey,
		actual_reserve: u64,
		estimate_reserve: u64,
		so_fee_by_ray: u64,
	) -> Result<()> {
		instructions::initialize::handler(
			ctx,
			beneficiary,
			redeemer_proxy,
			actual_reserve,
			estimate_reserve,
			so_fee_by_ray,
		)
	}

	/// Set relayer fee scale factor
	pub fn set_wormhole_reserve(
		ctx: Context<SetWormholeReserve>,
		actual_reserve: u64,
		estimate_reserve: u64,
	) -> Result<()> {
		instructions::set_wormhole_reserve::handler(ctx, actual_reserve, estimate_reserve)
	}

	/// Set so fee
	pub fn set_so_fee(ctx: Context<SetSoFee>, so_fee_by_ray: u64) -> Result<()> {
		instructions::set_so_fee::handler(ctx, so_fee_by_ray)
	}

	/// This instruction registers a new foreign contract (from another
	/// network) and saves the emitter information in a ForeignEmitter account
	/// and price ratio information in a PriceManager account.
	/// This instruction is owner-only, meaning that only the owner of the
	/// program (defined in the [Config] account) can add and update foreign
	/// contracts.
	///
	/// # Arguments
	///
	/// * `ctx`     - `RegisterForeignContract` context
	/// * `chain`   - Wormhole Chain ID
	/// * `address` - Wormhole Emitter Address. Left-zero-padded if shorter than 32 bytes
	/// * `normalized_dst_base_gas_le` - Normalized target chain minimum consumption of gas
	/// * `normalized_dst_gas_per_bytes_le` - Normalized target chain gas per bytes
	/// * `price_manager` - Who can update current_price_ratio
	/// * `init_price_ratio` - Current price ratio
	pub fn register_foreign_contract(
		ctx: Context<RegisterForeignContract>,
		chain: u16,
		address: [u8; 32],
		normalized_dst_base_gas_le: [u8; 32],
		normalized_dst_gas_per_bytes_le: [u8; 32],
		price_manager_owner: Pubkey,
		init_price_ratio: u64,
	) -> Result<()> {
		instructions::register_foreign_contract::handler(
			ctx,
			chain,
			address,
			normalized_dst_base_gas_le,
			normalized_dst_gas_per_bytes_le,
			price_manager_owner,
			init_price_ratio,
		)
	}

	/// Set the target chain price ratio
	/// Note: the owner of PriceManager can be overwrite by register_foreign_contract
	pub fn set_price_ratio(
		ctx: Context<SetPriceManager>,
		chain: u16,
		new_price_ratio: u64,
	) -> Result<()> {
		instructions::set_price_ratio::handler(ctx, chain, new_price_ratio)
	}

	/// Precondition: request has been posted
	pub fn so_swap_native_without_swap(ctx: Context<SoSwapNativeWithoutSwap>) -> Result<()> {
		instructions::so_swap_native_without_swap::handler(ctx)
	}

	pub fn complete_so_swap_native_without_swap(
		ctx: Context<CompleteSoSwapNativeWithoutSwap>,
		vaa_hash: [u8; 32],
		skip_verify_soswap_message: bool,
	) -> Result<()> {
		instructions::complete_so_swap_native_without_swap::handler(
			ctx,
			vaa_hash,
			skip_verify_soswap_message,
		)
	}

	/// Precondition: request has been posted
	pub fn so_swap_wrapped_without_swap(ctx: Context<SoSwapWrappedWithoutSwap>) -> Result<()> {
		instructions::so_swap_wrapped_without_swap::handler(ctx)
	}

	pub fn complete_so_swap_wrapped_without_swap(
		ctx: Context<CompleteSoSwapWrappedWithoutSwap>,
		vaa_hash: [u8; 32],
		skip_verify_soswap_message: bool,
	) -> Result<()> {
		instructions::complete_so_swap_wrapped_without_swap::handler(
			ctx,
			vaa_hash,
			skip_verify_soswap_message,
		)
	}

	pub fn estimate_relayer_fee(
		ctx: Context<EstimateRelayerFee>,
		so_data: Vec<u8>,
		wormhole_data: Vec<u8>,
		swap_data_dst: Vec<u8>,
	) -> Result<(u64, u64, u128)> {
		instructions::estimate_relayer_fee::handler(ctx, so_data, wormhole_data, swap_data_dst)
	}

	/// Precondition: request has been posted
	pub fn so_swap_native_with_whirlpool(ctx: Context<SoSwapNativeWithWhirlpool>) -> Result<()> {
		instructions::so_swap_native_with_whirlpool::handler(ctx)
	}

	/// Precondition: request has been posted
	pub fn so_swap_wrapped_with_whirlpool(ctx: Context<SoSwapWrappedWithWhirlpool>) -> Result<()> {
		instructions::so_swap_wrapped_with_whirlpool::handler(ctx)
	}

	pub fn complete_so_swap_native_with_whirlpool(
		ctx: Context<CompleteSoSwapNativeWithWhirlpool>,
		vaa_hash: [u8; 32],
	) -> Result<()> {
		instructions::complete_so_swap_native_with_whirlpool::handler(ctx, vaa_hash)
	}

	pub fn complete_so_swap_wrapped_with_whirlpool(
		ctx: Context<CompleteSoSwapWrappedWithWhirlpool>,
		vaa_hash: [u8; 32],
	) -> Result<()> {
		instructions::complete_so_swap_wrapped_with_whirlpool::handler(ctx, vaa_hash)
	}

	pub fn set_redeem_proxy(ctx: Context<SetRedeemProxy>, new_proxy: Pubkey) -> Result<()> {
		instructions::set_redeem_proxy::handler(ctx, new_proxy)
	}

	pub fn so_swap_post_cross_request(
		ctx: Context<PostRequest>,
		so_data: Vec<u8>,
		swap_data_src: Vec<u8>,
		wormhole_data: Vec<u8>,
		swap_data_dst: Vec<u8>,
	) -> Result<u64> {
		instructions::post_request::handler(
			ctx,
			so_data,
			swap_data_src,
			wormhole_data,
			swap_data_dst,
		)
	}

	/// Close the pending cross request.
	/// The remaining lamports will be refunded to the requester
	pub fn so_swap_close_pending_request(ctx: Context<CloseRequest>) -> Result<()> {
		instructions::close_pending_request::handler(ctx)
	}

	pub fn wrap_sol(ctx: Context<WrapSOL>, amount_to_be_wrapped: u64) -> Result<()> {
		instructions::wrap_sol::handler(ctx, amount_to_be_wrapped)
	}
}
