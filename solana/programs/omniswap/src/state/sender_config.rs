use anchor_lang::prelude::*;
use wormhole_anchor_sdk::token_bridge;

#[derive(Default, AnchorSerialize, AnchorDeserialize, Copy, Clone, PartialEq, Eq)]
pub struct OutboundTokenBridgeAddresses {
    // program pdas
    pub config: Pubkey,
    pub authority_signer: Pubkey,
    pub custody_signer: Pubkey,
    pub emitter: Pubkey,
    pub sequence: Pubkey,
    /// [BridgeData](wormhole_anchor_sdk::wormhole::BridgeData) address.
    pub wormhole_bridge: Pubkey,
    /// [FeeCollector](wormhole_anchor_sdk::wormhole::FeeCollector) address.
    pub wormhole_fee_collector: Pubkey,
}

impl OutboundTokenBridgeAddresses {
    pub const LEN: usize =
          32 // config
        + 32 // authority_signer
        + 32 // custody_signer
        + 32 // token_bridge_emitter
        + 32 // token_bridge_sequence
        + 32 // wormhole_bridge
        + 32 // wormhole_fee_collector
    ;
}

#[account]
#[derive(Default)]
pub struct SenderConfig {
    /// Program's owner.
    pub owner: Pubkey,
    /// PDA bump.
    pub bump: u8,
    /// Token Bridge program's relevant addresses.
    pub token_bridge: OutboundTokenBridgeAddresses,

    /// AKA consistency level. u8 representation of Solana's
    /// [Finality](wormhole_anchor_sdk::wormhole::Finality).
    pub finality: u8,
}

impl SenderConfig {
    pub const MAXIMUM_SIZE: usize = 8 // discriminator
        + 32 // owner
        + 1 // bump
        + OutboundTokenBridgeAddresses::LEN
        + 1 // finality
        
    ;
    /// AKA `b"sender"`.
    pub const SEED_PREFIX: &'static [u8; 6] = token_bridge::SEED_PREFIX_SENDER;
}

#[cfg(test)]
pub mod test {
    use super::*;
    use std::mem::size_of;

    #[test]
    fn test_config() -> Result<()> {
        assert_eq!(
            OutboundTokenBridgeAddresses::LEN,
            size_of::<OutboundTokenBridgeAddresses>()
        );
        assert_eq!(SenderConfig::MAXIMUM_SIZE,
            size_of::<u64>()
            + size_of::<Pubkey>()
            + size_of::<u8>()
            + size_of::<OutboundTokenBridgeAddresses>()
            + size_of::<u8>());

        Ok(())
    }
}