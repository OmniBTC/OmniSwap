use anchor_lang::{prelude::*, solana_program};

use crate::wormhole::{message::PostedVaaMeta, program::ID};

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct BridgeData {
	/// The current guardian set index, used to decide which signature sets to accept.
	pub guardian_set_index: u32,

	/// Lamports in the collection account
	pub last_lamports: u64,

	/// Bridge configuration, which is set once upon initialization.
	pub config: BridgeConfig,
}

impl BridgeData {
	pub const SEED_PREFIX: &'static [u8; 6] = b"Bridge";

	pub fn guardian_set_expiration_time(&self) -> u32 {
		self.config.guardian_set_expiration_time
	}

	pub fn fee(&self) -> u64 {
		self.config.fee
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct BridgeConfig {
	/// Period for how long a guardian set is valid after it has been replaced by a new one.  This
	/// guarantees that VAAs issued by that set can still be submitted for a certain period.  In
	/// this period we still trust the old guardian set.
	pub guardian_set_expiration_time: u32,

	/// Amount of lamports that needs to be paid to the protocol to post a message
	pub fee: u64,
}

impl AccountDeserialize for BridgeData {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for BridgeData {}

impl Owner for BridgeData {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct FeeCollector {}

impl FeeCollector {
	pub const SEED_PREFIX: &'static [u8; 13] = b"fee_collector";
}

impl AccountDeserialize for FeeCollector {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for FeeCollector {}

impl Owner for FeeCollector {
	fn owner() -> Pubkey {
		solana_program::system_program::ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct SequenceTracker {
	pub sequence: u64,
}

impl SequenceTracker {
	pub const SEED_PREFIX: &'static [u8; 8] = b"Sequence";

	pub fn value(&self) -> u64 {
		self.sequence
	}

	pub fn next_value(&self) -> u64 {
		self.value() + 1
	}
}

impl AccountDeserialize for SequenceTracker {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for SequenceTracker {}

impl Owner for SequenceTracker {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct SignatureSetData {
	/// Signatures of validators
	pub signatures: Vec<bool>,

	/// Hash of the data
	pub hash: [u8; 32],

	/// Index of the guardian set
	pub guardian_set_index: u32,
}

impl AccountDeserialize for SignatureSetData {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for SignatureSetData {}

impl Owner for SignatureSetData {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct PostedVaaData {
	pub meta: PostedVaaMeta,
	pub payload: Vec<u8>,
}

impl PostedVaaData {
	pub const SEED_PREFIX: &'static [u8; 9] = super::SEED_PREFIX_POSTED_VAA;

	pub fn version(&self) -> u8 {
		self.meta.version
	}

	pub fn finality(&self) -> u8 {
		self.meta.finality
	}

	pub fn timestamp(&self) -> u32 {
		self.meta.timestamp
	}

	pub fn signature_set(&self) -> &Pubkey {
		&self.meta.signature_set
	}

	pub fn posted_timestamp(&self) -> u32 {
		self.meta.posted_timestamp
	}

	pub fn batch_id(&self) -> u32 {
		self.meta.batch_id
	}

	pub fn sequence(&self) -> u64 {
		self.meta.sequence
	}

	pub fn emitter_chain(&self) -> u16 {
		self.meta.emitter_chain
	}

	pub fn emitter_address(&self) -> &[u8; 32] {
		&self.meta.emitter_address
	}
}

impl AccountDeserialize for PostedVaaData {
	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		Self::deserialize(buf).map_err(Into::into)
	}
}

impl AccountSerialize for PostedVaaData {}

impl Owner for PostedVaaData {
	fn owner() -> Pubkey {
		ID
	}
}

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct PostedVaa<D: AnchorDeserialize + AnchorSerialize> {
	pub meta: PostedVaaMeta,
	pub payload: (u32, D),
}

impl<D: AnchorDeserialize + AnchorSerialize> PostedVaa<D> {
	pub fn version(&self) -> u8 {
		self.meta.version
	}

	pub fn finality(&self) -> u8 {
		self.meta.finality
	}

	pub fn timestamp(&self) -> u32 {
		self.meta.timestamp
	}

	pub fn signature_set(&self) -> &Pubkey {
		&self.meta.signature_set
	}

	pub fn posted_timestamp(&self) -> u32 {
		self.meta.posted_timestamp
	}

	pub fn batch_id(&self) -> u32 {
		self.meta.batch_id
	}

	pub fn sequence(&self) -> u64 {
		self.meta.sequence
	}

	pub fn emitter_chain(&self) -> u16 {
		self.meta.emitter_chain
	}

	pub fn emitter_address(&self) -> &[u8; 32] {
		&self.meta.emitter_address
	}

	pub fn payload_size(&self) -> u32 {
		self.payload.0
	}

	pub fn data(&self) -> &D {
		&self.payload.1
	}

	pub fn message(&self) -> &D {
		self.data()
	}
}

impl<D: AnchorDeserialize + AnchorSerialize> AccountDeserialize for PostedVaa<D> {
	fn try_deserialize(buf: &mut &[u8]) -> Result<Self> {
		require!(buf.len() >= 3, ErrorCode::AccountDiscriminatorNotFound);
		let given_disc = &buf[..3];
		require!(*given_disc == *b"vaa", ErrorCode::AccountDiscriminatorMismatch);
		Self::try_deserialize_unchecked(buf)
	}

	fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
		let mut data: &[u8] = &buf[3..];
		AnchorDeserialize::deserialize(&mut data).map_err(Into::into)
		//.map_err(|_| anchor_lang::error::ErrorCode::AccountDidNotDeserialize.into())
	}
}

impl<D: AnchorDeserialize + AnchorSerialize> AccountSerialize for PostedVaa<D> {}

impl<D: AnchorDeserialize + AnchorSerialize> Owner for PostedVaa<D> {
	fn owner() -> Pubkey {
		ID
	}
}
