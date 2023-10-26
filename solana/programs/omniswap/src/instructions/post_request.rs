use anchor_lang::prelude::*;

use crate::{
	cross::{NormalizedSoData, NormalizedSwapData, NormalizedWormholeData},
	cross_request::CrossRequest,
	state::SenderConfig,
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
        seeds = [SenderConfig::SEED_PREFIX],
        bump,
    )]
	/// Sender Config account
	pub config: Box<Account<'info, SenderConfig>>,

	#[account(
        init,
        payer = payer,
        seeds = [
            CrossRequest::SEED_PREFIX,
            &config.nonce.to_le_bytes()[..]
        ],
        bump,
        space = 8 + 32 + 32 + so_data.len() + swap_data_src.len() + wormhole_data.len() + swap_data_dst.len(),
    )]
	pub request: Box<Account<'info, CrossRequest>>,

	/// System program.
	pub system_program: Program<'info, System>,
}

pub fn handler(
	ctx: Context<PostRequest>,
	so_data: Vec<u8>,
	swap_data_src: Vec<u8>,
	wormhole_data: Vec<u8>,
	swap_data_dst: Vec<u8>,
) -> Result<()> {
	let _parsed_wormhole_data =
		NormalizedWormholeData::decode_normalized_wormhole_data(&wormhole_data)?;
	let _parsed_so_data = NormalizedSoData::decode_normalized_so_data(&so_data)?;
	let _parsed_swap_data_src = NormalizedSwapData::decode_normalized_swap_data(&swap_data_src)?;
	let _parsed_swap_data_dst = NormalizedSwapData::decode_normalized_swap_data(&swap_data_dst)?;

	let request = &mut ctx.accounts.request;

	request.payer = ctx.accounts.payer.key();
	request.owner = ctx.accounts.config.key();
	request.nonce = ctx.accounts.config.nonce;
	request.so_data = so_data;
	request.swap_data_src = swap_data_src;
	request.wormhole_data = wormhole_data;
	request.swap_data_dst = swap_data_dst;

	// increase config nonce
	ctx.accounts.config.nonce += 1;

	Ok(())
}
