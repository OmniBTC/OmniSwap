pub const CHAIN_ID_SOLANA: u16 = 1;

// seeds
pub const SEED_PREFIX_EMITTER: &[u8; 7] = b"emitter";
pub const SEED_PREFIX_POSTED_VAA: &[u8; 9] = b"PostedVAA";

// version 1 message
pub const MESSAGE_INDEX_VERSION: usize = 3;
pub const MESSAGE_INDEX_FINALITY: usize = 4;
pub const MESSAGE_INDEX_TIMESTAMP: usize = 5;
pub const MESSAGE_INDEX_SIGNATURE_ACCOUNT: usize = 9;
pub const MESSAGE_INDEX_POSTED_TIMESTAMP: usize = 41;
pub const MESSAGE_INDEX_BATCH_ID: usize = 45;
pub const MESSAGE_INDEX_SEQUENCE: usize = 49;
pub const MESSAGE_INDEX_EMITTER_CHAIN: usize = 57;
pub const MESSAGE_INDEX_EMITTER_ADDRESS: usize = 59;
pub const MESSAGE_INDEX_PAYLOAD_LENGTH: usize = 91;
pub const MESSAGE_INDEX_PAYLOAD: usize = 95;

// other useful constants
pub const INITIAL_SEQUENCE: u64 = 1;
