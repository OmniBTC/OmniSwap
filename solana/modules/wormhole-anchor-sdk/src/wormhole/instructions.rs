use anchor_lang::{prelude::*, solana_program};

use super::Finality;

#[derive(AnchorDeserialize, AnchorSerialize)]
/// Wormhole instructions.
pub enum Instruction {
	Initialize, // placeholder
	PostMessage {
		batch_id: u32,
		payload: Vec<u8>,
		finality: Finality,
	},
	PostVAA {
		version: u8,
		guardian_set_index: u32,
		timestamp: u32,
		nonce: u32,
		emitter_chain: u16,
		emitter_address: [u8; 32],
		sequence: u64,
		consistency_level: u8,
		payload: Vec<u8>,
	},
	SetFees,            // placeholder (governance action)
	TransferFees,       // placeholder (governance action)
	UpgradeContract,    // placeholder (governance action)
	UpgradeGuardianSet, // placeholder (governance action)
	VerifySignatures {
		signers: [i8; 19],
	},
	PostMessageUnreliable, // placeholder (unused)
}

#[derive(Accounts)]
pub struct PostMessage<'info> {
	pub config: AccountInfo<'info>,
	pub message: AccountInfo<'info>,
	pub emitter: AccountInfo<'info>,
	pub sequence: AccountInfo<'info>,
	pub payer: AccountInfo<'info>,
	pub fee_collector: AccountInfo<'info>,
	pub clock: AccountInfo<'info>,
	pub rent: AccountInfo<'info>,
	pub system_program: AccountInfo<'info>,
}

pub fn post_message<'info>(
	ctx: CpiContext<'_, '_, '_, 'info, PostMessage<'info>>,
	batch_id: u32,
	payload: Vec<u8>,
	finality: Finality,
) -> Result<()> {
	let ix = solana_program::instruction::Instruction {
		program_id: ctx.program.key(),
		accounts: vec![
			AccountMeta::new(ctx.accounts.config.key(), false),
			AccountMeta::new(ctx.accounts.message.key(), true),
			AccountMeta::new_readonly(ctx.accounts.emitter.key(), true),
			AccountMeta::new(ctx.accounts.sequence.key(), false),
			AccountMeta::new(ctx.accounts.payer.key(), true),
			AccountMeta::new(ctx.accounts.fee_collector.key(), false),
			AccountMeta::new_readonly(ctx.accounts.clock.key(), false),
			AccountMeta::new_readonly(ctx.accounts.system_program.key(), false),
			AccountMeta::new_readonly(ctx.accounts.rent.key(), false),
		],
		data: Instruction::PostMessage { batch_id, payload, finality }.try_to_vec()?,
	};

	solana_program::program::invoke_signed(
		&ix,
		&ToAccountInfos::to_account_infos(&ctx),
		ctx.signer_seeds,
	)
	.map_err(Into::into)
}
