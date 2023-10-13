use anchor_lang::prelude::*;
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Token, TokenAccount},
};
use wormhole_anchor_sdk::{token_bridge, wormhole};

use crate::{
	constants::{SEED_PREFIX_BRIDGED, SEED_PREFIX_TMP},
	cross::{NormalizedSoData, NormalizedWormholeData},
	error::SoSwapError,
	message::SoSwapMessage,
	state::{ForeignContract, SenderConfig},
};

#[derive(Accounts)]
#[instruction(
	amount: u64,
	wormhole_data: Vec<u8>,
	so_data: Vec<u8>,
)]
pub struct SoSwapWrappedWithoutSwap<'info> {
	#[account(mut)]
	/// Payer will pay Wormhole fee to transfer tokens and create temporary
	/// token account.
	pub payer: Signer<'info>,

	#[account(
		seeds = [SenderConfig::SEED_PREFIX],
		bump
	)]
	/// Sender Config account. Acts as the Token Bridge sender PDA. Mutable.
	pub config: Box<Account<'info, SenderConfig>>,

	#[account(
		seeds = [
			ForeignContract::SEED_PREFIX,
			&NormalizedSoData::decode_normalized_so_data(&so_data)?.destination_chain_id.to_le_bytes()[..]
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
		mut,
		address = config.token_bridge.config @ SoSwapError::InvalidTokenBridgeConfig
	)]
	/// Token Bridge config. Mutable.
	pub token_bridge_config: Account<'info, token_bridge::Config>,

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
	/// tokens transferred in this account.
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

pub fn handler(
	ctx: Context<SoSwapWrappedWithoutSwap>,
	amount: u64,
	wormhole_data: Vec<u8>,
	so_data: Vec<u8>,
) -> Result<()> {
	require!(amount > 0, SoSwapError::ZeroBridgeAmount);

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
	//     of amount.
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
		dst_max_gas_price: normalized_wormhole_data.dst_max_gas_price_in_wei_for_relayer,
		// TODO: dst_max_gas
		dst_max_gas: Default::default(),
		normalized_so_data,
		normalized_swap_data: Default::default(),
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
