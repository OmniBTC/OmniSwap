use anchor_lang::prelude::*;

use crate::context::Initialize;
use crate::error::SoSwapError;

pub fn handler(
    ctx: Context<Initialize>,
    actual_reserve: u64,
    estimate_reserve: u64,
) -> Result<()> {
    // Initialize program's sender config
    let sender_config = &mut ctx.accounts.sender_config;

    // Set the owner of the sender config (effectively the owner of the
    // program).
    sender_config.owner = ctx.accounts.owner.key();
    sender_config.actual_reserve = actual_reserve;
    sender_config.estimate_reserve = estimate_reserve;
    sender_config.bump = *ctx
        .bumps
        .get("sender_config")
        .ok_or(SoSwapError::BumpNotFound)?;

    // Set Token Bridge related addresses.
    {
        let token_bridge = &mut sender_config.token_bridge;
        token_bridge.config = ctx.accounts.token_bridge_config.key();
        token_bridge.authority_signer = ctx.accounts.token_bridge_authority_signer.key();
        token_bridge.custody_signer = ctx.accounts.token_bridge_custody_signer.key();
        token_bridge.emitter = ctx.accounts.token_bridge_emitter.key();
        token_bridge.sequence = ctx.accounts.token_bridge_sequence.key();
        token_bridge.wormhole_bridge = ctx.accounts.wormhole_bridge.key();
        token_bridge.wormhole_fee_collector = ctx.accounts.wormhole_fee_collector.key();
    }

    // Initialize program's redeemer config
    let redeemer_config = &mut ctx.accounts.redeemer_config;

    // Set the owner of the redeemer config (effectively the owner of the
    // program).
    redeemer_config.owner = ctx.accounts.owner.key();
    redeemer_config.bump = *ctx
        .bumps
        .get("redeemer_config")
        .ok_or(SoSwapError::BumpNotFound)?;

    // Set Token Bridge related addresses.
    {
        let token_bridge = &mut redeemer_config.token_bridge;
        token_bridge.config = ctx.accounts.token_bridge_config.key();
        token_bridge.custody_signer = ctx.accounts.token_bridge_custody_signer.key();
        token_bridge.mint_authority = ctx.accounts.token_bridge_mint_authority.key();
    }

    // Done.
    Ok(())
}