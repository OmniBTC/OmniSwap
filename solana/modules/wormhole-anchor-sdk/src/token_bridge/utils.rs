pub const MAX_WRAPPED_ASSET_DECIMALS: u8 = 8;

/// Normalize raw amount based on this native mint's decimals.
pub fn normalize_amount(amount: u64, mint_decimals: u8) -> u64 {
	amount / amount_adjustment(mint_decimals)
}

/// Denormalize encoded amount based on this native mint's decimals. This will
/// be the amount transferred from the Token Bridge program's token (custody)
/// account.
pub fn denormalize_amount(amount: u64, mint_decimals: u8) -> u64 {
	amount * amount_adjustment(mint_decimals)
}

// Truncate raw amount based on this native mint's decimals before bridging
/// to prevent dust left in a token account.
pub fn truncate_amount(amount: u64, mint_decimals: u8) -> u64 {
	denormalize_amount(normalize_amount(amount, mint_decimals), mint_decimals)
}

fn amount_adjustment(mint_decimals: u8) -> u64 {
	if mint_decimals > MAX_WRAPPED_ASSET_DECIMALS {
		10u64.pow((mint_decimals - MAX_WRAPPED_ASSET_DECIMALS) as u32)
	} else {
		1
	}
}
