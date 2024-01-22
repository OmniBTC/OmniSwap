use anchor_lang::{prelude::*, solana_program};
use anchor_spl;

#[derive(AnchorDeserialize, AnchorSerialize)]
/// Token Bridge instructions.
pub enum Instruction {
	Initialize, // placeholder
	AttestToken {
		batch_id: u32,
	},
	CompleteNative {},
	CompleteWrapped {},
	TransferWrapped {
		batch_id: u32,
		amount: u64,
		fee: u64,
		recipient_address: [u8; 32],
		recipient_chain: u16,
	},
	TransferNative {
		batch_id: u32,
		amount: u64,
		fee: u64,
		recipient_address: [u8; 32],
		recipient_chain: u16,
	},
	RegisterChain, // placeholder (governance action)
	CreateWrapped {},
	UpgradeContract, // placeholder (governance action)
	CompleteNativeWithPayload {},
	CompleteWrappedWithPayload {},
	TransferWrappedWithPayload {
		batch_id: u32,
		amount: u64,
		recipient_address: [u8; 32],
		recipient_chain: u16,
		payload: Vec<u8>,
		cpi_program_id: Option<Pubkey>,
	},
	TransferNativeWithPayload {
		batch_id: u32,
		amount: u64,
		recipient_address: [u8; 32],
		recipient_chain: u16,
		payload: Vec<u8>,
		cpi_program_id: Option<Pubkey>,
	},
}

#[derive(Accounts)]
pub struct TransferNativeWithPayload<'info> {
	pub payer: AccountInfo<'info>,
	pub config: AccountInfo<'info>,
	pub from: AccountInfo<'info>,
	pub mint: AccountInfo<'info>,
	pub custody: AccountInfo<'info>,
	pub authority_signer: AccountInfo<'info>,
	pub custody_signer: AccountInfo<'info>,
	pub wormhole_bridge: AccountInfo<'info>,
	pub wormhole_message: AccountInfo<'info>,
	pub wormhole_emitter: AccountInfo<'info>,
	pub wormhole_sequence: AccountInfo<'info>,
	pub wormhole_fee_collector: AccountInfo<'info>,
	pub clock: AccountInfo<'info>,
	pub sender: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
	pub token_program: AccountInfo<'info>,
	pub wormhole_program: AccountInfo<'info>,
}

pub fn transfer_native_with_payload<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, TransferNativeWithPayload<'info>>,
	batch_id: u32,
	amount: u64,
	recipient_address: [u8; 32],
	recipient_chain: u16,
	payload: Vec<u8>,
	cpi_program_id: &Pubkey,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new_readonly(ctx.accounts.config.key(), false),
			AccountMeta::new(ctx.accounts.from.key(), false),
			AccountMeta::new(ctx.accounts.mint.key(), false),
			AccountMeta::new(ctx.accounts.custody.key(), false),
			AccountMeta::new_readonly(ctx.accounts.authority_signer.key(), false),
			AccountMeta::new_readonly(ctx.accounts.custody_signer.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_bridge.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_message.key(), true),
			AccountMeta::new_readonly(ctx.accounts.wormhole_emitter.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_sequence.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_fee_collector.key(), false),
			AccountMeta::new_readonly(solana_program::sysvar::clock::id(), false),
			AccountMeta::new_readonly(ctx.accounts.sender.key(), true),
			AccountMeta::new_readonly(solana_program::sysvar::rent::id(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wormhole_program.key(), false),
			AccountMeta::new_readonly(anchor_spl::token::spl_token::id(), false),
		],
		data: Instruction::TransferNativeWithPayload {
			batch_id,
			amount,
			recipient_address,
			recipient_chain,
			payload,
			cpi_program_id: Some(*cpi_program_id),
		}
		.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}

#[derive(Accounts)]
pub struct CompleteTransferNativeWithPayload<'info> {
	pub payer: AccountInfo<'info>,
	pub config: AccountInfo<'info>,
	pub vaa: AccountInfo<'info>,
	pub claim: AccountInfo<'info>,
	pub foreign_endpoint: AccountInfo<'info>,
	pub to: AccountInfo<'info>,
	pub redeemer: AccountInfo<'info>,
	pub custody: AccountInfo<'info>,
	pub mint: AccountInfo<'info>,
	pub custody_signer: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
	pub token_program: AccountInfo<'info>,
	pub wormhole_program: AccountInfo<'info>,
}

pub fn complete_transfer_native_with_payload<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, CompleteTransferNativeWithPayload<'info>>,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new_readonly(ctx.accounts.config.key(), false),
			AccountMeta::new_readonly(ctx.accounts.vaa.key(), false),
			AccountMeta::new(ctx.accounts.claim.key(), false),
			AccountMeta::new_readonly(ctx.accounts.foreign_endpoint.key(), false),
			AccountMeta::new(ctx.accounts.to.key(), false),
			AccountMeta::new_readonly(ctx.accounts.redeemer.key(), true),
			AccountMeta::new(ctx.accounts.to.key(), false), // to_fees, lol
			AccountMeta::new(ctx.accounts.custody.key(), false),
			AccountMeta::new_readonly(ctx.accounts.mint.key(), false),
			AccountMeta::new_readonly(ctx.accounts.custody_signer.key(), false),
			AccountMeta::new_readonly(solana_program::sysvar::rent::id(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wormhole_program.key(), false),
			AccountMeta::new_readonly(anchor_spl::token::spl_token::id(), false),
		],
		data: Instruction::CompleteNativeWithPayload {}.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}

#[derive(Accounts)]
pub struct TransferWrappedWithPayload<'info> {
	pub payer: AccountInfo<'info>,
	pub config: AccountInfo<'info>,
	pub from: AccountInfo<'info>,
	pub from_owner: AccountInfo<'info>,
	pub wrapped_mint: AccountInfo<'info>,
	pub wrapped_metadata: AccountInfo<'info>,
	pub authority_signer: AccountInfo<'info>,
	pub wormhole_bridge: AccountInfo<'info>,
	pub wormhole_message: AccountInfo<'info>,
	pub wormhole_emitter: AccountInfo<'info>,
	pub wormhole_sequence: AccountInfo<'info>,
	pub wormhole_fee_collector: AccountInfo<'info>,
	pub clock: AccountInfo<'info>,
	pub sender: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
	pub token_program: AccountInfo<'info>,
	pub wormhole_program: AccountInfo<'info>,
}

pub fn transfer_wrapped_with_payload<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, TransferWrappedWithPayload<'info>>,
	batch_id: u32,
	amount: u64,
	recipient_address: [u8; 32],
	recipient_chain: u16,
	payload: Vec<u8>,
	cpi_program_id: &Pubkey,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new_readonly(ctx.accounts.config.key(), false),
			AccountMeta::new(ctx.accounts.from.key(), false),
			AccountMeta::new_readonly(ctx.accounts.from_owner.key(), true),
			AccountMeta::new(ctx.accounts.wrapped_mint.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wrapped_metadata.key(), false),
			AccountMeta::new_readonly(ctx.accounts.authority_signer.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_bridge.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_message.key(), true),
			AccountMeta::new_readonly(ctx.accounts.wormhole_emitter.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_sequence.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_fee_collector.key(), false),
			AccountMeta::new_readonly(solana_program::sysvar::clock::id(), false),
			AccountMeta::new_readonly(ctx.accounts.sender.key(), true),
			AccountMeta::new_readonly(solana_program::sysvar::rent::id(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wormhole_program.key(), false),
			AccountMeta::new_readonly(anchor_spl::token::spl_token::id(), false),
		],
		data: Instruction::TransferWrappedWithPayload {
			batch_id,
			amount,
			recipient_address,
			recipient_chain,
			payload,
			cpi_program_id: Some(*cpi_program_id),
		}
		.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}

#[derive(Accounts)]
pub struct CompleteTransferWrappedWithPayload<'info> {
	pub payer: AccountInfo<'info>,
	pub config: AccountInfo<'info>,
	pub vaa: AccountInfo<'info>,
	pub claim: AccountInfo<'info>,
	pub foreign_endpoint: AccountInfo<'info>,
	pub to: AccountInfo<'info>,
	pub redeemer: AccountInfo<'info>,
	pub wrapped_mint: AccountInfo<'info>,
	pub wrapped_metadata: AccountInfo<'info>,
	pub mint_authority: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
	pub token_program: AccountInfo<'info>,
	pub wormhole_program: AccountInfo<'info>,
}

pub fn complete_transfer_wrapped_with_payload<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, CompleteTransferWrappedWithPayload<'info>>,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new_readonly(ctx.accounts.config.key(), false),
			AccountMeta::new_readonly(ctx.accounts.vaa.key(), false),
			AccountMeta::new(ctx.accounts.claim.key(), false),
			AccountMeta::new_readonly(ctx.accounts.foreign_endpoint.key(), false),
			AccountMeta::new(ctx.accounts.to.key(), false),
			AccountMeta::new_readonly(ctx.accounts.redeemer.key(), true),
			AccountMeta::new(ctx.accounts.to.key(), false), // to_fees, lol
			AccountMeta::new(ctx.accounts.wrapped_mint.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wrapped_metadata.key(), false),
			AccountMeta::new_readonly(ctx.accounts.mint_authority.key(), false),
			AccountMeta::new_readonly(solana_program::sysvar::rent::id(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wormhole_program.key(), false),
			AccountMeta::new_readonly(anchor_spl::token::spl_token::id(), false),
		],
		data: Instruction::CompleteWrappedWithPayload {}.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}

#[derive(Accounts)]
pub struct TransferWrapped<'info> {
	pub payer: AccountInfo<'info>,
	pub config: AccountInfo<'info>,
	pub from: AccountInfo<'info>,
	pub from_owner: AccountInfo<'info>,
	pub wrapped_mint: AccountInfo<'info>,
	pub wrapped_metadata: AccountInfo<'info>,
	pub authority_signer: AccountInfo<'info>,
	pub wormhole_bridge: AccountInfo<'info>,
	pub wormhole_message: AccountInfo<'info>,
	pub wormhole_emitter: AccountInfo<'info>,
	pub wormhole_sequence: AccountInfo<'info>,
	pub wormhole_fee_collector: AccountInfo<'info>,
	pub clock: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
	pub token_program: AccountInfo<'info>,
	pub wormhole_program: AccountInfo<'info>,
}

pub fn transfer_wrapped<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, TransferWrapped<'info>>,
	batch_id: u32,
	amount: u64,
	fee: u64,
	recipient_address: [u8; 32],
	recipient_chain: u16,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new_readonly(ctx.accounts.config.key(), false),
			AccountMeta::new(ctx.accounts.from.key(), false),
			AccountMeta::new_readonly(ctx.accounts.from_owner.key(), true),
			AccountMeta::new(ctx.accounts.wrapped_mint.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wrapped_metadata.key(), false),
			AccountMeta::new_readonly(ctx.accounts.authority_signer.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_bridge.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_message.key(), true),
			AccountMeta::new_readonly(ctx.accounts.wormhole_emitter.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_sequence.key(), false),
			AccountMeta::new(ctx.accounts.wormhole_fee_collector.key(), false),
			AccountMeta::new_readonly(solana_program::sysvar::clock::id(), false),
			AccountMeta::new_readonly(solana_program::sysvar::rent::id(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.wormhole_program.key(), false),
			AccountMeta::new_readonly(anchor_spl::token::spl_token::id(), false),
		],
		data: Instruction::TransferWrapped {
			batch_id,
			amount,
			fee,
			recipient_address,
			recipient_chain,
		}
		.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}
