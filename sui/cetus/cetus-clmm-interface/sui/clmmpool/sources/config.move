module cetus_clmm::config {

    use sui::object::UID;
    use sui::vec_map::VecMap;

    use cetus_clmm::acl;

    /// The clmmpools fee tier data
    struct FeeTier has store, copy, drop {
        /// The tick spacing
        tick_spacing: u32,

        /// The default fee rate
        fee_rate: u64,
    }

    struct GlobalConfig has key, store {
        id: UID,
        /// `protocol_fee_rate` The protocol fee rate
        protocol_fee_rate: u64,
        /// 'fee_tiers' The Clmmpools fee tire map
        fee_tiers: VecMap<u32, FeeTier>,
        /// `acl` The Clmmpools ACL
        acl: acl::ACL,

        /// The current package version
        package_version: u64
    }
}