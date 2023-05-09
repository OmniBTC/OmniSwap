module cetus_clmm::rewarder {
    use sui::bag::Bag;
    use std::type_name::TypeName;

    use sui::object::UID;

    friend cetus_clmm::pool;

    struct RewarderManager has store {
        rewarders: vector<Rewarder>,
        points_released: u128,
        points_growth_global: u128,
        last_updated_time: u64,
    }

    struct Rewarder has copy, drop, store {
        reward_coin: TypeName,
        emissions_per_second: u128,
        growth_global: u128,
    }

    struct RewarderGlobalVault has key, store {
        id: UID,
        balances: Bag
    }
}
