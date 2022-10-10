module omniswap::wormhole_facet {
    use omniswap::cross;
    use omniswap::swap;
    use omniswap::u256::{U256, Self};
    use std::vector;
    use wormhole::emitter::EmitterCapability;
    use wormhole::wormhole;
    use wormhole::u16;
    use token_bridge::transfer_tokens;
    use aptos_framework::account;
    use std::signer;
    use omniswap::serde;
    use omniswap::cross::{SoData, SwapData};
    use omniswap::serde::{serialize_vector_with_length, serialize_u256};
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;
    use wormhole::external_address;
    use token_bridge::complete_transfer_with_payload;
    use token_bridge::transfer_with_payload;
    use aptos_framework::coin::{Coin, is_account_registered};
    use aptos_std::type_info;
    use aptos_framework::aptos_account;

    const SEED: vector<u8> = b"wormhole";

    const NOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const HAS_initialize: u64 = 0x01;

    const NOT_initialize: u64 = 0x02;

    const EINVALID_LENGTH: u64 = 0x03;

    struct WormholeData has drop, copy {
        dst_wormhole_chain_id: u64,
        dst_max_gas_price_in_wei_for_relayer: U256,
        wormhole_fee: U256,
        dst_so_diamond: vector<u8>,
    }

    struct EmitterManager has key {
        emitter_cap: EmitterCapability
    }


    fun transfer<X>(coin_x: Coin<X>, to: address) {
        if (!is_account_registered<X>(to) && type_info::type_of<X>() == type_info::type_of<AptosCoin>()) {
            aptos_account::create_account(to);
        };
        coin::deposit(to, coin_x);
    }

    public fun encode_wormhole_data(wormhole_data: WormholeData): vector<u8> {
        let data = vector::empty<u8>();
        serde::serialize_u64(&mut data, wormhole_data.dst_wormhole_chain_id);
        serde::serialize_u256(&mut data, wormhole_data.dst_max_gas_price_in_wei_for_relayer);
        serde::serialize_u256(&mut data, wormhole_data.wormhole_fee);
        serde::serialize_vector_with_length(&mut data, wormhole_data.dst_so_diamond);
        data
    }

    public fun decode_wormhole_data(data: &vector<u8>): WormholeData {
        let len = vector::length(data);
        assert!(len > 0, EINVALID_LENGTH);
        let index = 0;
        let wormhole_data = WormholeData {
            dst_wormhole_chain_id: 0,
            dst_max_gas_price_in_wei_for_relayer: u256::zero(),
            wormhole_fee: u256::zero(),
            dst_so_diamond: vector::empty()
        };
        wormhole_data.dst_wormhole_chain_id = serde::deserialize_u64(data);

        index = index + 8;
        wormhole_data.dst_max_gas_price_in_wei_for_relayer = serde::deserialize_u256(&serde::vector_slice(data, index, index + 32));

        index = index + 32;
        wormhole_data.wormhole_fee = serde::deserialize_u256(&serde::vector_slice(data, index, index + 32));

        index = index + 32;
        wormhole_data.dst_so_diamond = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));

        wormhole_data
    }

    public fun decode_wormhole_payload(data: &vector<u8>): (U256, U256, SoData, vector<SwapData>) {
        let len = vector::length(data);
        assert!(len > 0, EINVALID_LENGTH);
        let index = 0;

        let dst_max_gas_price = serde::deserialize_u256(data);

        index = index + 32;
        let dst_max_gas = serde::deserialize_u256(&serde::vector_slice(data, index, index + 32));

        let so_data = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));
        index = index + vector::length(&so_data);

        let so_data = cross::decode_so_data(&mut so_data);

        if (index < len) {
            let swap_data_dst = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, len));
            let swap_data_dst = cross::decode_swap_data(&mut swap_data_dst);
            (dst_max_gas_price, dst_max_gas, so_data, swap_data_dst)
        }else {
            (dst_max_gas_price, dst_max_gas, so_data, vector::empty())
        }
    }

    public fun encode_wormhole_payload(dst_max_gas_price: U256, dst_max_gas: U256, so_data: SoData, swap_data_dst: vector<SwapData>): vector<u8> {
        let data = vector::empty<u8>();
        let so_data = cross::encode_so_data(so_data);

        serialize_u256(&mut data, dst_max_gas_price);
        serialize_u256(&mut data, dst_max_gas);
        serialize_vector_with_length(&mut data, so_data);
        if (vector::length(&swap_data_dst) > 0) {
            let swap_data_dst = cross::encode_swap_data(swap_data_dst);
            serialize_vector_with_length(&mut data, swap_data_dst);
        };
        data
    }

    fun get_resource_address(): address {
        account::create_resource_address(&@omniswap, SEED)
    }

    public fun is_initialize(): bool {
        exists<EmitterManager>(get_resource_address())
    }

    public entry fun initiliaze(account: &signer) {
        assert!(signer::address_of(account) == @omniswap, NOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(), HAS_initialize);

        let (resource_signer, _) = account::create_resource_account(account, SEED);

        move_to(&resource_signer, EmitterManager { emitter_cap: wormhole::register_emitter() })
    }

    public entry fun so_swap<X, Y, Z, M>(
        account: &signer,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>
    ) acquires EmitterManager {
        assert!(is_initialize(), NOT_initialize);
        let emitter_cap = &borrow_global<EmitterManager>(get_resource_address()).emitter_cap;

        let so_data = cross::decode_so_data(&mut so_data);
        let wormhole_data = decode_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            u256::zero(), // todo! add relayer related
            so_data,
            swap_data_dst
        );

        let coin_val = u256::as_u64(wormhole_data.wormhole_fee);
        let coin_aptos = coin::withdraw<AptosCoin>(account, coin_val);

        if (vector::length(&swap_data_src) > 0) {
            let swap_data_src = cross::decode_swap_data(&mut swap_data_src);
            if (vector::length(&swap_data_src) == 1) {
                let coin_y = swap::swap_two_by_account<X, Y>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_y,
                    coin_aptos,
                    u16::from_u64(wormhole_data.dst_wormhole_chain_id),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0, // todo! nonce ++ ???
                    payload
                );
            }else if (vector::length(&swap_data_src) == 2) {
                let coin_z = swap::swap_three_by_account<X, Y, Z>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_z,
                    coin_aptos,
                    u16::from_u64(wormhole_data.dst_wormhole_chain_id),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0, // todo! nonce ++ ???
                    payload
                );
            }else if (vector::length(&swap_data_src) == 3) {
                let coin_m = swap::swap_four_by_account<X, Y, Z, M>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_m,
                    coin_aptos,
                    u16::from_u64(wormhole_data.dst_wormhole_chain_id),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0, // todo! nonce ++ ???
                    payload
                );
            }else {
                abort EINVALID_LENGTH
            }
        }else {
            let coin_val = u256::as_u64(cross::so_amount(so_data));
            let coin_x = coin::withdraw<X>(account, coin_val);
            transfer_tokens::transfer_tokens_with_payload(
                emitter_cap,
                coin_x,
                coin_aptos,
                u16::from_u64(wormhole_data.dst_wormhole_chain_id),
                external_address::from_bytes(wormhole_data.dst_so_diamond),
                0, // todo! nonce ++ ???
                payload
            );
        };
    }

    public entry fun complete_so_swap<X, Y, Z, M>(vaa: vector<u8>) acquires EmitterManager {
        let emitter_cap = &borrow_global<EmitterManager>(get_resource_address()).emitter_cap;
        let (coin_x, payload) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);
        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::get_payload(&payload));

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        // todo! add some check

        if (vector::length(&swap_data_dst) > 0) {
            if (vector::length(&swap_data_dst) == 1) {
                let coin_y = swap::swap_two_by_coin<X, Y>(coin_x, swap_data_dst);
                transfer(coin_y, receiver);
            }else if (vector::length(&swap_data_dst) == 2) {
                let coin_z = swap::swap_three_by_coin<X, Y, Z>(coin_x, swap_data_dst);
                transfer(coin_z, receiver);
            }else if (vector::length(&swap_data_dst) == 3) {
                let coin_m = swap::swap_four_by_coin<X, Y, Z, M>(coin_x, swap_data_dst);
                transfer(coin_m, receiver);
            }else {
                abort EINVALID_LENGTH
            }
        }else {
            transfer(coin_x, receiver);
        }
    }
}
