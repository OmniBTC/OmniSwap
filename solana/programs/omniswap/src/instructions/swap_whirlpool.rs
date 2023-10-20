use anchor_lang::{prelude::*, solana_program::account_info::AccountInfo};
use anchor_spl::token::TokenAccount;

use crate::{
	cross::{NormalizedSoData, NormalizedSwapData},
	dex::swap_whirlpool_cpi::{
		orca_whirlpool_swap_cpi, parse_whirlpool_call_data, OrcaWhirlpoolSwap,
	},
};

pub trait SoSwapWithWhirlpool<'info> {
	fn whirlpool_program(&self) -> AccountInfo<'info>;
	fn token_program(&self) -> AccountInfo<'info>;
	fn token_authority(&self) -> AccountInfo<'info>;
	fn whirlpool(&self) -> AccountInfo<'info>;
	fn token_owner_account_a(&self) -> Box<Account<'info, TokenAccount>>;
	fn token_vault_a(&self) -> AccountInfo<'info>;
	fn token_owner_account_b(&self) -> Box<Account<'info, TokenAccount>>;
	fn token_vault_b(&self) -> AccountInfo<'info>;
	fn tick_array_0(&self) -> AccountInfo<'info>;
	fn tick_array_1(&self) -> AccountInfo<'info>;
	fn tick_array_2(&self) -> AccountInfo<'info>;
	fn oracle(&self) -> AccountInfo<'info>;
	fn mint(&self) -> AccountInfo<'info>;
}

pub fn swap_by_whirlpool<'info, S: SoSwapWithWhirlpool<'info>>(
	ctx: &S,
	parsed_swap_data_src: &Vec<NormalizedSwapData>,
	parsed_so_data: &NormalizedSoData,
) -> Result<(bool, u64)> {
	assert_eq!(parsed_swap_data_src.len(), 1, "Unsupported more than one swap");
	let swap_data = parsed_swap_data_src.first().unwrap();

	// sending_asset -> receiving_asset
	assert!(swap_data.from_amount < u64::MAX.into(), "swap.amount >= u64.max");
	assert_eq!(swap_data.from_amount, parsed_so_data.amount, "swap.amount != so.amount");
	assert_eq!(
		swap_data.sending_asset_id, parsed_so_data.sending_asset_id,
		"swap.sending != so_sending"
	);
	assert_eq!(
		Pubkey::try_from(swap_data.call_to.clone()).unwrap(),
		crate::ID,
		"swap.call != crate::ID"
	);

	let (min_amount_out, sqrt_price_limit) = parse_whirlpool_call_data(&swap_data.call_data)?;

	let a_to_b = check_a_to_b::<S>(ctx)?;

	let token_value_a_before = S::token_owner_account_a(ctx).amount;
	let token_value_b_before = S::token_owner_account_b(ctx).amount;

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
		swap_data.from_amount.as_u64(),
		min_amount_out,
		sqrt_price_limit,
		true,
		a_to_b,
	)?;

	S::token_owner_account_a(ctx).reload()?;
	S::token_owner_account_b(ctx).reload()?;
	let token_value_a_after = S::token_owner_account_a(ctx).amount;
	let token_value_b_after = S::token_owner_account_b(ctx).amount;

	let amount_out_value = if a_to_b {
		token_value_b_after.checked_sub(token_value_b_before).unwrap()
	} else {
		token_value_a_after.checked_sub(token_value_a_before).unwrap()
	};

	Ok((a_to_b, amount_out_value))
}

fn check_a_to_b<'info, S: SoSwapWithWhirlpool<'info>>(ctx: &S) -> Result<bool> {
	if S::mint(ctx).key() == S::token_owner_account_a(ctx).mint {
		return Ok(false)
	};

	if S::mint(ctx).key() == S::token_owner_account_b(ctx).mint {
		return Ok(true)
	}

	panic!("mint is neither a nor b");
}
