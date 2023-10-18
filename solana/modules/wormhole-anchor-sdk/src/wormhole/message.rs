use anchor_lang::prelude::*;

#[derive(Default, AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub struct PostedVaaMeta {
	/// Header of the posted VAA
	pub version: u8,

	/// Level of consistency requested by the emitter
	pub finality: u8,

	/// Time the message was submitted
	pub timestamp: u32,

	/// Account where signatures are stored
	pub signature_set: Pubkey,

	/// Time the posted message was created
	pub posted_timestamp: u32,

	/// Unique id for this message
	pub batch_id: u32,

	/// Sequence number of this message
	pub sequence: u64,

	/// Emitter of the message
	pub emitter_chain: u16,

	/// Emitter of the message
	pub emitter_address: [u8; 32],
}
