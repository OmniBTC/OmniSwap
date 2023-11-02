use crate::{
	cross::{NormalizedSoData, NormalizedSwapData},
	serde, SoSwapError,
};
use anchor_lang::{AnchorDeserialize, AnchorSerialize};
use spl_math::uint::U256;
use std::io;
use wormhole_anchor_sdk::token_bridge;

#[derive(PartialEq, Eq, Debug, Clone, Default)]
pub struct SoSwapMessage {
	pub(crate) dst_max_gas_price: U256,
	pub(crate) dst_max_gas: U256,
	pub(crate) normalized_so_data: NormalizedSoData,
	pub(crate) normalized_swap_data: Vec<NormalizedSwapData>,
}

impl SoSwapMessage {
	pub fn decode_message(data: Vec<u8>) -> Result<Self, SoSwapError> {
		// CrossData
		// 1. dst_max_gas_price INTER_DELIMITER
		// 2. dst_max_gas INTER_DELIMITER
		// 3. transactionId(SoData) INTER_DELIMITER
		// 4. receiver(SoData) INTER_DELIMITER
		// 5. receivingAssetId(SoData) INTER_DELIMITER
		// 6. swapDataLength(u8) INTER_DELIMITER
		// 7. callTo(SwapData) INTER_DELIMITER
		// 8. sendingAssetId(SwapData) INTER_DELIMITER
		// 9. receivingAssetId(SwapData) INTER_DELIMITER
		// 10. callData(SwapData)

		let data_len = data.len();

		let mut index = 0;
		let mut next_len;

		next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
		index += 1;
		let dst_max_gas_price =
			serde::deserialize_u256_with_hex_str(&data[index..index + next_len])?;
		index += next_len;

		next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
		index += 1;
		let dst_max_gas = serde::deserialize_u256_with_hex_str(&data[index..index + next_len])?;
		index += next_len;

		// SoData
		next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
		index += 1;
		let so_transaction_id = data[index..index + next_len].to_vec();
		index += next_len;

		next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
		index += 1;
		let so_receiver = data[index..index + next_len].to_vec();
		index += next_len;

		next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
		index += 1;
		let so_receiving_asset_id = data[index..index + next_len].to_vec();
		index += next_len;
		let so_data = NormalizedSoData::padding_so_data(
			so_transaction_id,
			so_receiver,
			so_receiving_asset_id,
		);

		// Skip len
		if index < data_len {
			next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
			index += 1;
			index += next_len;
		};

		// Swap data
		let mut swap_data = Vec::<NormalizedSwapData>::new();

		while index < data_len {
			next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
			index += 1;
			let swap_call_to = data[index..index + next_len].to_vec();
			index += next_len;

			next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
			index += 1;
			let swap_sending_asset_id = data[index..index + next_len].to_vec();
			index += next_len;

			next_len = serde::deserialize_u8(&data[index..index + 1])? as usize;
			index += 1;
			let swap_receiving_asset_id = data[index..index + next_len].to_vec();
			index += next_len;

			next_len = serde::deserialize_u16(&data[index..index + 2])? as usize;
			index += 2;
			let swap_call_data = data[index..index + next_len].to_vec();
			index += next_len;

			swap_data.push(NormalizedSwapData::padding_swap_data(
				swap_call_to,
				swap_sending_asset_id,
				swap_receiving_asset_id,
				swap_call_data,
			));
		}

		Ok(Self {
			dst_max_gas_price,
			dst_max_gas,
			normalized_so_data: so_data,
			normalized_swap_data: swap_data,
		})
	}
}

impl AnchorSerialize for SoSwapMessage {
	fn serialize<W: io::Write>(&self, writer: &mut W) -> io::Result<()> {
		// CrossData
		// 1. dst_max_gas_price INTER_DELIMITER
		// 2. dst_max_gas INTER_DELIMITER
		// 3. transactionId(SoData) INTER_DELIMITER
		// 4. receiver(SoData) INTER_DELIMITER
		// 5. receivingAssetId(SoData) INTER_DELIMITER
		// 6. swapDataLength(u8) INTER_DELIMITER
		// 7. callTo(SwapData) INTER_DELIMITER
		// 8. sendingAssetId(SwapData) INTER_DELIMITER
		// 9. receivingAssetId(SwapData) INTER_DELIMITER
		// 10. callData(SwapData)

		let mut data = Vec::<u8>::new();

		let mut cache = Vec::<u8>::new();
		serde::serialize_u256_with_hex_str(&mut cache, self.dst_max_gas_price);
		serde::serialize_u8(&mut data, cache.len() as u8);
		data.append(&mut cache);

		let mut cache = Vec::<u8>::new();
		serde::serialize_u256_with_hex_str(&mut cache, self.dst_max_gas);
		serde::serialize_u8(&mut data, cache.len() as u8);
		data.append(&mut cache);

		let mut cache = self.normalized_so_data.transaction_id.clone();
		serde::serialize_u8(&mut data, cache.len() as u8);
		data.append(&mut cache);

		let mut cache = self.normalized_so_data.receiver.clone();
		serde::serialize_u8(&mut data, cache.len() as u8);
		data.append(&mut cache);

		let mut cache = self.normalized_so_data.receiving_asset_id.clone();
		serde::serialize_u8(&mut data, cache.len() as u8);
		data.append(&mut cache);

		let swap_len = self.normalized_swap_data.len();
		if swap_len > 0 {
			let mut cache = Vec::<u8>::new();
			serde::serialize_u256_with_hex_str(&mut cache, U256::from(swap_len));
			serde::serialize_u8(&mut data, cache.len() as u8);
			data.append(&mut cache);
		};

		for d in &self.normalized_swap_data {
			let mut cache = d.call_to.clone();
			serde::serialize_u8(&mut data, cache.len() as u8);
			data.append(&mut cache);

			let mut cache = d.sending_asset_id.clone();
			serde::serialize_u8(&mut data, cache.len() as u8);
			data.append(&mut cache);

			let mut cache = d.receiving_asset_id.clone();
			serde::serialize_u8(&mut data, cache.len() as u8);
			data.append(&mut cache);

			let mut cache = d.call_data.clone();
			serde::serialize_u16(&mut data, cache.len() as u16);
			data.append(&mut cache);
		}

		writer.write_all(data.as_mut_slice())
	}
}

impl AnchorDeserialize for SoSwapMessage {
	fn deserialize(buf: &mut &[u8]) -> io::Result<Self> {
		let so_swap_message = SoSwapMessage::decode_message(buf.to_vec()).unwrap_or_default();

		Ok(so_swap_message)
	}
}

pub type PostedSoSwapMessage = token_bridge::PostedTransferWith<SoSwapMessage>;

#[cfg(test)]
pub mod test {
	use super::*;
	use anchor_lang::prelude::Result;
	use hex_literal::hex;

	#[test]
	fn test_serde_soswap_message() -> Result<()> {
		let data = hex!("00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100").to_vec();
		let so_data = NormalizedSoData::decode_normalized_so_data(&data)?;
		let data = hex!("000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7").to_vec();
		let swap_data = NormalizedSwapData::decode_normalized_swap_data(&data)?;
		let dst_max_gas_price = U256::from(10000u32);
		let dst_max_gas = U256::from(59u32);

		// Not swap
		let so_swap_message_without_swap = SoSwapMessage {
			dst_max_gas_price,
			dst_max_gas,
			normalized_so_data: so_data.clone(),
			normalized_swap_data: vec![],
		};
		let mut encode_data = Vec::new();
		so_swap_message_without_swap.serialize(&mut encode_data)?;

		let data = hex!("022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c1719").to_vec();
		assert_eq!(data, encode_data);

		let msg_without_swap = SoSwapMessage::deserialize(&mut data.as_slice())?;
		assert_eq!(msg_without_swap.dst_max_gas_price, dst_max_gas_price);
		assert_eq!(msg_without_swap.dst_max_gas, dst_max_gas);
		assert_eq!(
			msg_without_swap.normalized_so_data,
			NormalizedSoData::padding_so_data(
				so_data.transaction_id.clone(),
				so_data.receiver.clone(),
				so_data.receiving_asset_id.clone()
			)
		);
		assert!(msg_without_swap.normalized_swap_data.is_empty());

		// With swap
		let so_swap_message_with_swap = SoSwapMessage {
			dst_max_gas_price,
			dst_max_gas,
			normalized_so_data: so_data.clone(),
			normalized_swap_data: swap_data,
		};
		let mut encode_data = Vec::new();
		so_swap_message_with_swap.serialize(&mut encode_data)?;

		let data = hex!("022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c17190102204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c811a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e163078313a3a6f6d6e695f6272696467653a3a5842544300583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c6174656414957eb0316f02ba4a9de3d308742eefd44a3c1719142514895c72f50d8bd4b4f9b1110f0d6bd2c9752614143db3ceefbdfe5631add3e50f7614b6ba708ba700146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7").to_vec();
		assert_eq!(data, encode_data);

		let msg_with_swap = SoSwapMessage::deserialize(&mut data.as_slice())?;

		let mut decode_swap_data = Vec::<NormalizedSwapData>::new();

		for s in &msg_with_swap.normalized_swap_data {
			decode_swap_data.push(NormalizedSwapData::padding_swap_data(
				s.call_to.clone(),
				s.sending_asset_id.clone(),
				s.receiving_asset_id.clone(),
				s.call_data.clone(),
			))
		}

		assert_eq!(msg_with_swap.dst_max_gas_price, dst_max_gas_price);
		assert_eq!(msg_with_swap.dst_max_gas, dst_max_gas);
		assert_eq!(
			msg_with_swap.normalized_so_data,
			NormalizedSoData::padding_so_data(
				so_data.transaction_id,
				so_data.receiver,
				so_data.receiving_asset_id
			)
		);
		assert_eq!(msg_with_swap.normalized_swap_data, decode_swap_data);

		Ok(())
	}
}
