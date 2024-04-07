use anchor_lang::{prelude::*, system_program::Transfer};
use anchor_spl::token::{Mint, SyncNative, Token, TokenAccount};

use crate::WrapSOLKey;

#[derive(Accounts)]
pub struct WrapSOL<'info> {
	#[account(mut)]
	pub payer: Signer<'info>,

	#[account(
        mut,
        associated_token::mint = wsol_mint,
        associated_token::authority = payer,
    )]
	pub wrap_sol_account: Box<Account<'info, TokenAccount>>,

	#[account(
        constraint = wsol_mint.key() == WrapSOLKey
    )]
	pub wsol_mint: Account<'info, Mint>,

	/// Token program.
	pub token_program: Program<'info, Token>,

	/// System program.
	pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<WrapSOL>, amount_to_be_wrapped: u64) -> Result<()> {
	// 1. transfer sol to wrap_sol_account
	anchor_lang::system_program::transfer(
		CpiContext::new(
			ctx.accounts.system_program.to_account_info(),
			Transfer {
				from: ctx.accounts.payer.to_account_info(),
				to: ctx.accounts.wrap_sol_account.to_account_info(),
			},
		),
		amount_to_be_wrapped,
	)?;

	// 2. sync native
	anchor_spl::token::sync_native(CpiContext::new(
		ctx.accounts.token_program.to_account_info(),
		SyncNative { account: ctx.accounts.wrap_sol_account.to_account_info() },
	))
}
