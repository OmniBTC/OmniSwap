use anchor_lang::prelude::*;
use wormhole_anchor_sdk::token_bridge;

#[derive(Default, AnchorSerialize, AnchorDeserialize, Copy, Clone, PartialEq, Eq)]
pub struct InboundTokenBridgeAddresses {
    // program pdas
    pub config: Pubkey,
    pub custody_signer: Pubkey,
    pub mint_authority: Pubkey,
}

impl InboundTokenBridgeAddresses {
    pub const LEN: usize =
          32 // config
        + 32 // custody_signer
        + 32 // mint_authority
    ;
}

#[account]
#[derive(Default)]
pub struct RedeemerConfig {
    /// Program's owner.
    pub owner: Pubkey,
    /// PDA bump.
    pub bump: u8,
    /// Token Bridge program's relevant addresses.
    pub token_bridge: InboundTokenBridgeAddresses,

    /// Relayer Fee
    pub relayer_fee: u32,
    pub relayer_fee_precision: u32,
}

impl RedeemerConfig {
    pub const MAXIMUM_SIZE: usize = 8 // discriminator
        + 32 // owner
        + 1 // bump
        + InboundTokenBridgeAddresses::LEN
        + 4 // relayer_fee
        + 4 // relayer_fee_precision
        ;

    /// AKA `b"redeemer"`.
    pub const SEED_PREFIX: &'static [u8; 8] = token_bridge::SEED_PREFIX_REDEEMER;

    pub fn compute_relayer_amount(&self, amount: u64) -> u64 {
        (amount * self.relayer_fee as u64) / self.relayer_fee_precision as u64
    }
}

#[cfg(test)]
pub mod test {
    use super::*;
    use std::mem::size_of;

    #[test]
    fn test_config() -> Result<()> {
        assert_eq!(
            InboundTokenBridgeAddresses::LEN,
            size_of::<InboundTokenBridgeAddresses>()
        );
        assert_eq!(
            RedeemerConfig::MAXIMUM_SIZE,
            size_of::<u64>()
                + size_of::<Pubkey>()
                + size_of::<u8>()
                + size_of::<InboundTokenBridgeAddresses>()
                + size_of::<u32>()
                + size_of::<u32>()
        );

        Ok(())
    }
}
