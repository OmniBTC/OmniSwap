module cetus_clmm::position {
    use std::string::String;
    use std::type_name::TypeName;

    use sui::object::{UID, ID};

    use integer_mate::i32::I32;

    use move_stl::linked_table;

    struct PositionManager has store {
        tick_spacing: u32,
        position_index: u64,
        positions: linked_table::LinkedTable<ID, PositionInfo>
    }

    /// The Cetus clmmpool's position NFT.
    struct Position has key, store {
        id: UID,
        pool: ID,
        index: u64,
        coin_type_a: TypeName,
        coin_type_b: TypeName,
        name: String,
        description: String,
        url: String,
        tick_lower_index: I32,
        tick_upper_index: I32,
        liquidity: u128,
    }

    /// The Cetus clmmpool's position information.
    struct PositionInfo has store, drop, copy {
        position_id: ID,
        liquidity: u128,
        tick_lower_index: I32,
        tick_upper_index: I32,
        fee_growth_inside_a: u128,
        fee_growth_inside_b: u128,
        fee_owned_a: u64,
        fee_owned_b: u64,
        points_owned: u128,
        points_growth_inside: u128,
        rewards: vector<PositionReward>,
    }

    /// The Position's rewarder
    struct PositionReward has drop, copy, store {
        growth_inside: u128,
        amount_owned: u64,
    }

    public fun liquidity(_position_nft: &Position): u128 {
        abort 0
    }
}
