use anchor_lang::{prelude::*, solana_program::account_info::AccountInfo};
use anchor_spl::token::TokenAccount;

use crate::{
	cross::NormalizedSwapData,
	dex::swap_whirlpool_cpi::{
		get_default_price_limit, orca_whirlpool_swap_cpi, parse_whirlpool_call_data,
		OrcaWhirlpoolSwap,
	},
};

pub trait SoSwapWithWhirlpool<'info> {
	fn whirlpool_program(&self) -> AccountInfo<'info>;
	fn token_program(&self) -> AccountInfo<'info>;
	fn token_authority(&self) -> AccountInfo<'info>;
	fn whirlpool(&self) -> AccountInfo<'info>;
	fn token_owner_account_a(&self) -> &Account<'info, TokenAccount>;
	fn token_vault_a(&self) -> AccountInfo<'info>;
	fn token_owner_account_b(&self) -> &Account<'info, TokenAccount>;
	fn token_vault_b(&self) -> AccountInfo<'info>;
	fn tick_array_0(&self) -> AccountInfo<'info>;
	fn tick_array_1(&self) -> AccountInfo<'info>;
	fn tick_array_2(&self) -> AccountInfo<'info>;
	fn oracle(&self) -> AccountInfo<'info>;
	fn mint(&self) -> AccountInfo<'info>;
	fn is_origin(&self) -> bool {
		true
	}
}

pub fn swap_by_whirlpool<'info, S: SoSwapWithWhirlpool<'info>>(
	ctx: &S,
	parsed_swap_data: &NormalizedSwapData,
) -> Result<bool> {
	// sending_asset -> receiving_asset
	assert!(parsed_swap_data.from_amount < u64::MAX.into(), "swap.amount >= u64.max");
	assert_eq!(
		Pubkey::try_from(parsed_swap_data.call_to.clone()).unwrap(),
		S::whirlpool(ctx).key.clone(),
		"swap.call != whirlpool_pda"
	);

	let min_amount_out = parse_whirlpool_call_data(&parsed_swap_data.call_data)?;

	let a_to_b = check_a_to_b::<S>(ctx)?;

	orca_whirlpool_swap_cpi(
		CpiContext::new(
			S::whirlpool_program(ctx),
			OrcaWhirlpoolSwap {
				token_program: S::token_program(ctx),
				token_authority: S::token_authority(ctx),
				whirlpool: S::whirlpool(ctx),
				token_owner_account_a: S::token_owner_account_a(ctx).to_account_info(),
				token_vault_a: S::token_vault_a(ctx),
				token_owner_account_b: S::token_owner_account_b(ctx).to_account_info(),
				token_vault_b: S::token_vault_b(ctx),
				tick_array_0: S::tick_array_0(ctx),
				tick_array_1: S::tick_array_1(ctx),
				tick_array_2: S::tick_array_2(ctx),
				oracle: S::oracle(ctx),
			},
		),
		parsed_swap_data.from_amount.as_u64(),
		min_amount_out,
		get_default_price_limit(a_to_b),
		true,
		a_to_b,
	)?;

	msg!("a_to_b: {:?}", a_to_b);

	Ok(a_to_b)
}

pub fn check_a_to_b<'info, S: SoSwapWithWhirlpool<'info>>(ctx: &S) -> Result<bool> {
	if S::mint(ctx).key() == S::token_owner_account_a(ctx).mint {
		if S::is_origin(ctx) {
			return Ok(false)
		} else {
			return Ok(true)
		}
	};

	if S::mint(ctx).key() == S::token_owner_account_b(ctx).mint {
		if S::is_origin(ctx) {
			return Ok(true)
		} else {
			return Ok(false)
		}
	}

	panic!("mint is neither a nor b");
}
