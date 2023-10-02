use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token::{Mint, Token, TokenAccount},
};
use wormhole_anchor_sdk::{token_bridge, wormhole};

use super::{
    state::{ForeignContract, RedeemerConfig, SenderConfig},
    HelloTokenError, PostedHelloTokenMessage,
};

/// AKA `b"bridged"`.
pub const SEED_PREFIX_BRIDGED: &[u8; 7] = b"bridged";
/// AKA `b"tmp"`.
pub const SEED_PREFIX_TMP: &[u8; 3] = b"tmp";

#[derive(Accounts)]
/// Context used to initialize program data (i.e. configs).
pub struct Initialize<'info> {
    #[account(mut)]
    /// Whoever initializes the config will be the owner of the program. Signer
    /// for creating the [`SenderConfig`] and [`RedeemerConfig`] accounts.
    pub owner: Signer<'info>,

    #[account(
        init,
        payer = owner,
        seeds = [SenderConfig::SEED_PREFIX],
        bump,
        space = SenderConfig::MAXIMUM_SIZE,
    )]
    /// Sender Config account, which saves program data useful for other
    /// instructions, specifically for outbound transfers. Also saves the payer
    /// of the [`initialize`](crate::initialize) instruction as the program's
    /// owner.
    pub sender_config: Box<Account<'info, SenderConfig>>,

    #[account(
        init,
        payer = owner,
        seeds = [RedeemerConfig::SEED_PREFIX],
        bump,
        space = RedeemerConfig::MAXIMUM_SIZE,
    )]
    /// Redeemer Config account, which saves program data useful for other
    /// instructions, specifically for inbound transfers. Also saves the payer
    /// of the [`initialize`](crate::initialize) instruction as the program's
    /// owner.
    pub redeemer_config: Box<Account<'info, RedeemerConfig>>,

    /// Wormhole program.
    pub wormhole_program: Program<'info, wormhole::program::Wormhole>,

    /// Token Bridge program.
    pub token_bridge_program: Program<'info, token_bridge::program::TokenBridge>,

    #[account(
        seeds = [token_bridge::Config::SEED_PREFIX],
        bump,
        seeds::program = token_bridge_program,
    )]
    /// Token Bridge config. Token Bridge program needs this account to
    /// invoke the Wormhole program to post messages. Even though it is a
    /// required account for redeeming token transfers, it is not actually
    /// used for completing these transfers.
    pub token_bridge_config: Account<'info, token_bridge::Config>,

    #[account(
        seeds = [token_bridge::SEED_PREFIX_AUTHORITY_SIGNER],
        bump,
        seeds::program = token_bridge_program,
    )]
    /// CHECK: Token Bridge authority signer. This isn't an account that holds
    /// data; it is purely just a signer for SPL tranfers when it is delegated
    /// spending approval for the SPL token.
    pub token_bridge_authority_signer: UncheckedAccount<'info>,

    #[account(
        seeds = [token_bridge::SEED_PREFIX_CUSTODY_SIGNER],
        bump,
        seeds::program = token_bridge_program,
    )]
    /// CHECK: Token Bridge custody signer. This isn't an account that holds
    /// data; it is purely just a signer for Token Bridge SPL tranfers.
    pub token_bridge_custody_signer: UncheckedAccount<'info>,

    #[account(
        seeds = [token_bridge::SEED_PREFIX_MINT_AUTHORITY],
        bump,
        seeds::program = token_bridge_program,
    )]
    /// CHECK: Token Bridge mint authority. This isn't an account that holds
    /// data; it is purely just a signer (SPL mint authority) for Token Bridge
    /// wrapped assets.
    pub token_bridge_mint_authority: UncheckedAccount<'info>,

    #[account(
        seeds = [wormhole::BridgeData::SEED_PREFIX],
        bump,
        seeds::program = wormhole_program,
    )]
    /// Wormhole bridge data account (a.k.a. its config).
    pub wormhole_bridge: Box<Account<'info, wormhole::BridgeData>>,

    #[account(
        seeds = [token_bridge::SEED_PREFIX_EMITTER],
        bump,
        seeds::program = token_bridge_program
    )]
    /// CHECK: Token Bridge program's emitter account. This isn't an account
    /// that holds data; it is purely just a signer for posting Wormhole
    /// messages on behalf of the Token Bridge program.
    pub token_bridge_emitter: UncheckedAccount<'info>,

    #[account(
        seeds = [wormhole::FeeCollector::SEED_PREFIX],
        bump,
        seeds::program = wormhole_program
    )]
    /// Wormhole fee collector account, which requires lamports before the
    /// program can post a message (if there is a fee). Token Bridge program
    /// handles the fee payments.
    pub wormhole_fee_collector: Account<'info, wormhole::FeeCollector>,

    #[account(
        seeds = [
            wormhole::SequenceTracker::SEED_PREFIX,
            token_bridge_emitter.key().as_ref()
        ],
        bump,
        seeds::program = wormhole_program
    )]
    /// Token Bridge emitter's sequence account. Like with all Wormhole
    /// emitters, this account keeps track of the sequence number of the last
    /// posted message.
    pub token_bridge_sequence: Account<'info, wormhole::SequenceTracker>,

    /// System program.
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(chain: u16)]
pub struct RegisterForeignContract<'info> {
    #[account(mut)]
    /// Owner of the program set in the [`SenderConfig`] account. Signer for
    /// creating [`ForeignContract`] account.
    pub owner: Signer<'info>,

    #[account(
        has_one = owner @ HelloTokenError::OwnerOnly,
        seeds = [SenderConfig::SEED_PREFIX],
        bump
    )]
    /// Sender Config account. This program requires that the `owner` specified
    /// in the context equals the pubkey specified in this account. Read-only.
    pub config: Box<Account<'info, SenderConfig>>,

    #[account(
        init_if_needed,
        payer = owner,
        seeds = [
            ForeignContract::SEED_PREFIX,
            &chain.to_le_bytes()[..]
        ],
        bump,
        space = ForeignContract::MAXIMUM_SIZE
    )]
    /// Foreign Contract account. Create this account if an emitter has not been
    /// registered yet for this Wormhole chain ID. If there already is a
    /// contract address saved in this account, overwrite it.
    pub foreign_contract: Box<Account<'info, ForeignContract>>,

    #[account(
        seeds = [
            &chain.to_be_bytes(),
            token_bridge_foreign_endpoint.emitter_address.as_ref()
        ],
        bump,
        seeds::program = token_bridge_program
    )]
    /// Token Bridge foreign endpoint. This account should really be one
    /// endpoint per chain, but Token Bridge's PDA allows for multiple
    /// endpoints for each chain. We store the proper endpoint for the
    /// emitter chain.
    pub token_bridge_foreign_endpoint: Account<'info, token_bridge::EndpointRegistration>,

    /// Token Bridge program.
    pub token_bridge_program: Program<'info, token_bridge::program::TokenBridge>,

    /// System program.
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateRelayerFee<'info> {
    #[account(mut)]
    /// CHECK: Owner of the program set in the [`RedeemerConfig`] account.
    pub owner: UncheckedAccount<'info>,

    #[account(
        mut,
        has_one = owner @ HelloTokenError::OwnerOnly,
        seeds = [RedeemerConfig::SEED_PREFIX],
        bump
    )]
    /// Redeemer Config account. This program requires that the `owner`
    /// specified in the context equals the pubkey specified in this account.
    /// Mutable.
    pub config: Box<Account<'info, RedeemerConfig>>,

    /// System program.
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(
    batch_id: u32,
    amount: u64,
    recipient_address: [u8; 32],
    recipient_chain: u16,
)]
pub struct SendNativeTokensWithPayload<'info> {
    /// Payer will pay Wormhole fee to transfer tokens and create temporary
    /// token account.
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        seeds = [SenderConfig::SEED_PREFIX],
        bump
    )]
    /// Sender Config account. Acts as the signer for the Token Bridge token
    /// transfer. Read-only.
    pub config: Box<Account<'info, SenderConfig>>,

    #[account(
        seeds = [
            ForeignContract::SEED_PREFIX,
            &recipient_chain.to_le_bytes()[..]
        ],
        bump,
    )]
    /// Foreign Contract account. Send tokens to the contract specified in this
    /// account. Funnily enough, the Token Bridge program does not have any
    /// requirements for outbound transfers for the recipient chain to be
    /// registered. This account provides extra protection against sending
    /// tokens to an unregistered Wormhole chain ID. Read-only.
    pub foreign_contract: Box<Account<'info, ForeignContract>>,

    #[account(mut)]
    /// Mint info. This is the SPL token that will be bridged over to the
    /// foreign contract. Mutable.
    pub mint: Box<Account<'info, Mint>>,

    #[account(
        mut,
        associated_token::mint = mint,
        associated_token::authority = payer,
    )]
    /// Payer's associated token account. We may want to make this a generic
    /// token account in the future.
    pub from_token_account: Account<'info, TokenAccount>,

    #[account(
        init,
        payer = payer,
        seeds = [
            SEED_PREFIX_TMP,
            mint.key().as_ref(),
        ],
        bump,
        token::mint = mint,
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
        address = config.token_bridge.config @ HelloTokenError::InvalidTokenBridgeConfig
    )]
    /// Token Bridge config. Read-only.
    pub token_bridge_config: Account<'info, token_bridge::Config>,

    #[account(
        mut,
        seeds = [mint.key().as_ref()],
        bump,
        seeds::program = token_bridge_program
    )]
    /// CHECK: Token Bridge custody. This is the Token Bridge program's token
    /// account that holds this mint's balance. This account needs to be
    /// unchecked because a token account may not have been created for this
    /// mint yet. Mutable.
    pub token_bridge_custody: UncheckedAccount<'info>,

    #[account(
        address = config.token_bridge.authority_signer @ HelloTokenError::InvalidTokenBridgeAuthoritySigner
    )]
    /// CHECK: Token Bridge authority signer. Read-only.
    pub token_bridge_authority_signer: UncheckedAccount<'info>,

    #[account(
        address = config.token_bridge.custody_signer @ HelloTokenError::InvalidTokenBridgeCustodySigner
    )]
    /// CHECK: Token Bridge custody signer. Read-only.
    pub token_bridge_custody_signer: UncheckedAccount<'info>,

    #[account(
        mut,
        address = config.token_bridge.wormhole_bridge @ HelloTokenError::InvalidWormholeBridge,
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
        address = config.token_bridge.emitter @ HelloTokenError::InvalidTokenBridgeEmitter
    )]
    /// CHECK: Token Bridge emitter. Read-only.
    pub token_bridge_emitter: UncheckedAccount<'info>,

    #[account(
        mut,
        address = config.token_bridge.sequence @ HelloTokenError::InvalidTokenBridgeSequence
    )]
    /// CHECK: Token Bridge sequence. Mutable.
    pub token_bridge_sequence: Account<'info, wormhole::SequenceTracker>,

    #[account(
        mut,
        address = config.token_bridge.wormhole_fee_collector @ HelloTokenError::InvalidWormholeFeeCollector
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

#[derive(Accounts)]
#[instruction(vaa_hash: [u8; 32])]
pub struct RedeemNativeTransferWithPayload<'info> {
    #[account(mut)]
    /// Payer will pay Wormhole fee to transfer tokens and create temporary
    /// token account.
    pub payer: Signer<'info>,

    #[account(
        mut,
        constraint = payer.key() == recipient.key() || payer_token_account.key() == anchor_spl::associated_token::get_associated_token_address(&payer.key(), &mint.key()) @ HelloTokenError::InvalidPayerAta
    )]
    /// CHECK: Payer's token account. If payer != recipient, must be an
    /// associated token account. Mutable.
    pub payer_token_account: UncheckedAccount<'info>,

    #[account(
        seeds = [RedeemerConfig::SEED_PREFIX],
        bump
    )]
    /// Redeemer Config account. Acts as the Token Bridge redeemer, which signs
    /// for the complete transfer instruction. Read-only.
    pub config: Box<Account<'info, RedeemerConfig>>,

    #[account(
        seeds = [
            ForeignContract::SEED_PREFIX,
            &vaa.emitter_chain().to_le_bytes()[..]
        ],
        bump,
        constraint = foreign_contract.verify(&vaa) @ HelloTokenError::InvalidForeignContract
    )]
    /// Foreign Contract account. The registered contract specified in this
    /// account must agree with the target address for the Token Bridge's token
    /// transfer. Read-only.
    pub foreign_contract: Box<Account<'info, ForeignContract>>,

    #[account(
        address = vaa.data().mint()
    )]
    /// Mint info. This is the SPL token that will be bridged over from the
    /// foreign contract. This must match the token address specified in the
    /// signed Wormhole message. Read-only.
    pub mint: Account<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = mint,
        associated_token::authority = recipient
    )]
    /// Recipient associated token account.
    pub recipient_token_account: Box<Account<'info, TokenAccount>>,

    #[account(mut)]
    /// CHECK: Recipient may differ from payer if a relayer paid for this
    /// transaction.
    pub recipient: UncheckedAccount<'info>,

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
        address = config.token_bridge.config @ HelloTokenError::InvalidTokenBridgeConfig
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
        constraint = vaa.data().to() == crate::ID || vaa.data().to() == config.key() @ HelloTokenError::InvalidTransferToAddress,
        constraint = vaa.data().to_chain() == wormhole::CHAIN_ID_SOLANA @ HelloTokenError::InvalidTransferToChain,
        constraint = vaa.data().token_chain() == wormhole::CHAIN_ID_SOLANA @ HelloTokenError::InvalidTransferTokenChain
    )]
    /// Verified Wormhole message account. The Wormhole program verified
    /// signatures and posted the account data here. Read-only.
    pub vaa: Box<Account<'info, PostedHelloTokenMessage>>,

    #[account(mut)]
    /// CHECK: Token Bridge claim account. It stores a boolean, whose value
    /// is true if the bridged assets have been claimed. If the transfer has
    /// not been redeemed, this account will not exist yet.
    pub token_bridge_claim: UncheckedAccount<'info>,

    #[account(
        address = foreign_contract.token_bridge_foreign_endpoint @ HelloTokenError::InvalidTokenBridgeForeignEndpoint
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
        address = config.token_bridge.custody_signer @ HelloTokenError::InvalidTokenBridgeCustodySigner
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

#[derive(Accounts)]
#[instruction(
    batch_id: u32,
    amount: u64,
    recipient_address: [u8; 32],
    recipient_chain: u16,
)]
pub struct SendWrappedTokensWithPayload<'info> {
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
            &recipient_chain.to_le_bytes()[..]
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
        address = config.token_bridge.config @ HelloTokenError::InvalidTokenBridgeConfig
    )]
    /// Token Bridge config. Mutable.
    pub token_bridge_config: Account<'info, token_bridge::Config>,

    #[account(
        address = config.token_bridge.authority_signer @ HelloTokenError::InvalidTokenBridgeAuthoritySigner
    )]
    /// CHECK: Token Bridge authority signer. Read-only.
    pub token_bridge_authority_signer: UncheckedAccount<'info>,

    #[account(
        mut,
        address = config.token_bridge.wormhole_bridge @ HelloTokenError::InvalidWormholeBridge,
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
        address = config.token_bridge.emitter @ HelloTokenError::InvalidTokenBridgeEmitter
    )]
    /// CHECK: Token Bridge emitter. Read-only.
    pub token_bridge_emitter: UncheckedAccount<'info>,

    #[account(
        mut,
        address = config.token_bridge.sequence @ HelloTokenError::InvalidTokenBridgeSequence
    )]
    /// CHECK: Token Bridge sequence. Mutable.
    pub token_bridge_sequence: Account<'info, wormhole::SequenceTracker>,

    #[account(
        mut,
        address = config.token_bridge.wormhole_fee_collector @ HelloTokenError::InvalidWormholeFeeCollector
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

#[derive(Accounts)]
#[instruction(vaa_hash: [u8; 32])]
pub struct RedeemWrappedTransferWithPayload<'info> {
    #[account(mut)]
    /// Payer will pay Wormhole fee to transfer tokens and create temporary
    /// token account.
    pub payer: Signer<'info>,

    #[account(
        mut,
        constraint = payer.key() == recipient.key() || payer_token_account.key() == anchor_spl::associated_token::get_associated_token_address(&payer.key(), &token_bridge_wrapped_mint.key()) @ HelloTokenError::InvalidPayerAta
    )]
    /// CHECK: Payer's token account. If payer != recipient, must be an
    /// associated token account.
    pub payer_token_account: UncheckedAccount<'info>,

    #[account(
        seeds = [RedeemerConfig::SEED_PREFIX],
        bump
    )]
    /// Redeemer Config account. Acts as the Token Bridge redeemer, which signs
    /// for the complete transfer instruction. Read-only.
    pub config: Box<Account<'info, RedeemerConfig>>,

    #[account(
        seeds = [
            ForeignContract::SEED_PREFIX,
            &vaa.emitter_chain().to_le_bytes()[..]
        ],
        bump,
        constraint = foreign_contract.verify(&vaa) @ HelloTokenError::InvalidForeignContract
    )]
    /// Foreign Contract account. The registered contract specified in this
    /// account must agree with the target address for the Token Bridge's token
    /// transfer. Read-only.
    pub foreign_contract: Box<Account<'info, ForeignContract>>,

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

    #[account(
        mut,
        associated_token::mint = token_bridge_wrapped_mint,
        associated_token::authority = recipient
    )]
    /// Recipient associated token account.
    pub recipient_token_account: Box<Account<'info, TokenAccount>>,

    #[account(mut)]
    /// CHECK: recipient may differ from payer if a relayer paid for this
    /// transaction.
    pub recipient: UncheckedAccount<'info>,

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
        address = config.token_bridge.config @ HelloTokenError::InvalidTokenBridgeConfig
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
        constraint = vaa.data().to() == crate::ID || vaa.data().to() == config.key() @ HelloTokenError::InvalidTransferToAddress,
        constraint = vaa.data().to_chain() == wormhole::CHAIN_ID_SOLANA @ HelloTokenError::InvalidTransferToChain,
        constraint = vaa.data().token_chain() != wormhole::CHAIN_ID_SOLANA @ HelloTokenError::InvalidTransferTokenChain
    )]
    /// Verified Wormhole message account. The Wormhole program verified
    /// signatures and posted the account data here. Read-only.
    pub vaa: Box<Account<'info, PostedHelloTokenMessage>>,

    #[account(mut)]
    /// CHECK: Token Bridge claim account. It stores a boolean, whose value
    /// is true if the bridged assets have been claimed. If the transfer has
    /// not been redeemed, this account will not exist yet.
    pub token_bridge_claim: UncheckedAccount<'info>,

    #[account(
        address = foreign_contract.token_bridge_foreign_endpoint @ HelloTokenError::InvalidTokenBridgeForeignEndpoint
    )]
    /// Token Bridge foreign endpoint. This account should really be one
    /// endpoint per chain, but the PDA allows for multiple endpoints for each
    /// chain! We store the proper endpoint for the emitter chain.
    pub token_bridge_foreign_endpoint: Account<'info, token_bridge::EndpointRegistration>,

    #[account(
        address = config.token_bridge.mint_authority @ HelloTokenError::InvalidTokenBridgeMintAuthority
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
