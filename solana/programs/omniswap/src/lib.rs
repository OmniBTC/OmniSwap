extern crate core;

use anchor_lang::prelude::*;

pub use context::*;
pub use error::*;
pub use state::*;

pub mod context;
pub mod cross;
pub mod error;
pub mod instructions;
pub mod message;
pub mod serde;
pub mod state;

declare_id!("9YYGvVLZJ9XmKM2A1RNv1Dx3oUnHWgtXWt8V3HU5MtXU");

#[program]
pub mod omniswap {
	use super::*;

	/// This instruction can be used to generate your program's config.
	/// And for convenience, we will store Wormhole-related PDAs in the
	/// config so we can verify these accounts with a simple == constraint.
	pub fn initialize(
		ctx: Context<Initialize>,
		actual_reserve: u64,
		estimate_reserve: u64,
	) -> Result<()> {
		instructions::initialize::handler(ctx, actual_reserve, estimate_reserve)
	}

	/// Set relayer fee scale factor
	pub fn set_wormhole_reserve(
		ctx: Context<SetWormholeReserve>,
		actual_reserve: u64,
		estimate_reserve: u64,
	) -> Result<()> {
		instructions::set_wormhole_reserve::handler(ctx, actual_reserve, estimate_reserve)
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

	pub fn so_swap_native_without_swap(
		ctx: Context<SoSwapNativeWithoutSwap>,
		amount: u64,
		wormhole_data: Vec<u8>,
		so_data: Vec<u8>,
	) -> Result<()> {
		instructions::so_swap_native_without_swap::handler(ctx, amount, wormhole_data, so_data)
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

	pub fn so_swap_wrapped_without_swap(
		ctx: Context<SoSwapWrappedWithoutSwap>,
		amount: u64,
		wormhole_data: Vec<u8>,
		so_data: Vec<u8>,
	) -> Result<()> {
		instructions::so_swap_wrapped_without_swap::handler(ctx, amount, wormhole_data, so_data)
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
}
