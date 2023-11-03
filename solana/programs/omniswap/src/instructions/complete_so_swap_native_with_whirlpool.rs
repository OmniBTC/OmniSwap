use anchor_lang::{prelude::*, system_program::Transfer};
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Mint, Token, TokenAccount},
};
use spl_math::uint::U256;
use wormhole_anchor_sdk::{token_bridge, wormhole};

use super::swap_whirlpool::{check_a_to_b, swap_by_whirlpool, SoSwapWithWhirlpool};
use crate::{
	constants::{RAY, SEED_PREFIX_TMP, SEED_UNWRAP},
	error::SoSwapError,
	message::PostedSoSwapMessage,
	state::{ForeignContract, RedeemerConfig, SoFeeConfig},
	utils::bytes_to_hex,
	UnwrapSOLKey, WrapSOLKey,
};

#[derive(Accounts)]
#[instruction(vaa_hash: [u8; 32])]
pub struct CompleteSoSwapNativeWithWhirlpool<'info> {
	#[account(mut)]
	/// Payer will pay Wormhole fee to transfer tokens and create temporary
	/// token account.
	pub payer: Signer<'info>,

	// 1. soswap configs
	#[account(
		seeds = [RedeemerConfig::SEED_PREFIX],
		bump
	)]
	/// Redeemer Config account. Acts as the Token Bridge redeemer, which signs
	/// for the complete transfer instruction. Read-only.
	pub config: Box<Account<'info, RedeemerConfig>>,

	#[account(
		seeds = [SoFeeConfig::SEED_PREFIX],
		bump,
	)]
	/// SoFee Config account. Read-only.
	pub fee_config: Box<Account<'info, SoFeeConfig>>,

	#[account(
		mut,
		associated_token::mint = mint,
		associated_token::authority = fee_config.beneficiary
	)]
	/// CHECK: collect relayer fee
	pub beneficiary_token_account: Box<Account<'info, TokenAccount>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&vaa.emitter_chain().to_le_bytes()[..]
		],
		bump,
		constraint = foreign_contract.verify(&vaa) @ SoSwapError::InvalidForeignContract
	)]
	/// Foreign Contract account. The registered contract specified in this
	/// account must agree with the target address for the Token Bridge's token
	/// transfer. Read-only.
	pub foreign_contract: Box<Account<'info, ForeignContract>>,

	// 2. whirlpool configs
	/// CHECK: Whirlpool Program
	pub whirlpool_program: AccountInfo<'info>,

	/// CHECK: Whirlpool Account
	#[account(mut)]
	pub whirlpool_account: AccountInfo<'info>,
	/// CHECK: token_owner_account_a,
	/// Payer's associated token account.
	#[account(
		mut,
		constraint = whirlpool_token_owner_account_a.owner == config.proxy
	)]
	pub whirlpool_token_owner_account_a: Box<Account<'info, TokenAccount>>,
	/// CHECK: token_vault_a
	#[account(mut)]
	pub whirlpool_token_vault_a: AccountInfo<'info>,
	/// CHECK: token_owner_account_b
	/// Payer's associated token account.
	#[account(
		mut,
		constraint = whirlpool_token_owner_account_b.owner == config.proxy
	)]
	pub whirlpool_token_owner_account_b: Box<Account<'info, TokenAccount>>,
	/// CHECK: token_vault_b
	#[account(mut)]
	pub whirlpool_token_vault_b: AccountInfo<'info>,
	/// CHECK:
	#[account(mut)]
	pub whirlpool_tick_array_0: AccountInfo<'info>,
	/// CHECK:
	#[account(mut)]
	pub whirlpool_tick_array_1: AccountInfo<'info>,
	/// CHECK:
	#[account(mut)]
	pub whirlpool_tick_array_2: AccountInfo<'info>,
	/// CHECK:
	#[account(
		seeds = [
			b"oracle",
			whirlpool_account.key().as_ref()
		],
		bump,
		seeds::program = whirlpool_program
	)]
	/// Oracle is currently unused and will be enabled on subsequent updates
	pub whirlpool_oracle: AccountInfo<'info>,

	#[account(
		init,
		payer = payer,
		seeds = [SEED_UNWRAP],
		bump,
		token::mint = wsol_mint,
		token::authority = payer
	)]
	pub unwrap_sol_account: Option<Box<Account<'info, TokenAccount>>>,

	#[account(
		constraint = wsol_mint.key() == WrapSOLKey
	)]
	pub wsol_mint: Option<Box<Account<'info, Mint>>>,

	#[account(
		mut,
		address = recipient_token_account.owner @ SoSwapError::InvalidRecipient
	)]
	/// CHECK: the recipient account
	pub recipient: Option<UncheckedAccount<'info>>,

	// 3. wormhole configs
	#[account(
		address = vaa.data().mint()
	)]
	/// Mint info. This is the SPL token that will be bridged over from the
	/// foreign contract. This must match the token address specified in the
	/// signed Wormhole message. Read-only.
	pub mint: Box<Account<'info, Mint>>,

	#[account(mut)]
	/// Recipient associated token account.
	/// If swap ok, transfer the receiving token to this account
	pub recipient_token_account: Box<Account<'info, TokenAccount>>,

	#[account(
		mut,
		constraint = recipient_bridge_token_account.mint == mint.key(),
	)]
	/// Recipient associated token account.
	/// If swap failed, transfer the bridge token to this account
	pub recipient_bridge_token_account: Box<Account<'info, TokenAccount>>,

	#[account(
		init,
		payer = payer,
		seeds = [
			SEED_PREFIX_TMP,
			mint.key().as_ref(),
		],
		bump,
		token::mint = mint,
		token::authority = config
	)]
	/// Program's temporary token account. This account is created before the
	/// instruction is invoked to temporarily take custody of the payer's
	/// tokens. When the tokens are finally bridged in, the tokens will be
	/// transferred to the destination token accounts. This account will have
	/// zero balance and can be closed.
	pub tmp_token_account: Box<Account<'info, TokenAccount>>,

	/// Wormhole program.
	pub wormhole_program: Program<'info, wormhole::program::Wormhole>,

	/// Token Bridge program.
	pub token_bridge_program: Program<'info, token_bridge::program::TokenBridge>,

	#[account(
		address = config.token_bridge.config @ SoSwapError::InvalidTokenBridgeConfig
	)]
	/// Token Bridge config. Read-only.
	pub token_bridge_config: Box<Account<'info, token_bridge::Config>>,

	#[account(
		seeds = [
			wormhole::SEED_PREFIX_POSTED_VAA,
			&vaa_hash
		],
		bump,
		seeds::program = wormhole_program,
		constraint = vaa.data().to() == crate::ID || vaa.data().to() == config.key() @ SoSwapError::InvalidTransferToAddress,
		constraint = vaa.data().to_chain() == wormhole::CHAIN_ID_SOLANA @ SoSwapError::InvalidTransferToChain,
		constraint = vaa.data().token_chain() == wormhole::CHAIN_ID_SOLANA @ SoSwapError::InvalidTransferTokenChain
	)]
	/// Verified Wormhole message account. The Wormhole program verified
	/// signatures and posted the account data here. Read-only.
	pub vaa: Box<Account<'info, PostedSoSwapMessage>>,

	#[account(mut)]
	/// CHECK: Token Bridge claim account. It stores a boolean, whose value
	/// is true if the bridged assets have been claimed. If the transfer has
	/// not been redeemed, this account will not exist yet.
	pub token_bridge_claim: UncheckedAccount<'info>,

	#[account(
		address = foreign_contract.token_bridge_foreign_endpoint @ SoSwapError::InvalidTokenBridgeForeignEndpoint
	)]
	/// Token Bridge foreign endpoint. This account should really be one
	/// endpoint per chain, but the PDA allows for multiple endpoints for each
	/// chain! We store the proper endpoint for the emitter chain.
	pub token_bridge_foreign_endpoint: Box<Account<'info, token_bridge::EndpointRegistration>>,

	#[account(
		mut,
		seeds = [mint.key().as_ref()],
		bump,
		seeds::program = token_bridge_program
	)]
	/// CHECK: Token Bridge custody. This is the Token Bridge program's token
	/// account that holds this mint's balance.
	pub token_bridge_custody: Box<Account<'info, TokenAccount>>,

	#[account(
		address = config.token_bridge.custody_signer @ SoSwapError::InvalidTokenBridgeCustodySigner
	)]
	/// CHECK: Token Bridge custody signer. Read-only.
	pub token_bridge_custody_signer: UncheckedAccount<'info>,

	// 4. system configs
	/// System program.
	pub system_program: Program<'info, System>,

	/// Token program.
	pub token_program: Program<'info, Token>,

	/// Associated Token program.
	pub associated_token_program: Program<'info, AssociatedToken>,

	/// Rent sysvar.
	pub rent: Sysvar<'info, Rent>,
}

impl<'info> SoSwapWithWhirlpool<'info>
	for Context<'_, '_, '_, '_, CompleteSoSwapNativeWithWhirlpool<'info>>
{
	fn whirlpool_program(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_program.to_account_info()
	}

	fn token_program(&self) -> AccountInfo<'info> {
		self.accounts.token_program.to_account_info()
	}

	fn token_authority(&self) -> AccountInfo<'info> {
		self.accounts.payer.to_account_info()
	}

	fn whirlpool(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_account.to_account_info()
	}

	fn token_owner_account_a(&self) -> &Account<'info, TokenAccount> {
		self.accounts.whirlpool_token_owner_account_a.as_ref()
	}

	fn token_vault_a(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_token_vault_a.to_account_info()
	}

	fn token_owner_account_b(&self) -> &Account<'info, TokenAccount> {
		self.accounts.whirlpool_token_owner_account_b.as_ref()
	}

	fn token_vault_b(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_token_vault_b.to_account_info()
	}

	fn tick_array_0(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_tick_array_0.to_account_info()
	}

	fn tick_array_1(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_tick_array_1.to_account_info()
	}

	fn tick_array_2(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_tick_array_2.to_account_info()
	}

	fn oracle(&self) -> AccountInfo<'info> {
		self.accounts.whirlpool_oracle.to_account_info()
	}

	fn mint(&self) -> AccountInfo<'info> {
		self.accounts.mint.to_account_info()
	}

	fn is_origin(&self) -> bool {
		false
	}
}

pub fn handler(ctx: Context<CompleteSoSwapNativeWithWhirlpool>, _vaa_hash: [u8; 32]) -> Result<()> {
	// The Token Bridge program's claim account is only initialized when
	// a transfer is redeemed (and the boolean value `true` is written as
	// its data).
	//
	// The Token Bridge program will automatically fail if this transfer
	// is redeemed again. But we choose to short-circuit the failure as the
	// first evaluation of this instruction.
	require!(ctx.accounts.token_bridge_claim.data_is_empty(), SoSwapError::AlreadyRedeemed);
	require!(
		ctx.accounts.payer.key().as_ref() == ctx.accounts.config.proxy.as_ref(),
		SoSwapError::InvalidProxy
	);

	// The intended recipient must agree with the recipient.
	let so_msg = ctx.accounts.vaa.message().data();
	require!(*so_msg != Default::default(), SoSwapError::DeserializeSoSwapMessageFail);
	require!(
		ctx.accounts.recipient_token_account.owner.as_ref() == so_msg.normalized_so_data.receiver,
		SoSwapError::InvalidRecipient
	);
	require!(
		ctx.accounts.recipient_bridge_token_account.owner.as_ref() ==
			so_msg.normalized_so_data.receiver,
		SoSwapError::InvalidRecipient
	);

	// 1. redeem bridge token: tmp_account => proxy_a_or_b
	let (bridge_amount, tx_id) = complete_redeem(&ctx)?;

	// 2. swap bridge token to receiving token: proxy_a <=> proxy_b
	assert_eq!(so_msg.normalized_swap_data.len(), 1, "must be one swap");
	let mut swap_data = so_msg.normalized_swap_data.first().unwrap().clone();
	swap_data.reset_from_amount(U256::from(bridge_amount));

	let need_unwrap_sol = so_msg.normalized_so_data.receiving_asset_id == UnwrapSOLKey.as_ref();

	let (from_token_account, to_token_account, status, final_amount) = if let Ok(a_to_b) =
		swap_by_whirlpool(&ctx, &swap_data)
	{
		// 3. swap ok, send receiving token: proxy_a_or_b => recipient
		let (other_proxy_recipient_account, amount) = if a_to_b {
			let token_value_b_before = ctx.accounts.whirlpool_token_owner_account_b.amount;
			ctx.accounts.whirlpool_token_owner_account_b.reload()?;
			let token_value_b_after = ctx.accounts.whirlpool_token_owner_account_b.amount;

			let amount = token_value_b_after.checked_sub(token_value_b_before).unwrap();
			let account = ctx.accounts.whirlpool_token_owner_account_b.as_ref();

			(account, amount)
		} else {
			let token_value_a_before = ctx.accounts.whirlpool_token_owner_account_a.amount;
			ctx.accounts.whirlpool_token_owner_account_a.reload()?;
			let token_value_a_after = ctx.accounts.whirlpool_token_owner_account_a.amount;

			let amount = token_value_a_after.checked_sub(token_value_a_before).unwrap();
			let account = ctx.accounts.whirlpool_token_owner_account_a.as_ref();

			(account, amount)
		};

		(other_proxy_recipient_account, &ctx.accounts.recipient_token_account, 0, amount)
	} else {
		// 4. swap fail, send bridge token: proxy_a_or_b => recipient
		let proxy_recipient_account = if check_a_to_b(&ctx)? {
			ctx.accounts.whirlpool_token_owner_account_a.as_ref()
		} else {
			ctx.accounts.whirlpool_token_owner_account_b.as_ref()
		};

		(proxy_recipient_account, &ctx.accounts.recipient_bridge_token_account, 1, bridge_amount)
	};

	if need_unwrap_sol &&
		from_token_account.mint == WrapSOLKey &&
		ctx.accounts.unwrap_sol_account.is_some() &&
		ctx.accounts.recipient.is_some()
	{
		let unwrap_sol_account = &ctx.accounts.unwrap_sol_account.clone().unwrap();
		let recipient = &ctx.accounts.recipient.clone().unwrap();

		require!(
			recipient.key().as_ref() == so_msg.normalized_so_data.receiver,
			SoSwapError::InvalidRecipient
		);

		// 1. transfer: from_token_account(wsol) => unwrap_sol_account(wsol)
		anchor_spl::token::transfer(
			CpiContext::new(
				ctx.accounts.token_program.to_account_info(),
				anchor_spl::token::Transfer {
					from: from_token_account.to_account_info(),
					to: unwrap_sol_account.to_account_info(),
					authority: ctx.accounts.payer.to_account_info(),
				},
			),
			final_amount,
		)?;

		// 2. close unwrap_sol_account: unwrap_sol_account(wsol) -> proxy(sol)
		anchor_spl::token::close_account(CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::CloseAccount {
				account: unwrap_sol_account.to_account_info(),
				destination: ctx.accounts.payer.to_account_info(),
				authority: ctx.accounts.payer.to_account_info(),
			},
		))?;

		// 3. transfer: proxy(sol) -> recipient(sol)
		anchor_lang::system_program::transfer(
			CpiContext::new(
				ctx.accounts.system_program.to_account_info(),
				Transfer {
					from: ctx.accounts.payer.to_account_info(),
					to: recipient.to_account_info(),
				},
			),
			final_amount,
		)?;

		msg!(
			"[SoTransferCompleted]: status={}, amount={}, r_token={}, txid={}",
			0,
			final_amount,
			UnwrapSOLKey.to_string(),
			tx_id,
		);

		return Ok(())
	};

	msg!(
		"[SoTransferCompleted]: status={}, amount={}, r_token={}, txid={}",
		status,
		final_amount,
		to_token_account.mint.to_string(),
		tx_id,
	);

	anchor_spl::token::transfer(
		CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Transfer {
				from: from_token_account.to_account_info(),
				to: to_token_account.to_account_info(),
				authority: ctx.accounts.payer.to_account_info(),
			},
		),
		final_amount,
	)?;

	if let Some(unwrap_sol_account) = &ctx.accounts.unwrap_sol_account {
		anchor_spl::token::close_account(CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::CloseAccount {
				account: unwrap_sol_account.to_account_info(),
				destination: ctx.accounts.payer.to_account_info(),
				authority: ctx.accounts.payer.to_account_info(),
			},
		))?;
	}

	Ok(())
}

fn complete_redeem(ctx: &Context<CompleteSoSwapNativeWithWhirlpool>) -> Result<(u64, String)> {
	// These seeds are used to:
	// 1.  Redeem Token Bridge program's complete_transfer_native_with_payload.
	// 2.  Transfer tokens to recipient.
	// 3.  Close tmp_token_account.
	let config_seeds = &[RedeemerConfig::SEED_PREFIX.as_ref(), &[ctx.accounts.config.bump]];

	// Redeem the token transfer.
	token_bridge::complete_transfer_native_with_payload(CpiContext::new_with_signer(
		ctx.accounts.token_bridge_program.to_account_info(),
		token_bridge::CompleteTransferNativeWithPayload {
			payer: ctx.accounts.payer.to_account_info(),
			config: ctx.accounts.token_bridge_config.to_account_info(),
			vaa: ctx.accounts.vaa.to_account_info(),
			claim: ctx.accounts.token_bridge_claim.to_account_info(),
			foreign_endpoint: ctx.accounts.token_bridge_foreign_endpoint.to_account_info(),
			to: ctx.accounts.tmp_token_account.to_account_info(),
			redeemer: ctx.accounts.config.to_account_info(),
			custody: ctx.accounts.token_bridge_custody.to_account_info(),
			mint: ctx.accounts.mint.to_account_info(),
			custody_signer: ctx.accounts.token_bridge_custody_signer.to_account_info(),
			rent: ctx.accounts.rent.to_account_info(),
			system_program: ctx.accounts.system_program.to_account_info(),
			token_program: ctx.accounts.token_program.to_account_info(),
			wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
		},
		&[&config_seeds[..]],
	))?;

	let mut amount = token_bridge::denormalize_amount(
		ctx.accounts.vaa.data().amount(),
		ctx.accounts.mint.decimals,
	);

	let so_fee =
		(((amount as u128) * (ctx.accounts.fee_config.so_fee) as u128) / (RAY as u128)) as u64;

	let transaction_id =
		bytes_to_hex(&ctx.accounts.vaa.data().message().normalized_so_data.transaction_id);

	let actual_fee = if so_fee <= amount {
		// Transfer tokens so_fee from tmp_token_account to beneficiary.
		anchor_spl::token::transfer(
			CpiContext::new_with_signer(
				ctx.accounts.token_program.to_account_info(),
				anchor_spl::token::Transfer {
					from: ctx.accounts.tmp_token_account.to_account_info(),
					to: ctx.accounts.beneficiary_token_account.to_account_info(),
					authority: ctx.accounts.config.to_account_info(),
				},
				&[&config_seeds[..]],
			),
			so_fee,
		)?;

		so_fee
	} else {
		0
	};

	msg!("[DstAmount]: so_fee={}, bridge_amount={}", actual_fee, amount);

	amount -= actual_fee;

	// Transfer the other tokens from tmp_token_account to proxy recipient.
	let proxy_recipient_account = if check_a_to_b(ctx)? {
		ctx.accounts.whirlpool_token_owner_account_a.to_account_info()
	} else {
		ctx.accounts.whirlpool_token_owner_account_b.to_account_info()
	};

	anchor_spl::token::transfer(
		CpiContext::new_with_signer(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Transfer {
				from: ctx.accounts.tmp_token_account.to_account_info(),
				to: proxy_recipient_account,
				authority: ctx.accounts.config.to_account_info(),
			},
			&[&config_seeds[..]],
		),
		amount,
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
	))?;

	Ok((amount, transaction_id))
}
