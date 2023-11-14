pub mod swap_whirlpool_cpi;

pub const ORCA_WHIRLPOOL_SWAP: [u8; 9] = *b"Whirlpool";

pub use swap_whirlpool_cpi::ID as WhirlpoolProgram;
