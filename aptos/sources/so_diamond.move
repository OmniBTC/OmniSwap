module omniswap::so_diamond {
    use std::string::String;
    use aptos_std::type_info::TypeInfo;
    use aptos_framework::bucket_table::{BucketTable, Self};


    struct SupportedBridge has key{
        // Bridge typeinfo -> description
        bridges: BucketTable<String, TypeInfo>
    }

    public fun is_supported(bridge: String) :bool acquires SupportedBridge {
        let bridges = &borrow_global<SupportedBridge>(@omniswap).bridges;
        bucket_table::contains(bridges, &bridge)
    }

    public entry fun so_swap_via_wormhole(){

    }

}
