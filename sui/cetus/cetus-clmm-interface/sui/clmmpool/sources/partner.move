module cetus_clmm::partner {
    use sui::object::{UID, ID};
    use sui::vec_map::VecMap;
    use std::string::String;
    use sui::bag::Bag;

    // =============== Structs =================

    struct Partners has key {
        id: UID,
        partners: VecMap<String, ID>
    }

    struct Partner has key, store {
        id: UID,
        name: String,
        ref_fee_rate: u64,
        start_time: u64,
        end_time: u64,
        balances: Bag,
    }
}
