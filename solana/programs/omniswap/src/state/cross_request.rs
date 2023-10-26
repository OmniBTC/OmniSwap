use crate::cross::NormalizedSoData;
use anchor_lang::prelude::*;

#[account]
#[derive(Default)]
pub struct CrossRequest {
	/// The SenderConfig address.
	pub owner: Pubkey,
	/// The requester.
	pub payer: Pubkey,
	/// The SenderConfig nonce.
	pub nonce: u64,
	/// The cross data.
	pub so_data: Vec<u8>,
	pub swap_data_src: Vec<u8>,
	pub wormhole_data: Vec<u8>,
	pub swap_data_dst: Vec<u8>,
}

impl CrossRequest {
	pub const MINIMUM_SIZE: usize = 8 // discriminator
		+ 32 // owner
		+ 32 // bump
		+ 8  // nonce
		+ 24 // empty vec
		+ 24 // empty vec
		+ 24 // empty vec
		+ 24; // empty vec

	pub const SEED_PREFIX: &'static [u8; 7] = b"request";
	pub fn dst_chain_id(&self) -> Result<u16> {
		let so_data = NormalizedSoData::decode_normalized_so_data(&self.so_data)?;

		Ok(so_data.destination_chain_id)
	}
}

#[cfg(test)]
pub mod test {
	use super::*;
	use std::mem::size_of;

	#[test]
	fn test_request() -> Result<()> {
		assert_eq!(
			CrossRequest::MINIMUM_SIZE,
			size_of::<u64>() +
				size_of::<Pubkey>() +
				size_of::<Pubkey>() +
				size_of::<u64>() + size_of::<Vec<u8>>() +
				size_of::<Vec<u8>>() +
				size_of::<Vec<u8>>() +
				size_of::<Vec<u8>>()
		);

		Ok(())
	}
}
