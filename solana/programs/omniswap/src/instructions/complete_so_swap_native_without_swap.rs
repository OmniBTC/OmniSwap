use anchor_lang::{prelude::*, system_program::Transfer};
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Mint, Token, TokenAccount},
};
use wormhole_anchor_sdk::{token_bridge, wormhole};

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
pub struct CompleteSoSwapNativeWithoutSwap<'info> {
	#[account(mut)]
	/// Payer will pay Wormhole fee to transfer tokens and create temporary
	/// token account.
	pub payer: Signer<'info>,

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
	pub wsol_mint: Option<Account<'info, Mint>>,

	#[account(
		mut,
		address = recipient_token_account.owner @ SoSwapError::InvalidRecipient
	)]
	/// CHECK: the recipient account
	pub recipient: Option<UncheckedAccount<'info>>,

	#[account(
		address = vaa.data().mint()
	)]
	/// Mint info. This is the SPL token that will be bridged over from the
	/// foreign contract. This must match the token address specified in the
	/// signed Wormhole message. Read-only.
	pub mint: Account<'info, Mint>,

	#[account(
		mut,
		constraint = recipient_token_account.mint == mint.key(),
	)]
	/// Recipient associated token account.
	pub recipient_token_account: Box<Account<'info, TokenAccount>>,

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
	pub token_bridge_foreign_endpoint: Account<'info, token_bridge::EndpointRegistration>,

	#[account(
		mut,
		seeds = [mint.key().as_ref()],
		bump,
		seeds::program = token_bridge_program
	)]
	/// CHECK: Token Bridge custody. This is the Token Bridge program's token
	/// account that holds this mint's balance.
	pub token_bridge_custody: Account<'info, TokenAccount>,

	#[account(
		address = config.token_bridge.custody_signer @ SoSwapError::InvalidTokenBridgeCustodySigner
	)]
	/// CHECK: Token Bridge custody signer. Read-only.
	pub token_bridge_custody_signer: UncheckedAccount<'info>,

	/// System program.
	pub system_program: Program<'info, System>,

	/// Token program.
	pub token_program: Program<'info, Token>,

	/// Associated Token program.
	pub associated_token_program: Program<'info, AssociatedToken>,

	/// Rent sysvar.
	pub rent: Sysvar<'info, Rent>,
}

pub fn handler(
	ctx: Context<CompleteSoSwapNativeWithoutSwap>,
	_vaa_hash: [u8; 32],
	skip_verify_soswap_message: bool,
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

	if skip_verify_soswap_message {
		return complete_transfer(&ctx, false)
	}

	// The intended recipient must agree with the recipient.
	let soswap_message = ctx.accounts.vaa.message().data();
	require!(*soswap_message != Default::default(), SoSwapError::DeserializeSoSwapMessageFail);
	require!(
		ctx.accounts.recipient_token_account.owner.as_ref() ==
			soswap_message.normalized_so_data.receiver,
		SoSwapError::InvalidRecipient
	);

	complete_transfer(&ctx, true)
}

fn complete_transfer(
	ctx: &Context<CompleteSoSwapNativeWithoutSwap>,
	require_so_fee: bool,
) -> Result<()> {
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

	let mut tx_id = "".to_string();
	let mut status = 2u32;
	let mut need_unwrap_sol = false;
	if require_so_fee {
		let so_msg = ctx.accounts.vaa.data().message();
		let transaction_id = bytes_to_hex(&so_msg.normalized_so_data.transaction_id);

		let so_receiving_asset =
			Pubkey::try_from(so_msg.normalized_so_data.receiving_asset_id.as_slice()).unwrap();
		need_unwrap_sol = so_receiving_asset == UnwrapSOLKey;
		if need_unwrap_sol {
			let recipient = &ctx.accounts.recipient.clone().unwrap();
			require!(
				recipient.key().as_ref() == so_msg.normalized_so_data.receiver,
				SoSwapError::InvalidRecipient
			);
		}

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

		tx_id = transaction_id;
		status = 0;
	}

	let mut need_close_unwrap_sol_account = ctx.accounts.unwrap_sol_account.is_some();
	let receive_token = if need_unwrap_sol &&
		need_close_unwrap_sol_account &&
		ctx.accounts.tmp_token_account.mint == WrapSOLKey &&
		ctx.accounts.recipient.is_some()
	{
		let unwrap_sol_account = &ctx.accounts.unwrap_sol_account.clone().unwrap();
		let recipient = &ctx.accounts.recipient.clone().unwrap();

		// 1. transfer: tmp_token_account(wsol) => unwrap_sol_account(wsol)
		anchor_spl::token::transfer(
			CpiContext::new_with_signer(
				ctx.accounts.token_program.to_account_info(),
				anchor_spl::token::Transfer {
					from: ctx.accounts.tmp_token_account.to_account_info(),
					to: unwrap_sol_account.to_account_info(),
					authority: ctx.accounts.config.to_account_info(),
				},
				&[&config_seeds[..]],
			),
			amount,
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
		need_close_unwrap_sol_account = false;

		// 3. transfer: proxy(sol) -> recipient(sol)
		anchor_lang::system_program::transfer(
			CpiContext::new(
				ctx.accounts.system_program.to_account_info(),
				Transfer {
					from: ctx.accounts.payer.to_account_info(),
					to: recipient.to_account_info(),
				},
			),
			amount,
		)?;

		UnwrapSOLKey.to_string()
	} else {
		// Transfer the other tokens from tmp_token_account to recipient.
		anchor_spl::token::transfer(
			CpiContext::new_with_signer(
				ctx.accounts.token_program.to_account_info(),
				anchor_spl::token::Transfer {
					from: ctx.accounts.tmp_token_account.to_account_info(),
					to: ctx.accounts.recipient_token_account.to_account_info(),
					authority: ctx.accounts.config.to_account_info(),
				},
				&[&config_seeds[..]],
			),
			amount,
		)?;

		ctx.accounts.recipient_token_account.mint.to_string()
	};

	msg!(
		"[SoTransferCompleted]: status={}, amount={}, r_token={}, txid={}",
		status,
		amount,
		receive_token,
		tx_id,
	);

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

	if need_close_unwrap_sol_account {
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
	};

	Ok(())
}
