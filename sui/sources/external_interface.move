module omniswap::external_interface {
    use omniswap::wormhole_facet;
    use omniswap::u256::{Self, U256};

    struct DstGas has key {
        dst_base_gas: U256,
        dst_gas_per_bytes: U256
    }

    struct DstGasData has key {
        dst_base_gas: u64,
        dst_gas_per_bytes: u64
    }


    public entry fun get_dst_gas(account: &signer, dst_wormhole_chain_id: u64) {
        let (dst_base_gas, dst_gas_per_bytes) = wormhole_facet::get_dst_gas(dst_wormhole_chain_id);
        let dst_base_gas = u256::as_u64(dst_base_gas);
        let dst_gas_per_bytes = u256::as_u64(dst_gas_per_bytes);
        move_to(account, DstGasData { dst_base_gas, dst_gas_per_bytes });
    }
}
