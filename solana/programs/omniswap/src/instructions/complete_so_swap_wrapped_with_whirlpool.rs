use anchor_lang::prelude::*;
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Token, TokenAccount},
};
use wormhole_anchor_sdk::{token_bridge, wormhole};

use super::swap_whirlpool::{check_a_to_b, swap_by_whirlpool, SoSwapWithWhirlpool};
use crate::{
	constants::{RAY, SEED_PREFIX_TMP},
	error::SoSwapError,
	message::PostedSoSwapMessage,
	state::{ForeignContract, RedeemerConfig, SoFeeConfig},
	utils::bytes_to_hex,
};

#[derive(Accounts)]
#[instruction(vaa_hash: [u8; 32])]
pub struct CompleteSoSwapWrappedWithWhirlpool<'info> {
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
		associated_token::mint = token_bridge_wrapped_mint,
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

	// 3. wormhole configs
	#[account(
		mut,
		seeds = [
			token_bridge::WrappedMint::SEED_PREFIX,
			&vaa.data().token_chain().to_be_bytes(),
			vaa.data().token_address()
		],
		bump,
		seeds::program = token_bridge_program
	)]
	/// Token Bridge wrapped mint info. This is the SPL token that will be
	/// bridged from the foreign contract. The wrapped mint PDA must agree
	/// with the native token's metadata in the wormhole message. Mutable.
	pub token_bridge_wrapped_mint: Box<Account<'info, token_bridge::WrappedMint>>,

	#[account(mut)]
	/// Recipient associated token account.
	/// If swap ok, transfer the receiving token to this account
	pub recipient_token_account: Box<Account<'info, TokenAccount>>,

	#[account(
		mut,
		constraint = recipient_token_account.mint == token_bridge_wrapped_mint.key(),
	)]
	/// Recipient associated token account.
	/// If swap failed, transfer the bridge token to this account
	pub recipient_bridge_token_token: Box<Account<'info, TokenAccount>>,

	#[account(
		init,
		payer = payer,
		seeds = [
			SEED_PREFIX_TMP,
			token_bridge_wrapped_mint.key().as_ref(),
		],
		bump,
		token::mint = token_bridge_wrapped_mint,
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
		seeds = [
			token_bridge::WrappedMeta::SEED_PREFIX,
			token_bridge_wrapped_mint.key().as_ref()
		],
		bump,
		seeds::program = token_bridge_program
	)]
	/// Token Bridge program's wrapped metadata, which stores info
	/// about the token from its native chain:
	///   * Wormhole Chain ID
	///   * Token's native contract address
	///   * Token's native decimals
	pub token_bridge_wrapped_meta: Account<'info, token_bridge::WrappedMeta>,

	#[account(
		address = config.token_bridge.config @ SoSwapError::InvalidTokenBridgeConfig
	)]
	/// Token Bridge config. Read-only.
	pub token_bridge_config: Account<'info, token_bridge::Config>,

	#[account(
		seeds = [
			wormhole::SEED_PREFIX_POSTED_VAA,
			&vaa_hash
		],
		bump,
		seeds::program = wormhole_program,
		constraint = vaa.data().to() == crate::ID || vaa.data().to() == config.key() @ SoSwapError::InvalidTransferToAddress,
		constraint = vaa.data().to_chain() == wormhole::CHAIN_ID_SOLANA @ SoSwapError::InvalidTransferToChain,
		constraint = vaa.data().token_chain() != wormhole::CHAIN_ID_SOLANA @ SoSwapError::InvalidTransferTokenChain
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
	pub token_bridge_foreign_endpoint: Account<'info, token_bridge::EndpointRegistration>,

	#[account(
		address = config.token_bridge.mint_authority @ SoSwapError::InvalidTokenBridgeMintAuthority
	)]
	/// CHECK: Token Bridge custody signer. Read-only.
	pub token_bridge_mint_authority: UncheckedAccount<'info>,

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
	for Context<'_, '_, '_, '_, CompleteSoSwapWrappedWithWhirlpool<'info>>
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
		self.accounts.token_bridge_wrapped_mint.to_account_info()
	}

	fn is_origin(&self) -> bool {
		false
	}
}

pub fn handler(
	ctx: Context<CompleteSoSwapWrappedWithWhirlpool>,
	_vaa_hash: [u8; 32],
) -> Result<()> {
	// The Token Bridge program's claim account is only initialized when
	// a transfer is redeemed (and the boolean value `true` is written as
	// its data).
	//
	// The Token Bridge program will automatically fail if this transfer
	// is redeemed again. But we choose to short-circuit the failure as the
	// first evaluation of this instruction.
	require!(ctx.accounts.token_bridge_claim.data_is_empty(), SoSwapError::AlreadyRedeemed);
	require!(ctx.accounts.payer.key() == ctx.accounts.config.proxy, SoSwapError::InvalidProxy);

	// The intended recipient must agree with the recipient.
	let soswap_message = ctx.accounts.vaa.message().data();
	require!(*soswap_message != Default::default(), SoSwapError::DeserializeSoSwapMessageFail);
	require!(
		ctx.accounts.recipient_token_account.owner.to_bytes() == soswap_message.recipient(),
		SoSwapError::InvalidRecipient
	);
	require!(
		ctx.accounts.recipient_bridge_token_token.owner.to_bytes() == soswap_message.recipient(),
		SoSwapError::InvalidRecipient
	);

	// 1. redeem bridge token: tmp_account => proxy_a_or_b
	let bridge_amount = complete_redeem(&ctx)?;

	// 2. swap bridge token to receiving token: proxy_a <=> proxy_b
	let so_msg = ctx.accounts.vaa.data().data();
	if let Ok(a_to_b) =
		swap_by_whirlpool(&ctx, &so_msg.normalized_swap_data, &so_msg.normalized_so_data)
	{
		// 3. swap ok, send receiving token: proxy_a_or_b => recipient
		let (other_proxy_recipient_account, amount) = if a_to_b {
			let token_value_b_before = ctx.accounts.whirlpool_token_owner_account_b.amount;
			ctx.accounts.whirlpool_token_owner_account_b.reload()?;
			let token_value_b_after = ctx.accounts.whirlpool_token_owner_account_b.amount;

			let amount = token_value_b_after.checked_sub(token_value_b_before).unwrap();
			let account = ctx.accounts.whirlpool_token_owner_account_b.to_account_info();

			(account, amount)
		} else {
			let token_value_a_before = ctx.accounts.whirlpool_token_owner_account_a.amount;
			ctx.accounts.whirlpool_token_owner_account_a.reload()?;
			let token_value_a_after = ctx.accounts.whirlpool_token_owner_account_a.amount;

			let amount = token_value_a_after.checked_sub(token_value_a_before).unwrap();
			let account = ctx.accounts.whirlpool_token_owner_account_a.to_account_info();

			(account, amount)
		};

		anchor_spl::token::transfer(
			CpiContext::new(
				ctx.accounts.token_program.to_account_info(),
				anchor_spl::token::Transfer {
					from: other_proxy_recipient_account,
					to: ctx.accounts.recipient_token_account.to_account_info(),
					authority: ctx.accounts.config.to_account_info(),
				},
			),
			amount,
		)?;

		msg!("[FinalSwapOk]: final_amount={}", amount);

		return Ok(())
	}

	// 4. swap fail, send bridge token: proxy_a_or_b => recipient
	let proxy_recipient_account = if check_a_to_b(&ctx)? {
		ctx.accounts.whirlpool_token_owner_account_a.to_account_info()
	} else {
		ctx.accounts.whirlpool_token_owner_account_b.to_account_info()
	};

	msg!("[FinalSwapFail]: final_amount={}", bridge_amount);
	anchor_spl::token::transfer(
		CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Transfer {
				from: proxy_recipient_account,
				to: ctx.accounts.recipient_bridge_token_token.to_account_info(),
				authority: ctx.accounts.config.to_account_info(),
			},
		),
		bridge_amount,
	)
}

fn complete_redeem(ctx: &Context<CompleteSoSwapWrappedWithWhirlpool>) -> Result<u64> {
	// These seeds are used to:
	// 1.  Redeem Token Bridge program's
	//     complete_transfer_wrapped_with_payload.
	// 2.  Transfer tokens to recipient.
	// 3.  Close tmp_token_account.
	let config_seeds = &[RedeemerConfig::SEED_PREFIX.as_ref(), &[ctx.accounts.config.bump]];

	// Redeem the token transfer.
	token_bridge::complete_transfer_wrapped_with_payload(CpiContext::new_with_signer(
		ctx.accounts.token_bridge_program.to_account_info(),
		token_bridge::CompleteTransferWrappedWithPayload {
			payer: ctx.accounts.payer.to_account_info(),
			config: ctx.accounts.token_bridge_config.to_account_info(),
			vaa: ctx.accounts.vaa.to_account_info(),
			claim: ctx.accounts.token_bridge_claim.to_account_info(),
			foreign_endpoint: ctx.accounts.token_bridge_foreign_endpoint.to_account_info(),
			to: ctx.accounts.tmp_token_account.to_account_info(),
			redeemer: ctx.accounts.config.to_account_info(),
			wrapped_mint: ctx.accounts.token_bridge_wrapped_mint.to_account_info(),
			wrapped_metadata: ctx.accounts.token_bridge_wrapped_meta.to_account_info(),
			mint_authority: ctx.accounts.token_bridge_mint_authority.to_account_info(),
			rent: ctx.accounts.rent.to_account_info(),
			system_program: ctx.accounts.system_program.to_account_info(),
			token_program: ctx.accounts.token_program.to_account_info(),
			wormhole_program: ctx.accounts.wormhole_program.to_account_info(),
		},
		&[&config_seeds[..]],
	))?;

	let mut amount = ctx.accounts.vaa.data().amount();

	let so_fee =
		(((amount as u128) * (ctx.accounts.fee_config.so_fee) as u128) / (RAY as u128)) as u64;

	let tx_sender = ctx.accounts.payer.key;
	let so_receiver =
		Pubkey::try_from(ctx.accounts.vaa.data().message().normalized_so_data.receiver.as_slice())
			.map_err(|_| SoSwapError::DeserializeSoSwapMessageFail)?;
	let token = Pubkey::try_from(
		ctx.accounts
			.vaa
			.data()
			.message()
			.normalized_so_data
			.receiving_asset_id
			.as_slice(),
	)
	.map_err(|_| SoSwapError::DeserializeSoSwapMessageFail)?;
	let transaction_id =
		bytes_to_hex(&ctx.accounts.vaa.data().message().normalized_so_data.transaction_id);

	msg!(
		"[OriginEvnet]: tx_sender={}, so_receiver={}, token={}, amount={}",
		tx_sender,
		so_receiver,
		token,
		amount
	);

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

	amount -= actual_fee;

	msg!(
		"[SoTransferCompleted] transaction_id={}, actual_receiving_amount={}",
		transaction_id,
		amount
	);

	msg!("[DstAmount] so_fee={}", actual_fee);

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

	Ok(amount)
}