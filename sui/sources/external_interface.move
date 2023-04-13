module omniswap::external_interface {
    use omniswap::wormhole_facet;
    use omniswap::wormhole_facet::Storage;

    struct DstGas has key {
        dst_base_gas: u256,
        dst_gas_per_bytes: u256
    }

    struct DstGasData has store, drop {
        dst_base_gas: u256,
        dst_gas_per_bytes: u256
    }


    public fun get_dst_gas(storage: &mut Storage, dst_wormhole_chain_id: u16): DstGasData  {
        let (dst_base_gas, dst_gas_per_bytes) = wormhole_facet::get_dst_gas(storage, dst_wormhole_chain_id);
        let dst_base_gas = dst_base_gas;
        let dst_gas_per_bytes = dst_gas_per_bytes;
        DstGasData {
            dst_base_gas,
            dst_gas_per_bytes
        }
    }
}
