use anchor_lang::prelude::*;
use std::io;

pub const PAYLOAD_ID_TRANSFER: u8 = 1;
pub const PAYLOAD_ID_ASSET_META: u8 = 2;
pub const PAYLOAD_ID_TRANSFER_WITH_PAYLOAD: u8 = 3;

#[derive(Default, AnchorSerialize, Clone, Copy, PartialEq, Eq)]
pub struct TransferWithMeta {
	/// Amount being transferred (big-endian uint256 -> u64)
	pub amount: u64,
	/// Address of the token. Left-zero-padded if shorter than 32 bytes
	pub token_address: [u8; 32],
	/// Chain ID of the token
	pub token_chain: u16,
	/// Address of the recipient. Left-zero-padded if shorter than 32 bytes
	pub to_address: [u8; 32],
	/// Chain ID of the recipient
	pub to_chain: u16,
	/// Sender of the transaction
	pub from_address: [u8; 32],
}

impl AnchorDeserialize for TransferWithMeta {
	fn deserialize(buf: &mut &[u8]) -> io::Result<Self> {
		// Verify Payload ID is a token transfer with payload.
		if buf[0] != PAYLOAD_ID_TRANSFER_WITH_PAYLOAD {
			return Err(io::Error::new(
				io::ErrorKind::InvalidInput,
				"Invalid Token Bridge Transfer With Payload",
			))
		}

		// Encoded amount should be the last 8 bytes of bytes 1 through 33,
		// otherwise we will have serious issues in the Token Bridge program.
		let amount = {
			let mut out = [0u8; 8];
			out.copy_from_slice(&buf[25..33]);
			u64::from_be_bytes(out)
		};

		let mut token_address = [0u8; 32];
		token_address.copy_from_slice(&buf[33..65]);

		let token_chain = to_u16_be(&buf[65..67]);

		let mut to_address = [0u8; 32];
		to_address.copy_from_slice(&buf[67..99]);

		let to_chain = to_u16_be(&buf[99..101]);

		let mut from_address = [0u8; 32];
		from_address.copy_from_slice(&buf[101..133]);

		Ok(TransferWithMeta {
			amount,
			token_address,
			token_chain,
			to_address,
			to_chain,
			from_address,
		})
	}
}

fn to_u16_be(buf: &[u8]) -> u16 {
	let mut out = [0u8; 2];
	out.copy_from_slice(buf);
	u16::from_be_bytes(out)
}
