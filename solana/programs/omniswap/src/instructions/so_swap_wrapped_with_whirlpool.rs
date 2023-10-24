use anchor_lang::{prelude::*, system_program::Transfer};
use anchor_spl::{
	associated_token::AssociatedToken,
	token::{Token, TokenAccount},
};
use spl_math::uint::U256;
use wormhole_anchor_sdk::{token_bridge, wormhole};

use crate::{
	constants::{RAY, SEED_PREFIX_BRIDGED, SEED_PREFIX_TMP},
	cross::{NormalizedSoData, NormalizedSwapData, NormalizedWormholeData},
	error::SoSwapError,
	message::SoSwapMessage,
	state::{ForeignContract, PriceManager, SenderConfig, SoFeeConfig},
	utils::bytes_to_hex,
};

use super::swap_whirlpool::{swap_by_whirlpool, SoSwapWithWhirlpool};

#[derive(Accounts)]
#[instruction(
	wormhole_data: Vec<u8>,
	swap_data_src: Vec<u8>,
	so_data: Vec<u8>,
)]
pub struct SoSwapWrappedWithWhirlpool<'info> {
	/// Payer will pay Wormhole fee to transfer tokens and create temporary
	/// token account.
	#[account(mut)]
	pub payer: Signer<'info>,

	// 1. soswap configs
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
			&NormalizedSoData::decode_normalized_so_data(&so_data)?.destination_chain_id.to_le_bytes()[..],
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

	// 2. whirlpool configs
	/// CHECK: Whirlpool Program
	pub whirlpool_program: AccountInfo<'info>,
	/// CHECK: Whirlpool Account
	#[account(mut)]
	pub whirlpool_account: AccountInfo<'info>,
	/// CHECK: token_owner_account_a,
	/// Payer's associated token account.
	#[account(mut)]
	pub whirlpool_token_owner_account_a: Box<Account<'info, TokenAccount>>,
	/// CHECK: token_vault_a
	#[account(mut)]
	pub whirlpool_token_vault_a: AccountInfo<'info>,
	/// CHECK: token_owner_account_b
	/// Payer's associated token account.
	#[account(mut)]
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

	// 4. system configs
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

impl<'info> SoSwapWithWhirlpool<'info>
	for Context<'_, '_, '_, '_, SoSwapWrappedWithWhirlpool<'info>>
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
}

pub fn handler(
	ctx: Context<SoSwapWrappedWithWhirlpool>,
	wormhole_data: Vec<u8>,
	swap_data_src: Vec<u8>,
	so_data: Vec<u8>,
	swap_data_dst: Vec<u8>,
) -> Result<()> {
	let parsed_wormhole_data =
		NormalizedWormholeData::decode_normalized_wormhole_data(&wormhole_data)?;
	let parsed_so_data = NormalizedSoData::decode_normalized_so_data(&so_data)?;
	let parsed_swap_data_src = NormalizedSwapData::decode_normalized_swap_data(&swap_data_src)?;
	let parsed_swap_data_dst = NormalizedSwapData::decode_normalized_swap_data(&swap_data_dst)?;

	let a_to_b = swap_by_whirlpool(&ctx, &parsed_swap_data_src, &parsed_so_data)?;

	let amount = if a_to_b {
		let token_value_b_before = ctx.accounts.whirlpool_token_owner_account_b.amount;
		ctx.accounts.whirlpool_token_owner_account_b.reload()?;
		let token_value_b_after = ctx.accounts.whirlpool_token_owner_account_b.amount;

		token_value_b_after.checked_sub(token_value_b_before).unwrap()
	} else {
		let token_value_a_before = ctx.accounts.whirlpool_token_owner_account_a.amount;
		ctx.accounts.whirlpool_token_owner_account_a.reload()?;
		let token_value_a_after = ctx.accounts.whirlpool_token_owner_account_a.amount;

		token_value_a_after.checked_sub(token_value_a_before).unwrap()
	};

	require!(amount > 0, SoSwapError::ZeroBridgeAmount);

	let recipient_chain = check_parameters(&ctx, &parsed_wormhole_data)?;

	let (flag, fee, _consume_value, dst_max_gas) = check_relayer_fee(
		&ctx,
		&parsed_wormhole_data,
		&parsed_so_data,
		&parsed_swap_data_dst,
		recipient_chain,
	)?;
	require!(flag, SoSwapError::CheckFeeFail);

	charge_relayer_fee(&ctx, fee)?;

	msg!("[SoTransferStarted]: transaction_id={}", bytes_to_hex(&parsed_so_data.transaction_id));

	let sequence = ctx.accounts.token_bridge_sequence.sequence;
	msg!(
		"[TransferFromWormholeEvent]: src_wormhole_chain_id={}, dst_wormhole_chain_id={}, sequence={}",
		&parsed_so_data.source_chain_id,
		&parsed_so_data.destination_chain_id,
		sequence
	);

	msg!("[SrcAmount] relayer_fee={}, cross_amount={}", fee, amount);

	publish_transfer(
		&ctx,
		amount,
		parsed_wormhole_data,
		parsed_so_data,
		parsed_swap_data_dst,
		recipient_chain,
		dst_max_gas,
		a_to_b,
	)
}

#[allow(clippy::too_many_arguments)]
fn publish_transfer(
	ctx: &Context<SoSwapWrappedWithWhirlpool>,
	amount: u64,
	parsed_wormhole_data: NormalizedWormholeData,
	parsed_so_data: NormalizedSoData,
	parsed_swap_data_dst: Vec<NormalizedSwapData>,
	recipient_chain: u16,
	dst_max_gas: U256,
	a_to_b: bool,
) -> Result<()> {
	// These seeds are used to:
	// 1.  Sign the Sender Config's token account to delegate approval of amount.
	// 2.  Sign Token Bridge program's transfer_wrapped instruction.
	// 3.  Close tmp_token_account.
	let config_seeds = &[SenderConfig::SEED_PREFIX.as_ref(), &[ctx.accounts.config.bump]];

	// First transfer tokens from payer to tmp_token_account.
	let from_token_account_info = if a_to_b {
		ctx.accounts.whirlpool_token_owner_account_b.to_account_info()
	} else {
		ctx.accounts.whirlpool_token_owner_account_a.to_account_info()
	};
	anchor_spl::token::transfer(
		CpiContext::new(
			ctx.accounts.token_program.to_account_info(),
			anchor_spl::token::Transfer {
				from: from_token_account_info,
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

fn check_parameters(
	ctx: &Context<SoSwapWrappedWithWhirlpool>,
	parsed_wormhole_data: &NormalizedWormholeData,
) -> Result<u16> {
	let recipient_chain = parsed_wormhole_data.dst_wormhole_chain_id;

	require!(
		recipient_chain > 0 &&
			recipient_chain != wormhole::CHAIN_ID_SOLANA &&
			!parsed_wormhole_data.dst_so_diamond.iter().all(|&x| x == 0) &&
			parsed_wormhole_data.dst_so_diamond ==
				ctx.accounts.foreign_contract.address.to_vec(),
		SoSwapError::InvalidRecipient,
	);

	Ok(recipient_chain)
}

fn check_relayer_fee(
	ctx: &Context<SoSwapWrappedWithWhirlpool>,
	parsed_wormhole_data: &NormalizedWormholeData,
	parsed_so_data: &NormalizedSoData,
	parsed_swap_data_dst: &Vec<NormalizedSwapData>,
	recipient_chain: u16,
) -> Result<(bool, u64, u64, U256)> {
	let estimate_reserve = U256::from(ctx.accounts.fee_config.estimate_reserve);

	let ratio = ctx.accounts.price_manager.current_price_ratio;

	let dst_max_gas = ctx.accounts.foreign_contract.estimate_complete_soswap_gas(
		&NormalizedSoData::encode_normalized_so_data(parsed_so_data),
		parsed_wormhole_data,
		&NormalizedSwapData::encode_normalized_swap_data(parsed_swap_data_dst),
	);

	let dst_fee = parsed_wormhole_data
		.dst_max_gas_price_in_wei_for_relayer
		.checked_mul(dst_max_gas)
		.unwrap();

	let one = U256::from(RAY);
	let mut src_fee = dst_fee
		.checked_mul(U256::from(ratio))
		.unwrap()
		.checked_div(one)
		.unwrap()
		.checked_mul(estimate_reserve)
		.unwrap()
		.checked_div(one)
		.unwrap();

	// Solana decimals = 9
	if recipient_chain == 22 {
		// Aptos chain, decimals=8
		// decimal * 10
		src_fee = src_fee.checked_mul(10u64.into()).unwrap();
	} else {
		// Evm chain, decimals=18
		// decimal / 1e9
		src_fee = src_fee.checked_div(1_000_000_000u64.into()).unwrap();
	};

	let mut consume_value = ctx.accounts.wormhole_bridge.config.fee;

	let src_fee = src_fee.as_u64();
	consume_value += src_fee;

	let mut flag = false;

	let wormhole_fee = parsed_wormhole_data.wormhole_fee.as_u64();
	if consume_value <= wormhole_fee {
		flag = true;
	};

	Ok((flag, src_fee, consume_value, dst_max_gas))
}

fn charge_relayer_fee(ctx: &Context<SoSwapWrappedWithWhirlpool>, relayer_fee: u64) -> Result<()> {
	// Pay fee
	anchor_lang::system_program::transfer(
		CpiContext::new(
			ctx.accounts.system_program.to_account_info(),
			Transfer {
				from: ctx.accounts.payer.to_account_info(),
				to: ctx.accounts.beneficiary_account.to_account_info(),
			},
		),
		relayer_fee,
	)
}