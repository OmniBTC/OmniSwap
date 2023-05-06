module omniswap::external_interface {
    use omniswap::wormhole_facet;
    use omniswap::wormhole_facet::Storage;
    use sui::object::UID;

    public fun get_dst_gas(storage: &mut Storage, dst_wormhole_chain_id: u16): (u256, u256)  {
        wormhole_facet::get_dst_gas(storage, dst_wormhole_chain_id)
    }
}
