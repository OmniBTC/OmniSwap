use anchor_lang::{
	prelude::*,
	solana_program::{hash::Hasher, instruction::Instruction, program::invoke_signed},
};

use crate::{
	constants::DELIMITER,
	error::SoSwapError,
	serde::{deserialize_u128, deserialize_u64},
};

#[derive(Accounts)]
pub struct OrcaWhirlpoolSwap<'info> {
	/// CHECK:
	pub token_program: AccountInfo<'info>,

	/// CHECK:
	#[account(signer)]
	pub token_authority: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub whirlpool: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub token_owner_account_a: AccountInfo<'info>,
	/// CHECK:
	#[account(mut)]
	pub token_vault_a: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub token_owner_account_b: AccountInfo<'info>,
	/// CHECK:
	#[account(mut)]
	pub token_vault_b: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub tick_array_0: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub tick_array_1: AccountInfo<'info>,

	/// CHECK:
	#[account(mut)]
	pub tick_array_2: AccountInfo<'info>,

	/// CHECK:
	#[account(seeds = [b"oracle", whirlpool.key().as_ref()],bump)]
	/// Oracle is currently unused and will be enabled on subsequent updates
	pub oracle: AccountInfo<'info>,
}

/// Format: "swap_name,min_amount_out_u64,sqrt_price_limit_u128"
/// example: "Whirlpool,1235678,1234567890"
pub fn parse_whirlpool_call_data(data: &[u8]) -> std::result::Result<(u64, u128), SoSwapError> {
	let mut parts: Vec<&[u8]> = Vec::new();
	let mut start = 0;

	for (i, &byte) in data.iter().enumerate() {
		if byte == DELIMITER {
			parts.push(&data[start..i]);
			start = i + 1;
		}
	}
	parts.push(&data[start..]);

	if parts.len() != 3 {
		return Err(SoSwapError::InvalidCallData)
	};

	// Check swap name
	if parts[0].to_vec() != super::ORCA_WHIRLPOOL_SWAP.to_vec() {
		return Err(SoSwapError::InvalidCallData)
	}

	// Check min_amout_out_u64
	let min_amount_out = deserialize_u64(parts[1]).map_err(|_| SoSwapError::InvalidCallData)?;

	// Check sqrt_price_limit_u128
	let sqrt_price_limit = deserialize_u128(parts[2]).map_err(|_| SoSwapError::InvalidCallData)?;

	Ok((min_amount_out, sqrt_price_limit))
}

pub fn orca_whirlpool_swap_cpi<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, OrcaWhirlpoolSwap<'info>>,
	amount: u64,
	other_amount_threshold: u64,
	sqrt_price_limit: u128,
	amount_specified_is_input: bool,
	a_to_b: bool,
) -> Result<()> {
	let accounts = &[
		ctx.accounts.token_program.to_account_info(),
		ctx.accounts.token_authority.to_account_info(),
		ctx.accounts.whirlpool.to_account_info(),
		ctx.accounts.token_owner_account_a.to_account_info(),
		ctx.accounts.token_vault_a.to_account_info(),
		ctx.accounts.token_owner_account_b.to_account_info(),
		ctx.accounts.token_vault_b.to_account_info(),
		ctx.accounts.tick_array_0.to_account_info(),
		ctx.accounts.tick_array_1.to_account_info(),
		ctx.accounts.tick_array_2.to_account_info(),
		ctx.accounts.oracle.to_account_info(),
	];

	let mut hasher = Hasher::default();
	hasher.hash(b"global:swap");

	let mut data = hasher.result().as_ref()[..8].to_vec();
	data.extend(amount.to_le_bytes());
	data.extend(other_amount_threshold.to_le_bytes());
	data.extend(sqrt_price_limit.to_le_bytes());
	data.extend([
		if amount_specified_is_input { 1_u8 } else { 0_u8 },
		if a_to_b { 1_u8 } else { 0_u8 },
	]);

	let whirlpool_accounts = vec![
		AccountMeta::new_readonly(ctx.accounts.token_program.key(), false),
		AccountMeta::new_readonly(ctx.accounts.token_authority.key(), true),
		AccountMeta::new(ctx.accounts.whirlpool.key(), false),
		AccountMeta::new(ctx.accounts.token_owner_account_a.key(), false),
		AccountMeta::new(ctx.accounts.token_vault_a.key(), false),
		AccountMeta::new(ctx.accounts.token_owner_account_b.key(), false),
		AccountMeta::new(ctx.accounts.token_vault_b.key(), false),
		AccountMeta::new(ctx.accounts.tick_array_0.key(), false),
		AccountMeta::new(ctx.accounts.tick_array_1.key(), false),
		AccountMeta::new(ctx.accounts.tick_array_2.key(), false),
		AccountMeta::new_readonly(ctx.accounts.oracle.key(), false),
	];

	let instruction =
		Instruction { program_id: ctx.program.key(), accounts: whirlpool_accounts, data };

	invoke_signed(&instruction, accounts, ctx.signer_seeds).map_err(Into::into)
}
