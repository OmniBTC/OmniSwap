use anchor_lang::prelude::*;

#[account]
#[derive(Default)]
/// The so fee of cross token
pub struct SoFeeConfig {
	/// Program's owner.
	pub owner: Pubkey,
	/// The recipient of [relayer_fee + so_fee].
	pub beneficiary: Pubkey,
	/// SoFee by RAY
	pub so_fee: u64,
	/// Actual relayer fee scale factor
	pub actual_reserve: u64,
	/// Estimate relayer fee scale factor
	pub estimate_reserve: u64,
}

impl SoFeeConfig {
	pub const MAXIMUM_SIZE: usize = 8 // discriminator
		+ 32 // owner
        + 32 // beneficiary
        + 8 // so_fee
		+ 8 // actual_reserve
		+ 8 // estimate_reserve
    ;
	/// AKA `b"so_fee"`.
	pub const SEED_PREFIX: &'static [u8; 6] = b"so_fee";
}

#[cfg(test)]
pub mod test {
	use super::*;
	use std::mem::size_of;

	#[test]
	fn test_config() -> Result<()> {
		assert_eq!(
			SoFeeConfig::MAXIMUM_SIZE,
			size_of::<u64>() +
				size_of::<Pubkey>() +
				size_of::<Pubkey>() +
				size_of::<u64>() + size_of::<u64>() +
				size_of::<u64>()
		);

		Ok(())
	}
}
