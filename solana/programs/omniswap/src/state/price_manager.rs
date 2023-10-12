use anchor_lang::prelude::*;

#[account]
#[derive(Default)]
pub struct PriceManager {
	/// Who can update current_price_ratio
	pub owner: Pubkey,
	/// The currnet price ratio of native coins
	pub current_price_ratio: u64,
	// Last update timestamp for price ratio
	pub last_update_timestamp: u64,
}

impl PriceManager {
	pub const MAXIMUM_SIZE: usize = 8 // discriminator
        + 32 // price_manager
        + 8 // current_price_ratio
        + 8 // last_update_timestamp
    ;
	/// AKA `b"price_manager"`.
	pub const SEED_PREFIX: &'static [u8; 13] = b"price_manager";
}

#[cfg(test)]
pub mod test {
	use super::*;
	use std::mem::size_of;

	#[test]
	fn test_config() -> Result<()> {
		assert_eq!(
			PriceManager::MAXIMUM_SIZE,
			size_of::<u64>() + size_of::<Pubkey>() + size_of::<u64>() + size_of::<u64>()
		);

		Ok(())
	}
}
