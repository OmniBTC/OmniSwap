use anchor_lang::prelude::*;
use spl_math::uint::U256;
use wormhole_anchor_sdk::wormhole;

use crate::{
	cross::{NormalizedSoData, NormalizedSwapData, NormalizedWormholeData},
	cross_request::CrossRequest,
	instructions::relayer_fee::EstRelayerFee,
	state::SenderConfig,
	ForeignContract, PriceManager, SoFeeConfig,
};

#[derive(Accounts)]
#[instruction(
    so_data: Vec<u8>,
    swap_data_src: Vec<u8>,
    wormhole_data: Vec<u8>,
    swap_data_dst: Vec<u8>
)]
pub struct PostRequest<'info> {
	#[account(mut)]
	/// The requester
	pub payer: Signer<'info>,

	#[account(
        mut,
        seeds = [
            SenderConfig::SEED_PREFIX
        ],
        bump,
    )]
	/// Sender Config account
	pub config: Box<Account<'info, SenderConfig>>,

	#[account(
        init_if_needed,
        payer = payer,
        seeds = [
            CrossRequest::SEED_PREFIX,
            payer.key().as_ref()
        ],
        bump,
        space = CrossRequest::MAXIMUM_SIZE,
    )]
	pub request: Box<Account<'info, CrossRequest>>,

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

	/// System program.
	pub system_program: Program<'info, System>,
}

impl<'info> EstRelayerFee<'info> for Context<'_, '_, '_, '_, PostRequest<'info>> {
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
	ctx: Context<PostRequest>,
	so_data: Vec<u8>,
	swap_data_src: Vec<u8>,
	wormhole_data: Vec<u8>,
	swap_data_dst: Vec<u8>,
) -> Result<u64> {
	let mut parsed_wormhole_data =
		NormalizedWormholeData::decode_compact_wormhole_data(&wormhole_data)?;
	let parsed_so_data = NormalizedSoData::decode_compact_so_data(&so_data)?;

	let parsed_swap_data_src = NormalizedSwapData::decode_compact_swap_data_src(&swap_data_src)?;

	let parsed_swap_data_dst = NormalizedSwapData::decode_normalized_swap_data(&swap_data_dst)?;

	let (relayer_fee, wormhole_fee, _) = EstRelayerFee::estimate_fee(
		&ctx,
		&parsed_so_data,
		&parsed_wormhole_data,
		&parsed_swap_data_dst,
	)?;

	let total_fee = relayer_fee.checked_add(wormhole_fee).unwrap();

	// Update total fee
	parsed_wormhole_data.wormhole_fee = U256::from(total_fee);
	let fix_wormhole_data =
		NormalizedWormholeData::encode_normalized_wormhole_data(&parsed_wormhole_data);

	let request = &mut ctx.accounts.request;

	request.payer = ctx.accounts.payer.key();
	request.owner = ctx.accounts.config.key();
	request.so_data = NormalizedSoData::encode_normalized_so_data(&parsed_so_data);
	request.swap_data_src = NormalizedSwapData::encode_normalized_swap_data(&parsed_swap_data_src);
	request.wormhole_data = fix_wormhole_data;
	request.swap_data_dst = swap_data_dst;

	Ok(total_fee)
}
