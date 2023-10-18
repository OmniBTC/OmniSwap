use anchor_lang::{prelude::*, AnchorDeserialize, AnchorSerialize};
use spl_math::uint::U256;

use crate::{cross::NormalizedWormholeData, message::PostedSoSwapMessage};

#[account]
#[derive(Default)]
/// Foreign emitter account data.
pub struct ForeignContract {
	/// Emitter chain. Cannot equal `1` (Solana's Chain ID).
	pub chain: u16,
	/// Emitter address. Cannot be zero address.
	/// Left-zero-padded if shorter than 32 bytes
	pub address: [u8; 32],
	/// Token Bridge program's foreign endpoint account key.
	pub token_bridge_foreign_endpoint: Pubkey,
	/// Normalized target chain minimum consumption of gas
	pub normalized_dst_base_gas: [u8; 32],
	/// Normalized target chain gas per bytes
	pub normalized_dst_gas_per_bytes: [u8; 32],
}

impl ForeignContract {
	pub const MAXIMUM_SIZE: usize = 8 // discriminator
        + 2 // chain
        + 32 // address
        + 32 // token_bridge_foreign_endpoint
        + 32 // normalized_dst_base_gas
        + 32 // normalized_dst_gas_per_bytes
    ;
	/// AKA `b"foreign_contract"`.
	pub const SEED_PREFIX: &'static [u8; 16] = b"foreign_contract";

	/// Convenience method to check whether an address equals the one saved in
	/// this account.
	pub fn verify(&self, vaa: &PostedSoSwapMessage) -> bool {
		vaa.emitter_chain() == self.chain && *vaa.data().from_address() == self.address
	}

	pub fn estimate_complete_soswap_gas(
		&self,
		so_data: &Vec<u8>,
		wormhole_data: &NormalizedWormholeData,
		swap_data_dst: &Vec<u8>,
	) -> U256 {
		let len = 32 + 32 + 1 + so_data.len() + 1 + swap_data_dst.len();

		if wormhole_data.dst_wormhole_chain_id != self.chain {
			return U256::zero()
		}

		let dst_base_gas = U256::from_little_endian(&self.normalized_dst_base_gas);
		let dst_gas_per_bytes = U256::from_little_endian(&self.normalized_dst_gas_per_bytes);

		dst_base_gas
			.checked_add(dst_gas_per_bytes.checked_mul(U256::from(len)).unwrap())
			.unwrap_or_default()
	}
}

#[cfg(test)]
pub mod test {
	use super::*;

	use crate::{cross::NormalizedSoData, message::SoSwapMessage};
	use std::mem::size_of;
	use wormhole_anchor_sdk::{token_bridge, wormhole};

	#[test]
	fn test_foreign_emitter() -> Result<()> {
		assert_eq!(
			ForeignContract::MAXIMUM_SIZE,
			size_of::<u64>() +
				size_of::<u16>() + size_of::<[u8; 32]>() +
				size_of::<Pubkey>() +
				size_of::<[u8; 32]>() +
				size_of::<[u8; 32]>()
		);

		let chain: u16 = 2;
		let address = Pubkey::new_unique().to_bytes();
		let token_bridge_foreign_endpoint = Pubkey::new_unique();
		let normalized_dst_base_gas = Pubkey::new_unique().to_bytes();
		let normalized_dst_gas_per_bytes = Pubkey::new_unique().to_bytes();
		let foreign_contract = ForeignContract {
			chain,
			address,
			token_bridge_foreign_endpoint,
			normalized_dst_base_gas,
			normalized_dst_gas_per_bytes,
		};

		let vaa = PostedSoSwapMessage {
			meta: wormhole::PostedVaaMeta {
				version: 1,
				finality: 200,
				timestamp: 0,
				signature_set: Pubkey::new_unique(),
				posted_timestamp: 1,
				batch_id: 69,
				sequence: 420,
				emitter_chain: chain,
				emitter_address: Pubkey::new_unique().to_bytes(),
			},
			payload: (
				0,
				token_bridge::TransferWith::new(
					&token_bridge::TransferWithMeta {
						amount: 1,
						token_chain: 2,
						token_address: Pubkey::new_unique().to_bytes(),
						to_chain: chain,
						to_address: Pubkey::new_unique().to_bytes(),
						from_address: address,
					},
					&SoSwapMessage {
						dst_max_gas_price: Default::default(),
						dst_max_gas: Default::default(),
						normalized_so_data: NormalizedSoData {
							transaction_id: vec![],
							receiver: vec![],
							source_chain_id: 0,
							sending_asset_id: vec![],
							destination_chain_id: 0,
							receiving_asset_id: vec![],
							amount: Default::default(),
						},
						normalized_swap_data: vec![],
					},
				),
			),
		};
		assert!(foreign_contract.verify(&vaa), "foreign_contract.verify(&vaa) failed");

		Ok(())
	}
}
