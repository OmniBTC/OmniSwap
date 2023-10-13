use anchor_lang::prelude::*;
use std::{io, ops::Deref};

use crate::{
	token_bridge::{message::TransferWithMeta, program::ID},
	wormhole::{PostedVaa, CHAIN_ID_SOLANA},
};

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
/// Token Bridge config data.
pub struct Config {
	pub wormhole_bridge: Pubkey,
}

impl Config {
	/// AKA `b"config"`
	pub const SEED_PREFIX: &'static [u8; 6] = b"config";
}

impl AccountDeserialize for Config {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for Config {}

impl Owner for Config {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, Clone, PartialEq)]
/// Token Bridge wrapped mint. See [`anchor_spl::token::Mint`].
pub struct WrappedMint(anchor_spl::token::Mint);

impl WrappedMint {
	/// AKA `b"wrapped"`
	pub const SEED_PREFIX: &'static [u8; 7] = b"wrapped";
}

impl AccountDeserialize for WrappedMint {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Ok(Self(anchor_spl::token::Mint::try_deserialize_unchecked(buf)?))
	}
}

impl AccountSerialize for WrappedMint {}

impl Owner for WrappedMint {
	fn owner() -> Pubkey {
		anchor_spl::token::ID
	}
}

impl Deref for WrappedMint {
	type Target = anchor_spl::token::Mint;

	fn deref(&self) -> &Self::Target {
		&self.0
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
/// Token Bridge wrapped metadata (for native token data).
pub struct WrappedMeta {
	pub chain: u16,
	pub token_address: [u8; 32],
	pub original_decimals: u8,
}

impl WrappedMeta {
	/// AKA `b"meta"`
	pub const SEED_PREFIX: &'static [u8; 4] = b"meta";
}

impl AccountDeserialize for WrappedMeta {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for WrappedMeta {}

impl Owner for WrappedMeta {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
/// Token Bridge foreign endpoint registration data.
pub struct EndpointRegistration {
	pub emitter_chain: u16,
	pub emitter_address: [u8; 32],
}

impl AccountDeserialize for EndpointRegistration {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for EndpointRegistration {}

impl Owner for EndpointRegistration {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, Clone, PartialEq, Eq)]
/// Token Bridge Transfer With Payload data. This data is found as the payload
/// of a posted Wormhole message.
pub struct TransferWithPayload {
	meta: TransferWithMeta,
	payload: Vec<u8>,
}

impl TransferWithPayload {
	pub fn amount(&self) -> u64 {
		self.meta.amount
	}

	pub fn token_address(&self) -> &[u8; 32] {
		&self.meta.token_address
	}

	pub fn mint(&self) -> Pubkey {
		if self.token_chain() == CHAIN_ID_SOLANA {
			Pubkey::new_from_array(*self.token_address())
		} else {
			Pubkey::default()
		}
	}

	pub fn token_chain(&self) -> u16 {
		self.meta.token_chain
	}

	pub fn to_address(&self) -> &[u8; 32] {
		&self.meta.to_address
	}

	pub fn to(&self) -> Pubkey {
		Pubkey::new_from_array(*self.to_address())
	}

	pub fn to_chain(&self) -> u16 {
		self.meta.to_chain
	}

	pub fn from_address(&self) -> &[u8; 32] {
		&self.meta.from_address
	}

	pub fn data(&self) -> &[u8] {
		&self.payload
	}

	pub fn message(&self) -> &[u8] {
		self.data()
	}
}

impl AnchorDeserialize for TransferWithPayload {
	fn deserialize(buf: &mut &[u8]) -> io::Result<Self> {
		Ok(TransferWithPayload {
			meta: TransferWithMeta::deserialize(&mut &buf[..133])?,
			payload: buf[133..].to_vec(),
		})
	}
}

#[derive(Default, AnchorSerialize, Clone, PartialEq, Eq)]
/// Token Bridge Transfer with generic payload type `P`. This data is found as
/// the payload of a posted Wormhole message.
pub struct TransferWith<P> {
	meta: TransferWithMeta,
	payload: P,
}

impl<P: AnchorDeserialize + AnchorSerialize + Clone> TransferWith<P> {
	pub fn new(meta: &TransferWithMeta, payload: &P) -> Self {
		Self { meta: *meta, payload: payload.clone() }
	}

	pub fn amount(&self) -> u64 {
		self.meta.amount
	}

	pub fn token_address(&self) -> &[u8; 32] {
		&self.meta.token_address
	}

	pub fn mint(&self) -> Pubkey {
		if self.token_chain() == CHAIN_ID_SOLANA {
			Pubkey::new_from_array(*self.token_address())
		} else {
			Pubkey::default()
		}
	}

	pub fn token_chain(&self) -> u16 {
		self.meta.token_chain
	}

	pub fn to_address(&self) -> &[u8; 32] {
		&self.meta.to_address
	}

	pub fn to(&self) -> Pubkey {
		Pubkey::new_from_array(*self.to_address())
	}

	pub fn to_chain(&self) -> u16 {
		self.meta.to_chain
	}

	pub fn from_address(&self) -> &[u8; 32] {
		&self.meta.from_address
	}

	pub fn data(&self) -> &P {
		&self.payload
	}

	pub fn message(&self) -> &P {
		self.data()
	}
}

impl<P: AnchorSerialize + AnchorDeserialize> AnchorDeserialize for TransferWith<P> {
	fn deserialize(buf: &mut &[u8]) -> io::Result<Self> {
		Ok(TransferWith {
			meta: TransferWithMeta::deserialize(&mut &buf[..133])?,
			payload: P::deserialize(&mut &buf[133..])?,
		})
	}
}

/// Posted VAA (verified Wormhole message) of a Token Bridge transfer with
/// payload.
pub type PostedTransferWithPayload = PostedVaa<TransferWithPayload>;

/// Posted VAA (verified Wormhole message) of a Token Bridge transfer with
/// generic payload type `P`.
pub type PostedTransferWith<P> = PostedVaa<TransferWith<P>>;
