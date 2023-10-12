use anchor_lang::prelude::*;
use wormhole_anchor_sdk::{token_bridge, wormhole};

use crate::{
	constants::SEED_PREFIX_BRIDGED,
	context::SoSwapNativeWithoutSwap,
	cross::{NormalizedSoData, NormalizedWormholeData},
	error::SoSwapError,
	message::SoSwapMessage,
	state::sender_config::SenderConfig,
};

pub fn handler(
	ctx: Context<SoSwapNativeWithoutSwap>,
	amount: u64,
	wormhole_data: Vec<u8>,
	so_data: Vec<u8>,
) -> Result<()> {
	// Token Bridge program truncates amounts to 8 decimals, so there will
	// be a residual amount if decimals of SPL is >8. We need to take into
	// account how much will actually be bridged.
	let truncated_amount = token_bridge::truncate_amount(amount, ctx.accounts.mint.decimals);
	require!(truncated_amount > 0, SoSwapError::ZeroBridgeAmount);
	if truncated_amount != amount {
		msg!("SendNativeTokensWithPayload :: truncating amount {} to {}", amount, truncated_amount);
	}

	let normalized_wormhole_data =
		NormalizedWormholeData::decode_normalized_wormhole_data(&wormhole_data)?;
	let normalized_so_data = NormalizedSoData::decode_normalized_so_data(&so_data)?;

	let recipient_chain = normalized_wormhole_data.dst_wormhole_chain_id;
	require!(
		recipient_chain > 0 &&
			recipient_chain != wormhole::CHAIN_ID_SOLANA &&
			!normalized_wormhole_data.dst_so_diamond.iter().all(|&x| x == 0) &&
			normalized_wormhole_data.dst_so_diamond ==
				ctx.accounts.foreign_contract.address.to_vec(),
		SoSwapError::InvalidRecipient,
	);

	// These seeds are used to:
	// 1.  Sign the Sender Config's token account to delegate approval
	//     of truncated_amount.
	// 2.  Sign Token Bridge program's transfer_native instruction.
	// 3.  Close tmp_token_account.
	let config_seeds = &[SenderConfig::SEED_PREFIX.as_ref(), &[ctx.accounts.config.bump]];

	// First transfer tokens from payer to tmp_token_account.
	anchor_spl::token::transfer(
		CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Transfer {
				from: ctx.accounts.from_token_account.to_account_info(),
				to: ctx.accounts.tmp_token_account.to_account_info(),
				authority: ctx.accounts.payer.to_account_info(),
			},
		),
		truncated_amount,
	)?;

	// Delegate spending to Token Bridge program's authority signer.
	anchor_spl::token::approve(
		CpiContext::new_with_signer(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Approve {
				to: ctx.accounts.tmp_token_account.to_account_info(),
				delegate: ctx.accounts.token_bridge_authority_signer.to_account_info(),
				authority: ctx.accounts.config.to_account_info(),
			},
			&[&config_seeds[..]],
		),
		truncated_amount,
	)?;

	// Serialize SoSwapMessage as encoded payload for Token Bridge
	// transfer.
	let payload = SoSwapMessage {
		dst_max_gas_price: normalized_wormhole_data.dst_max_gas_price_in_wei_for_relayer,
		// TODO: dst_max_gas
		dst_max_gas: Default::default(),
		normalized_so_data,
		normalized_swap_data: Default::default(),
	}
	.try_to_vec()?;

	// Bridge native token with encoded payload.
	token_bridge::transfer_native_with_payload(
		CpiContext::new_with_signer(
			ctx.accounts.token_bridge_program.to_account_info(),
			token_bridge::TransferNativeWithPayload {
				payer: ctx.accounts.payer.to_account_info(),
				config: ctx.accounts.token_bridge_config.to_account_info(),
				from: ctx.accounts.tmp_token_account.to_account_info(),
				mint: ctx.accounts.mint.to_account_info(),
				custody: ctx.accounts.token_bridge_custody.to_account_info(),
				authority_signer: ctx.accounts.token_bridge_authority_signer.to_account_info(),
				custody_signer: ctx.accounts.token_bridge_custody_signer.to_account_info(),
				wormhole_bridge: ctx.accounts.wormhole_bridge.to_account_info(),
				wormhole_message: ctx.accounts.wormhole_message.to_account_info(),
				wormhole_emitter: ctx.accounts.token_bridge_emitter.to_account_info(),
				wormhole_sequence: ctx.accounts.token_bridge_sequence.to_account_info(),
				wormhole_fee_collector: ctx.accounts.wormhole_fee_collector.to_account_info(),
				clock: ctx.accounts.clock.to_account_info(),
				sender: ctx.accounts.config.to_account_info(),
				rent: ctx.accounts.rent.to_account_info(),
				system_program: ctx.accounts.system_program.to_account_info(),
				token_program: ctx.accounts.token_program.to_account_info(),
				wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
			},
			&[
				&config_seeds[..],
				&[
					SEED_PREFIX_BRIDGED,
					&ctx.accounts.token_bridge_sequence.next_value().to_le_bytes()[..],
					&[*ctx.bumps.get("wormhole_message").ok_or(SoSwapError::BumpNotFound)?],
				],
			],
		),
		0,
		truncated_amount,
		ctx.accounts.foreign_contract.address,
		recipient_chain,
		payload,
		&ctx.program_id.key(),
	)?;

	// Finish instruction by closing tmp_token_account.
	anchor_spl::token::close_account(CpiContext::new_with_signer(
		ctx.accounts.token_program.to_account_info(),
		anchor_spl::token::CloseAccount {
			account: ctx.accounts.tmp_token_account.to_account_info(),
			destination: ctx.accounts.payer.to_account_info(),
			authority: ctx.accounts.config.to_account_info(),
		},
		&[&config_seeds[..]],
	))
}
