module omniswap::wormhole_facet {
    use omniswap::cross;
    use omniswap::swap;
    use omniswap::u256::{U256, Self};
    use omniswap::u16::{U16, Self};
    use wormhole::u16::{Self as wormhole_u16};
    use std::vector;
    use wormhole::emitter::EmitterCapability;
    use wormhole::wormhole;
    use token_bridge::transfer_tokens;
    use aptos_framework::account;
    use std::signer;
    use omniswap::serde;
    use omniswap::cross::{SoData, SwapData};
    use omniswap::serde::{serialize_vector_with_length, serialize_u256, deserialize_u256};
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;
    use wormhole::external_address;
    use token_bridge::complete_transfer_with_payload;
    use token_bridge::transfer_with_payload;
    use aptos_framework::coin::{Coin, is_account_registered};
    use aptos_std::type_info;
    use aptos_framework::aptos_account;
    use aptos_std::table::{Table, Self};
    use omniswap::so_fee_wormhole_v1;
    use wormhole::state;

    const RAY: u64 = 100000000;

    const SEED: vector<u8> = b"wormhole_facet";

    const NOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const HAS_initialize: u64 = 0x01;

    const NOT_initialize: u64 = 0x02;

    const EINVALID_LENGTH: u64 = 0x03;

    const EINVALID_ACCOUNT: u64 = 0x04;

    const EINVALID_CHAIN_ID: u64 = 0x05;

    const CHECK_FEE_FAIL: u64 = 0x05;


    struct WormholeData has drop, copy {
        dst_wormhole_chain_id: U16,
        dst_max_gas_price_in_wei_for_relayer: U256,
        wormhole_fee: u64,
        dst_so_diamond: vector<u8>,
    }

    struct EmitterManager has key {
        emitter_cap: EmitterCapability
    }

    struct Storage has key {
        src_wormhole_chain_id: U16,
        nonce: u64,
        actual_reserve: u64,
        estimate_reserve: u64,
        dst_base_gas: Table<U16, U256>,
        dst_gas_per_bytes: Table<U16, U256>
    }


    fun transfer<X>(coin_x: Coin<X>, to: address) {
        if (!is_account_registered<X>(to) && type_info::type_of<X>() == type_info::type_of<AptosCoin>()) {
            aptos_account::create_account(to);
        };
        coin::deposit(to, coin_x);
    }

    public fun encode_wormhole_data(wormhole_data: WormholeData): vector<u8> {
        let data = vector::empty<u8>();
        serde::serialize_u16(&mut data, wormhole_data.dst_wormhole_chain_id);
        serde::serialize_u256(&mut data, wormhole_data.dst_max_gas_price_in_wei_for_relayer);
        serde::serialize_u64(&mut data, wormhole_data.wormhole_fee);
        serde::serialize_vector_with_length(&mut data, wormhole_data.dst_so_diamond);
        data
    }

    public fun decode_wormhole_data(data: &vector<u8>): WormholeData {
        let len = vector::length(data);
        assert!(len > 0, EINVALID_LENGTH);
        let index = 0;
        let wormhole_data = WormholeData {
            dst_wormhole_chain_id: u16::zero(),
            dst_max_gas_price_in_wei_for_relayer: u256::zero(),
            wormhole_fee: 0,
            dst_so_diamond: vector::empty()
        };
        wormhole_data.dst_wormhole_chain_id = serde::deserialize_u16(data);

        index = index + 2;
        wormhole_data.dst_max_gas_price_in_wei_for_relayer = serde::deserialize_u256(&serde::vector_slice(data, index, index + 32));

        index = index + 32;
        wormhole_data.wormhole_fee = serde::deserialize_u64(&serde::vector_slice(data, index, index + 8));

        index = index + 8;
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

    // Update permission
    fun is_approve(account: address): bool {
        // todo! add permission manage
        account == @omniswap
    }

    public fun is_initialize(): bool {
        exists<EmitterManager>(get_resource_address())
    }

    public entry fun init_wormhole(account: &signer, wormhole_chain_id: u64) {
        assert!(signer::address_of(account) == @omniswap, NOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(), HAS_initialize);

        let (resource_signer, _) = account::create_resource_account(account, SEED);

        move_to(&resource_signer, EmitterManager { emitter_cap: wormhole::register_emitter() });
        move_to(&resource_signer,
            Storage {
                src_wormhole_chain_id: u16::from_u64(wormhole_chain_id),
                nonce: 0,
                actual_reserve: 0,
                estimate_reserve: 0,
                dst_base_gas: table::new(),
                dst_gas_per_bytes: table::new()
            });
    }

    public entry fun set_wormhole_reserve(
        account: &signer,
        actual_reserve: u64,
        estimate_reserve: u64
    ) acquires Storage {
        assert!(is_initialize(), NOT_initialize);
        assert!(is_approve(signer::address_of(account)), EINVALID_ACCOUNT);

        let s = borrow_global_mut<Storage>(get_resource_address());
        s.actual_reserve = actual_reserve;
        s.estimate_reserve = estimate_reserve;
    }

    public entry fun set_wormhole_gas(
        account: &signer,
        dst_wormhole_chain_id: u64,
        base_gas: vector<u8>,
        gas_per_bytes: vector<u8>
    ) acquires Storage {
        assert!(is_initialize(), NOT_initialize);
        assert!(is_approve(signer::address_of(account)), EINVALID_ACCOUNT);
        let s = borrow_global_mut<Storage>(get_resource_address());

        let dst_wormhole_chain_id = u16::from_u64(dst_wormhole_chain_id);

        table::upsert(&mut s.dst_base_gas, dst_wormhole_chain_id, deserialize_u256(&base_gas));
        table::upsert(&mut s.dst_gas_per_bytes, dst_wormhole_chain_id, deserialize_u256(&gas_per_bytes));
    }

    public fun estimate_complete_soswap_gas(
        so_data: vector<u8>,
        wormhole_data: WormholeData,
        swap_data_dst: vector<u8>
    ): U256 acquires Storage {
        let len = 32 + 32 + 1 + vector::length(&so_data) + 1 + vector::length(&swap_data_dst);
        let s = borrow_global<Storage>(get_resource_address());
        assert!(table::contains(&s.dst_base_gas, wormhole_data.dst_wormhole_chain_id), EINVALID_CHAIN_ID);
        let dst_base_gas = *table::borrow(&s.dst_base_gas, wormhole_data.dst_wormhole_chain_id);
        let dst_gas_per_bytes = *table::borrow(&s.dst_gas_per_bytes, wormhole_data.dst_wormhole_chain_id);
        u256::add(dst_base_gas, u256::mul(dst_gas_per_bytes, u256::from_u64(len)))
    }

    public fun check_relayer_fee(
        so_data: SoData,
        wormhole_data: WormholeData,
        swap_data_dst: vector<SwapData>
    ): (bool, u64, u64, U256) acquires Storage {
        let actual_reserve = borrow_global<Storage>(get_resource_address()).actual_reserve;

        let ratio = so_fee_wormhole_v1::update_price_ratio(u16::to_u64(wormhole_data.dst_wormhole_chain_id));

        let dst_max_gas = estimate_complete_soswap_gas(cross::encode_so_data(so_data), wormhole_data, cross::encode_swap_data(swap_data_dst));
        let dst_fee = u256::mul(wormhole_data.dst_max_gas_price_in_wei_for_relayer, dst_max_gas);

        let one = u256::from_u64(RAY);

        let src_fee = u256::mul(dst_fee, u256::from_u64(ratio));
        src_fee = u256::div(src_fee, one);
        src_fee = u256::mul(src_fee, u256::from_u64(actual_reserve));
        src_fee = u256::div(src_fee, one);

        let comsume_value = u256::from_u64(state::get_message_fee());
        comsume_value = u256::add(comsume_value, cross::so_amount(so_data));
        comsume_value = u256::add(comsume_value, src_fee);

        let src_fee = u256::as_u64(src_fee);
        let comsume_value = u256::as_u64(comsume_value);

        let flag = false;
        let return_value = 0;

        if (comsume_value <= wormhole_data.wormhole_fee) {
            flag = true;
            return_value = wormhole_data.wormhole_fee - comsume_value;
        };
        (flag, src_fee, return_value, dst_max_gas)
    }

    public entry fun so_swap<X, Y, Z, M>(
        account: &signer,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>
    ) acquires EmitterManager, Storage {
        assert!(is_initialize(), NOT_initialize);
        let emitter_cap = &borrow_global<EmitterManager>(get_resource_address()).emitter_cap;

        let so_data = cross::decode_so_data(&mut so_data);
        let wormhole_data = decode_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, _, dst_max_gas) = check_relayer_fee(so_data, wormhole_data, swap_data_dst);
        assert!(flag, CHECK_FEE_FAIL);


        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let coin_aptos = coin::withdraw<AptosCoin>(account, fee);

        let s = borrow_global_mut<Storage>(get_resource_address());
        if (vector::length(&swap_data_src) > 0) {
            let swap_data_src = cross::decode_swap_data(&mut swap_data_src);
            if (vector::length(&swap_data_src) == 1) {
                let coin_y = swap::swap_two_by_account<X, Y>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_y,
                    coin_aptos,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    s.nonce,
                    payload
                );
            }else if (vector::length(&swap_data_src) == 2) {
                let coin_z = swap::swap_three_by_account<X, Y, Z>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_z,
                    coin_aptos,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    s.nonce,
                    payload
                );
            }else if (vector::length(&swap_data_src) == 3) {
                let coin_m = swap::swap_four_by_account<X, Y, Z, M>(account, swap_data_src);
                transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_m,
                    coin_aptos,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    s.nonce,
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
                wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                external_address::from_bytes(wormhole_data.dst_so_diamond),
                s.nonce,
                payload
            );
        };
        s.nonce = s.nonce + 1;
    }

    public entry fun complete_so_swap<X, Y, Z, M>(vaa: vector<u8>) acquires EmitterManager {
        assert!(is_initialize(), NOT_initialize);

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
