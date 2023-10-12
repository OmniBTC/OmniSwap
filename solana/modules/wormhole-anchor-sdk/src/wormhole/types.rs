use anchor_lang::prelude::*;

#[derive(AnchorDeserialize, AnchorSerialize, Clone, Copy, PartialEq, Eq)]
pub enum Finality {
	Confirmed,
	Finalized,
}

impl TryFrom<u8> for Finality {
	type Error = std::io::Error;

	fn try_from(value: u8) -> std::result::Result<Self, Self::Error> {
		match value {
			0 => Ok(Finality::Confirmed),
			1 => Ok(Finality::Finalized),
			_ => Err(std::io::Error::new(std::io::ErrorKind::InvalidData, "invalid finality")),
		}
	}
}
