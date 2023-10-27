use anchor_lang::prelude::*;
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Token, TokenAccount},
};
use spl_math::uint::U256;
use wormhole_anchor_sdk::{token_bridge, wormhole};

use crate::{
	constants::{SEED_PREFIX_BRIDGED, SEED_PREFIX_TMP},
	cross::{NormalizedSoData, NormalizedSwapData, NormalizedWormholeData},
	cross_request::CrossRequest,
	error::SoSwapError,
	instructions::relayer_fee::{check_relayer_fee, CheckRelayerFee},
	message::SoSwapMessage,
	state::{ForeignContract, PriceManager, SenderConfig, SoFeeConfig},
	utils::bytes_to_hex,
};

#[derive(Accounts)]
pub struct SoSwapWrappedWithoutSwap<'info> {
	/// Payer will pay Wormhole fee to transfer tokens and create temporary
	/// token account.
	#[account(mut)]
	pub payer: Signer<'info>,

	#[account(
		mut,
		has_one = payer @ SoSwapError::OwnerOnly,
		constraint = request.owner == config.key(),
		close = payer
	)]
	pub request: Box<Account<'info, CrossRequest>>,

	#[account(
		seeds = [SenderConfig::SEED_PREFIX],
		bump
	)]
	/// Sender Config account. Acts as the signer for the Token Bridge token
	/// transfer. Read-only.
	pub config: Box<Account<'info, SenderConfig>>,

	#[account(
		seeds = [SoFeeConfig::SEED_PREFIX],
		bump,
	)]
	/// SoFee Config account. Read-only.
	pub fee_config: Box<Account<'info, SoFeeConfig>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&request.dst_chain_id()?.to_le_bytes()[..],
			PriceManager::SEED_PREFIX
		],
		bump
	)]
	/// Price Manager account. Read-only.
	pub price_manager: Box<Account<'info, PriceManager>>,

	#[account(
		mut,
		address = fee_config.beneficiary @ SoSwapError::InvalidBeneficiary
	)]
	/// CHECK: collect relayer fee
	pub beneficiary_account: UncheckedAccount<'info>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&request.dst_chain_id()?.to_le_bytes()[..],
		],
		bump,
	)]
	/// Foreign Contract account. Send tokens to the contract specified in this
	/// account. Funnily enough, the Token Bridge program does not have any
	/// requirements for outbound transfers for the recipient chain to be
	/// registered. This account provides extra protection against sending
	/// tokens to an unregistered Wormhole chain ID. Read-only.
	pub foreign_contract: Box<Account<'info, ForeignContract>>,

	#[account(
		mut,
		seeds = [
			token_bridge::WrappedMint::SEED_PREFIX,
			&token_bridge_wrapped_meta.chain.to_be_bytes(),
			&token_bridge_wrapped_meta.token_address
		],
		bump,
		seeds::program = token_bridge_program
	)]
	/// Token Bridge wrapped mint info. This is the SPL token that will be
	/// bridged to the foreign contract. The wrapped mint PDA must agree
	/// with the native token's metadata. Mutable.
	pub token_bridge_wrapped_mint: Box<Account<'info, token_bridge::WrappedMint>>,

	#[account(
		mut,
		associated_token::mint = token_bridge_wrapped_mint,
		associated_token::authority = payer,
	)]
	pub from_token_account: Account<'info, TokenAccount>,

	#[account(
		init,
		payer = payer,
		seeds = [
			SEED_PREFIX_TMP,
			token_bridge_wrapped_mint.key().as_ref(),
		],
		bump,
		token::mint = token_bridge_wrapped_mint,
		token::authority = config,
	)]
	/// Program's temporary token account. This account is created before the
	/// instruction is invoked to temporarily take custody of the payer's
	/// tokens. When the tokens are finally bridged out, the token account
	/// will have zero balance and can be closed.
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
		address = config.token_bridge.authority_signer @ SoSwapError::InvalidTokenBridgeAuthoritySigner
	)]
	/// CHECK: Token Bridge authority signer. Read-only.
	pub token_bridge_authority_signer: UncheckedAccount<'info>,

	#[account(
		mut,
		address = config.token_bridge.wormhole_bridge @ SoSwapError::InvalidWormholeBridge,
	)]
	/// Wormhole bridge data. Mutable.
	pub wormhole_bridge: Box<Account<'info, wormhole::BridgeData>>,

	#[account(
		mut,
		seeds = [
			SEED_PREFIX_BRIDGED,
			&token_bridge_sequence.next_value().to_le_bytes()[..]
		],
		bump,
	)]
	/// CHECK: Wormhole Message. Token Bridge program writes info about the
	/// tokens transferred in this account for our program. Mutable.
	pub wormhole_message: UncheckedAccount<'info>,

	#[account(
		mut,
		address = config.token_bridge.emitter @ SoSwapError::InvalidTokenBridgeEmitter
	)]
	/// CHECK: Token Bridge emitter. Read-only.
	pub token_bridge_emitter: UncheckedAccount<'info>,

	#[account(
		mut,
		address = config.token_bridge.sequence @ SoSwapError::InvalidTokenBridgeSequence
	)]
	/// CHECK: Token Bridge sequence. Mutable.
	pub token_bridge_sequence: Account<'info, wormhole::SequenceTracker>,

	#[account(
		mut,
		address = config.token_bridge.wormhole_fee_collector @ SoSwapError::InvalidWormholeFeeCollector
	)]
	/// Wormhole fee collector. Mutable.
	pub wormhole_fee_collector: Account<'info, wormhole::FeeCollector>,

	/// System program.
	pub system_program: Program<'info, System>,

	/// Token program.
	pub token_program: Program<'info, Token>,

	/// Associated Token program.
	pub associated_token_program: Program<'info, AssociatedToken>,

	/// Clock sysvar.
	pub clock: Sysvar<'info, Clock>,

	/// Rent sysvar.
	pub rent: Sysvar<'info, Rent>,
}

impl<'info> CheckRelayerFee<'info> for Context<'_, '_, '_, '_, SoSwapWrappedWithoutSwap<'info>> {
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

	fn system_program(&self) -> AccountInfo<'info> {
		self.accounts.system_program.to_account_info()
	}

	fn fee_collector(&self) -> AccountInfo<'info> {
		self.accounts.beneficiary_account.to_account_info()
	}

	fn payer(&self) -> AccountInfo<'info> {
		self.accounts.payer.to_account_info()
	}
}

pub fn handler(ctx: Context<SoSwapWrappedWithoutSwap>) -> Result<()> {
	let parsed_wormhole_data = NormalizedWormholeData::decode_normalized_wormhole_data(
		&ctx.accounts.request.wormhole_data,
	)?;
	let parsed_so_data =
		NormalizedSoData::decode_normalized_so_data(&ctx.accounts.request.so_data)?;
	let parsed_swap_data_src =
		NormalizedSwapData::decode_normalized_swap_data(&ctx.accounts.request.swap_data_src)?;
	let parsed_swap_data_dst =
		NormalizedSwapData::decode_normalized_swap_data(&ctx.accounts.request.swap_data_dst)?;

	assert!(parsed_swap_data_src.is_empty(), "must be empty");
	let amount = parsed_so_data.amount.as_u64();
	require!(amount > 0, SoSwapError::ZeroBridgeAmount);

	let recipient_chain = CheckRelayerFee::check_wormhole_data(&ctx, &parsed_wormhole_data)?;

	let (flag, fee, _consume_value, dst_max_gas) =
		check_relayer_fee(&ctx, &parsed_wormhole_data, &parsed_so_data, &parsed_swap_data_dst)?;
	require!(flag, SoSwapError::CheckFeeFail);

	CheckRelayerFee::charge_relayer_fee(&ctx, fee)?;

	msg!(
		"[SoTransferStarted]: txid={}, sender={}, amount={}, s_token={}, dst_chain={}, receiver={}, r_token={}",
		bytes_to_hex(&parsed_so_data.transaction_id),
		ctx.accounts.payer.key(),
		parsed_so_data.amount,
		Pubkey::try_from(parsed_so_data.sending_asset_id.as_slice()).unwrap(),
		&parsed_so_data.destination_chain_id,
		bytes_to_hex(&parsed_so_data.receiver),
		bytes_to_hex(&parsed_so_data.receiving_asset_id)
	);

	msg!("[SrcAmount]: relayer_fee={}, bridge_amount={}", fee, amount);

	msg!(
		"[Wormhole]: dst_chain={}, sequence={}",
		recipient_chain,
		ctx.accounts.token_bridge_sequence.sequence
	);

	publish_transfer(
		&ctx,
		amount,
		parsed_wormhole_data,
		parsed_so_data,
		parsed_swap_data_dst,
		recipient_chain,
		dst_max_gas,
	)
}

fn publish_transfer(
	ctx: &Context<SoSwapWrappedWithoutSwap>,
	amount: u64,
	parsed_wormhole_data: NormalizedWormholeData,
	parsed_so_data: NormalizedSoData,
	parsed_swap_data_dst: Vec<NormalizedSwapData>,
	recipient_chain: u16,
	dst_max_gas: U256,
) -> Result<()> {
	// These seeds are used to:
	// 1.  Sign the Sender Config's token account to delegate approval of amount.
	// 2.  Sign Token Bridge program's transfer_wrapped instruction.
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
		amount,
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
		amount,
	)?;

	// Serialize SoSwapMessage as encoded payload for Token Bridge
	// transfer.
	let payload = SoSwapMessage {
		dst_max_gas_price: parsed_wormhole_data.dst_max_gas_price_in_wei_for_relayer,
		dst_max_gas,
		normalized_so_data: parsed_so_data,
		normalized_swap_data: parsed_swap_data_dst,
	}
	.try_to_vec()?;

	// Bridge wrapped token with encoded payload.
	token_bridge::transfer_wrapped_with_payload(
		CpiContext::new_with_signer(
			ctx.accounts.token_bridge_program.to_account_info(),
			token_bridge::TransferWrappedWithPayload {
				payer: ctx.accounts.payer.to_account_info(),
				config: ctx.accounts.token_bridge_config.to_account_info(),
				from: ctx.accounts.tmp_token_account.to_account_info(),
				from_owner: ctx.accounts.config.to_account_info(),
				wrapped_mint: ctx.accounts.token_bridge_wrapped_mint.to_account_info(),
				wrapped_metadata: ctx.accounts.token_bridge_wrapped_meta.to_account_info(),
				authority_signer: ctx.accounts.token_bridge_authority_signer.to_account_info(),
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
		amount,
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
