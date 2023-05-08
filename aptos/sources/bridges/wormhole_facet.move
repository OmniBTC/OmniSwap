module omniswap::wormhole_facet {
    use std::vector;
    use std::signer;

    use aptos_std::table::{Table, Self};
    use aptos_std::type_info;
    use aptos_std::event::{Self, EventHandle};

    use aptos_framework::coin::{Self, Coin, is_account_registered};
    use aptos_framework::aptos_account;
    use aptos_framework::account;
    use aptos_framework::aptos_coin::AptosCoin;

    use wormhole::u16::{Self as wormhole_u16};
    use wormhole::emitter::EmitterCapability;
    use wormhole::wormhole;
    use wormhole::state;
    use wormhole::external_address;

    use token_bridge::transfer_tokens;
    use token_bridge::complete_transfer_with_payload;
    use token_bridge::transfer_with_payload;

    use omniswap::cross;
    use omniswap::swap;
    use omniswap::u256::{U256, Self};
    use omniswap::u16::{U16, Self};
    use omniswap::serde;
    use omniswap::cross::{NormalizedSoData, NormalizedSwapData, padding_swap_data};
    use omniswap::serde::{deserialize_u256, serialize_u256_with_hex_str, serialize_u16, serialize_u8};
    use omniswap::so_fee_wormhole;
    use omniswap::swap::right_type;
    #[test_only]
    use omniswap::cross::padding_so_data;


    const RAY: u64 = 100000000;

    const SEED: vector<u8> = b"wormhole_facet";

    const SEED_SO: vector<u8> = b"so_facet";

    // Data delimiter, represent ";"
    const INTER_DELIMITER: u8 = 59;

    /// Errors Code
    const ENOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const EHAS_INITIALIZE: u64 = 0x01;

    const ENOT_INITIALIZE: u64 = 0x02;

    const EINVALID_LENGTH: u64 = 0x03;

    const EINVALID_ACCOUNT: u64 = 0x04;

    const EINVALID_CHAIN_ID: u64 = 0x05;

    const ECHECK_FEE_FAIL: u64 = 0x06;

    /// Storage

    /// The so fee of cross token
    struct WormholeFee has key {
        fee: u64,
        beneficiary: address
    }

    struct WormholeRelayer has key {
        relayer: address
    }

    struct Storage has key {
        // current wormhole chain id, aptos 22
        src_wormhole_chain_id: U16,
        // actual relayer fee scale factor
        actual_reserve: u64,
        // estimate relayer fee scale factor
        estimate_reserve: u64,
        // target chain minimum consumption of gas
        dst_base_gas: Table<U16, U256>,
        // target chain gas per bytes
        dst_gas_per_bytes: Table<U16, U256>,
        // Deprecated
        // track cross-chain swaps sent from this chain
        so_transfer_started_events: EventHandle<SoTransferStartedEvent>,
        // Deprecated
        // track cross-chain swaps that reach the chain
        so_transfer_completed_events: EventHandle<SoTransferCompletedEvent>,
        // trace wormhole msg sent from this chain
        transfer_from_wormhole_events: EventHandle<TransferFromWormholeEvent>
    }

    struct SoTransferEventHandle has key {
        so_transfer_started: EventHandle<SoTransferStarted>,
        so_transfer_completed: EventHandle<SoTransferCompleted>
    }

    /// Some parameters needed to use wormhole
    struct NormalizedWormholeData has drop, copy {
        // destination wormhole chain id
        dst_wormhole_chain_id: U16,
        // gas price of the target chain
        dst_max_gas_price_in_wei_for_relayer: U256,
        // payment required for aptos coin
        wormhole_fee: U256,
        // destination chain sodiamond address
        dst_so_diamond: vector<u8>,
    }

    /// Own wormhole emitter capability
    struct WormholeFacetManager has key {
        emitter_cap: EmitterCapability,
        owner: address
    }

    /// Events

    struct TransferFromWormholeEvent has store, drop {
        src_wormhole_chain_id: U16,
        dst_wormhole_chain_id: U16,
        sequence: u64
    }

    /// Deprecated
    struct SoTransferStartedEvent has store, drop {
        transaction_id: vector<u8>,
        bridge: address,
        has_source_swap: bool,
        has_destination_swap: bool,
        so_data: vector<u8>
    }

    /// Deprecated
    struct SoTransferCompletedEvent has store, drop {
        transaction_id: vector<u8>,
        receiveing_asset_id: address,
        receiver: address,
        receive_amount: u64,
        timestamp: u64,
        so_data: vector<u8>
    }

    struct SoTransferStarted has store, drop {
        transaction_id: vector<u8>,
    }

    struct SoTransferCompleted has store, drop {
        transaction_id: vector<u8>,
        actual_receiving_amount: u64,
    }

    /// Helpers
    public fun is_initialize(): bool {
        exists<WormholeFacetManager>(get_resource_address())
    }

    public entry fun transfer_owner(account: &signer, to: address) acquires WormholeFacetManager {
        assert!(is_owner(signer::address_of(account)), EINVALID_ACCOUNT);
        let manager = borrow_global_mut<WormholeFacetManager>(get_resource_address());
        manager.owner = to;
    }

    fun is_owner(account: address): bool acquires WormholeFacetManager {
        let manager = borrow_global<WormholeFacetManager>(get_resource_address());
        return manager.owner == account
    }

    public entry fun transfer_beneficiary(account: &signer, to: address) acquires WormholeFee {
        let manager = borrow_global_mut<WormholeFee>(get_resource_address());
        assert!(manager.beneficiary == signer::address_of(account), EINVALID_ACCOUNT);
        manager.beneficiary = to;
    }

    public entry fun set_relayer(account: &signer, relayer: address) acquires WormholeRelayer {
        assert!(is_initialize(), ENOT_INITIALIZE);
        assert!(signer::address_of(account) == @omniswap, EINVALID_ACCOUNT);
        if (exists<WormholeRelayer>(@omniswap)) {
            let wormhole_relayer = borrow_global_mut<WormholeRelayer>(@omniswap);
            wormhole_relayer.relayer = relayer;
        }else {
            move_to(account, WormholeRelayer {
                relayer
            });
        }
    }

    public fun get_relayer(): address acquires WormholeRelayer {
        borrow_global<WormholeRelayer>(@omniswap).relayer
    }


    /// Make sure the user has aptos coin, and help register if they don't.
    fun transfer<X>(coin_x: Coin<X>, to: address) {
        if (!is_account_registered<X>(to) && type_info::type_of<X>() == type_info::type_of<AptosCoin>()) {
            aptos_account::create_account(to);
        };
        coin::deposit(to, coin_x);
    }

    fun is_transfer<X>(to: address): bool {
        if (is_account_registered<X>(to) || type_info::type_of<X>() == type_info::type_of<AptosCoin>()) {
            true
        }else {
            false
        }
    }

    fun get_resource_address(): address {
        account::create_resource_address(&@omniswap, SEED)
    }

    fun get_resource_address_so(): address {
        account::create_resource_address(&@omniswap, SEED_SO)
    }

    fun get_beneficiary_address(): address acquires WormholeFee {
        if (exists<WormholeFee>(get_resource_address())) {
            let manager = borrow_global_mut<WormholeFee>(get_resource_address());
            manager.beneficiary
        }else {
            @omniswap
        }
    }

    public entry fun set_so_fees(account: &signer, fee: u64) acquires WormholeFee {
        let manager = borrow_global_mut<WormholeFee>(get_resource_address());
        assert!(manager.beneficiary == signer::address_of(account), EINVALID_ACCOUNT);
        manager.fee = fee;
    }

    #[legacy_entry_fun]
    public entry fun get_so_fees(): u64 acquires WormholeFee {
        if (exists<WormholeFee>(get_resource_address())) {
            let manager = borrow_global_mut<WormholeFee>(get_resource_address());
            manager.fee
        }else {
            0
        }
    }

    /// Inits

    /// Set the wormhole chain id used by the current chain
    public entry fun init_wormhole(account: &signer, wormhole_chain_id: u64) {
        assert!(signer::address_of(account) == @omniswap, ENOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(), EHAS_INITIALIZE);

        let (resource_signer, _) = account::create_resource_account(account, SEED);

        move_to(&resource_signer, WormholeFacetManager {
            emitter_cap: wormhole::register_emitter(),
            owner: @omniswap
        });
        move_to(&resource_signer,
            Storage {
                src_wormhole_chain_id: u16::from_u64(wormhole_chain_id),
                actual_reserve: 0,
                estimate_reserve: 0,
                dst_base_gas: table::new(),
                dst_gas_per_bytes: table::new(),
                so_transfer_started_events: account::new_event_handle(&resource_signer),
                so_transfer_completed_events: account::new_event_handle(&resource_signer),
                transfer_from_wormhole_events: account::new_event_handle(&resource_signer)
            });
        move_to(&resource_signer,
            WormholeFee {
                fee: 0,
                beneficiary: @omniswap
            }
        );
    }

    public entry fun init_so_transfer_event(account: &signer) {
        assert!(signer::address_of(account) == @omniswap, ENOT_DEPLOYED_ADDRESS);
        assert!(!exists<SoTransferEventHandle>(signer::address_of(account)), EHAS_INITIALIZE);
        let (resource_signer, _) = account::create_resource_account(account, SEED_SO);
        move_to(&resource_signer,
            SoTransferEventHandle {
                so_transfer_started: account::new_event_handle(&resource_signer),
                so_transfer_completed: account::new_event_handle(&resource_signer)
            });
    }

    public entry fun register_new_emitter(account: &signer) {
        move_to(account, WormholeFacetManager {
            emitter_cap: wormhole::register_emitter(),
            owner: signer::address_of(account)
        });
    }

    /// Set relayer fee scale factor
    public entry fun set_wormhole_reserve(
        account: &signer,
        actual_reserve: u64,
        estimate_reserve: u64
    ) acquires Storage, WormholeFacetManager {
        assert!(is_initialize(), ENOT_INITIALIZE);
        assert!(is_owner(signer::address_of(account)), EINVALID_ACCOUNT);

        let s = borrow_global_mut<Storage>(get_resource_address());
        s.actual_reserve = actual_reserve;
        s.estimate_reserve = estimate_reserve;
    }

    /// Set destination chain's minimum gas and gas per bytes
    public entry fun set_wormhole_gas(
        account: &signer,
        dst_wormhole_chain_id: u64,
        base_gas: vector<u8>,
        gas_per_bytes: vector<u8>
    ) acquires Storage, WormholeFacetManager {
        assert!(is_initialize(), ENOT_INITIALIZE);
        assert!(is_owner(signer::address_of(account)), EINVALID_ACCOUNT);
        let s = borrow_global_mut<Storage>(get_resource_address());

        let dst_wormhole_chain_id = u16::from_u64(dst_wormhole_chain_id);

        table::upsert(&mut s.dst_base_gas, dst_wormhole_chain_id, deserialize_u256(&base_gas));
        table::upsert(&mut s.dst_gas_per_bytes, dst_wormhole_chain_id, deserialize_u256(&gas_per_bytes));
    }

    /// Swap

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized, and all of this data can be serialized and
    /// deserialized in the methods found here.
    public entry fun so_swap<X, Y, Z, M>(
        account: &signer,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>
    ) acquires WormholeFacetManager, Storage, SoTransferEventHandle, WormholeFee {
        assert!(is_initialize(), ENOT_INITIALIZE);
        let resource_address = get_resource_address();
        let emitter_cap = &borrow_global<WormholeFacetManager>(resource_address).emitter_cap;

        let so_data = cross::decode_normalized_so_data(&mut so_data);
        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, _, dst_max_gas) = check_relayer_fee(so_data, wormhole_data, swap_data_dst);
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let coin_fees = coin::withdraw<AptosCoin>(account, fee);
        transfer(coin_fees, get_beneficiary_address());

        let wormhole_fee = coin::withdraw<AptosCoin>(account, state::get_message_fee());

        let sequence: u64;
        if (vector::length(&swap_data_src) > 0) {
            let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);
            if (vector::length(&swap_data_src) == 1) {
                let coin_y = swap::swap_two_by_account<X, Y>(account, swap_data_src);
                sequence = transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_y,
                    wormhole_fee,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0,
                    payload
                );
            }else if (vector::length(&swap_data_src) == 2) {
                let coin_z = swap::swap_three_by_account<X, Y, Z>(account, swap_data_src);
                sequence = transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_z,
                    wormhole_fee,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0,
                    payload
                );
            }else if (vector::length(&swap_data_src) == 3) {
                let coin_m = swap::swap_four_by_account<X, Y, Z, M>(account, swap_data_src);
                sequence = transfer_tokens::transfer_tokens_with_payload(
                    emitter_cap,
                    coin_m,
                    wormhole_fee,
                    wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                    external_address::from_bytes(wormhole_data.dst_so_diamond),
                    0,
                    payload
                );
            }else {
                abort EINVALID_LENGTH
            }
        }else {
            let coin_val = u256::as_u64(cross::so_amount(so_data));
            let coin_x = coin::withdraw<X>(account, coin_val);
            sequence = transfer_tokens::transfer_tokens_with_payload(
                emitter_cap,
                coin_x,
                wormhole_fee,
                wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
                external_address::from_bytes(wormhole_data.dst_so_diamond),
                0,
                payload
            );
        };

        let so_transfer_evnet_handle = borrow_global_mut<SoTransferEventHandle>(get_resource_address_so());
        event::emit_event<SoTransferStarted>(
            &mut so_transfer_evnet_handle.so_transfer_started,
            SoTransferStarted {
                transaction_id: cross::so_transaction_id(so_data),
            }
        );

        let s = borrow_global_mut<Storage>(resource_address);
        event::emit_event<TransferFromWormholeEvent>(
            &mut s.transfer_from_wormhole_events,
            TransferFromWormholeEvent {
                src_wormhole_chain_id: s.src_wormhole_chain_id,
                dst_wormhole_chain_id: wormhole_data.dst_wormhole_chain_id,
                sequence
            }
        );
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap<X, Y, Z, M>(
        vaa: vector<u8>
    ) acquires WormholeFacetManager, WormholeFee, SoTransferEventHandle {
        assert!(is_initialize(), ENOT_INITIALIZE);

        let resource_address = get_resource_address();
        let emitter_cap = &borrow_global<WormholeFacetManager>(resource_address).emitter_cap;
        let (coin_x, payload) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
        let beneficiary = get_beneficiary_address();
        if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
            let coin_fee = coin::extract(&mut coin_x, so_fee);
            transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::get_payload(&payload));

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        if (vector::length(&swap_data_dst) > 0) {
            if (vector::length(&swap_data_dst) == 1) {
                let coin_y = swap::swap_two_by_coin<X, Y>(coin_x, swap_data_dst);

                receiving_amount = coin::value(&coin_y);
                transfer(coin_y, receiver);
            }else if (vector::length(&swap_data_dst) == 2) {
                let coin_z = swap::swap_three_by_coin<X, Y, Z>(coin_x, swap_data_dst);

                receiving_amount = coin::value(&coin_z);
                transfer(coin_z, receiver);
            }else if (vector::length(&swap_data_dst) == 3) {
                let coin_m = swap::swap_four_by_coin<X, Y, Z, M>(coin_x, swap_data_dst);

                receiving_amount = coin::value(&coin_m);
                transfer(coin_m, receiver);
            }else {
                abort EINVALID_LENGTH
            }
        }else {
            transfer(coin_x, receiver);
        };

        let so_transfer_event_handle = borrow_global_mut<SoTransferEventHandle>(get_resource_address_so());
        event::emit_event<SoTransferCompleted>(
            &mut so_transfer_event_handle.so_transfer_completed,
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        )
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_by_account<X, Y, Z, M>(
        account: &signer,
        vaa: vector<u8>
    ) acquires WormholeFacetManager, WormholeFee, SoTransferEventHandle {
        assert!(is_initialize(), ENOT_INITIALIZE);

        let resource_address = get_resource_address();
        let emitter_cap = &borrow_global<WormholeFacetManager>(resource_address).emitter_cap;
        let (coin_x, payload) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
        let beneficiary = get_beneficiary_address();
        if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
            let coin_fee = coin::extract(&mut coin_x, so_fee);
            transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::get_payload(&payload));

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        if (vector::length(&swap_data_dst) > 0) {
            if (vector::length(&swap_data_dst) == 1) {
                let coin_y = swap::swap_two_by_coin_with_delegate<X, Y>(coin_x, swap_data_dst, account);

                receiving_amount = coin::value(&coin_y);
                transfer(coin_y, receiver);
            }else if (vector::length(&swap_data_dst) == 2) {
                let coin_z = swap::swap_three_by_coin_with_delegate<X, Y, Z>(coin_x, swap_data_dst, account);

                receiving_amount = coin::value(&coin_z);
                transfer(coin_z, receiver);
            }else if (vector::length(&swap_data_dst) == 3) {
                let coin_m = swap::swap_four_by_coin_with_delegate<X, Y, Z, M>(coin_x, swap_data_dst, account);

                receiving_amount = coin::value(&coin_m);
                transfer(coin_m, receiver);
            }else {
                abort EINVALID_LENGTH
            }
        }else {
            transfer(coin_x, receiver);
        };

        let so_transfer_event_handle = borrow_global_mut<SoTransferEventHandle>(get_resource_address_so());
        event::emit_event<SoTransferCompleted>(
            &mut so_transfer_event_handle.so_transfer_completed,
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        )
    }

    /// To avoid wormhole payload data construction errors, lock the token and allow the owner to handle
    /// it manually.
    public entry fun complete_so_swap_by_admin<X, Y, Z, M>(
        account: &signer,
        vaa: vector<u8>,
        to: address
    ) acquires WormholeFacetManager, WormholeFee, SoTransferEventHandle {
        assert!(is_initialize(), ENOT_INITIALIZE);
        assert!(signer::address_of(account) == @omniswap, EINVALID_ACCOUNT);

        let emitter_cap = &borrow_global<WormholeFacetManager>(get_resource_address()).emitter_cap;
        let (coin_x, payload) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
        let beneficiary = get_beneficiary_address();
        if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
            let coin_fee = coin::extract(&mut coin_x, so_fee);
            transfer(coin_fee, beneficiary);
        };

        let receiving_amount = coin::value(&coin_x);
        transfer(coin_x, to);

        let (_, _, so_data, _) = decode_wormhole_payload(&transfer_with_payload::get_payload(&payload));
        let so_transfer_event_handle = borrow_global_mut<SoTransferEventHandle>(get_resource_address_so());
        event::emit_event<SoTransferCompleted>(
            &mut so_transfer_event_handle.so_transfer_completed,
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        )
    }

    public entry fun complete_so_swap_by_emitter<X, Y, Z, M>(
        account: &signer,
        vaa: vector<u8>,
        to: address
    ) acquires WormholeFacetManager, WormholeFee {
        assert!(is_initialize(), ENOT_INITIALIZE);

        let emitter_cap = &borrow_global<WormholeFacetManager>(signer::address_of(account)).emitter_cap;
        let (coin_x, _) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
        let beneficiary = get_beneficiary_address();
        if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
            let coin_fee = coin::extract(&mut coin_x, so_fee);
            transfer(coin_fee, beneficiary);
        };

        transfer(coin_x, to);
    }

    /// To avoid swap min amount errors, allow relayer to compensate
    public entry fun complete_so_swap_by_relayer<X, Y, Z, M>(
        account: &signer,
        vaa: vector<u8>,
    ) acquires WormholeFacetManager, WormholeFee, WormholeRelayer, SoTransferEventHandle {
        assert!(is_initialize(), ENOT_INITIALIZE);
        assert!(signer::address_of(account) == get_relayer(), EINVALID_ACCOUNT);

        let emitter_cap = &borrow_global<WormholeFacetManager>(get_resource_address()).emitter_cap;
        let (coin_x, payload) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
        let beneficiary = get_beneficiary_address();
        if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
            let coin_fee = coin::extract(&mut coin_x, so_fee);
            transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, _) = decode_wormhole_payload(&transfer_with_payload::get_payload(&payload));

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);

        transfer(coin_x, receiver);

        let so_transfer_event_handle = borrow_global_mut<SoTransferEventHandle>(get_resource_address_so());
        event::emit_event<SoTransferCompleted>(
            &mut so_transfer_event_handle.so_transfer_completed,
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        )
    }

    /// Swap Helpers

    /// Ensure that there is a minimal cost to help Relayer complete transactions in the destination chain.
    public fun check_relayer_fee(
        so_data: NormalizedSoData,
        wormhole_data: NormalizedWormholeData,
        swap_data_dst: vector<NormalizedSwapData>
    ): (bool, u64, u64, U256) acquires Storage {
        let actual_reserve = borrow_global<Storage>(get_resource_address()).actual_reserve;

        let ratio = so_fee_wormhole::update_price_ratio(u16::to_u64(wormhole_data.dst_wormhole_chain_id));

        let dst_max_gas = estimate_complete_soswap_gas(
            cross::encode_normalized_so_data(so_data),
            wormhole_data,
            cross::encode_normalized_swap_data(swap_data_dst)
        );
        let dst_fee = u256::mul(wormhole_data.dst_max_gas_price_in_wei_for_relayer, dst_max_gas);

        let one = u256::from_u64(RAY);
        let src_fee = u256::mul(dst_fee, u256::from_u64(ratio));
        src_fee = u256::div(src_fee, one);
        src_fee = u256::mul(src_fee, u256::from_u64(actual_reserve));
        src_fee = u256::div(src_fee, one);

        if (u16::to_u64(wormhole_data.dst_wormhole_chain_id) == 21) {
            // Sui chain, decimal / 10
            src_fee = u256::div(src_fee, u256::from_u64(10));
        }else {
            // Evm chain, decimal change
            src_fee = u256::div(src_fee, u256::from_u64(10000000000));
        };


        let comsume_value = u256::from_u64(state::get_message_fee());

        if (right_type<AptosCoin>(cross::so_sending_asset_id(so_data))) {
            comsume_value = u256::add(comsume_value, cross::so_amount(so_data));
        };
        comsume_value = u256::add(comsume_value, src_fee);

        let src_fee = u256::as_u64(src_fee);
        let comsume_value = u256::as_u64(comsume_value);

        let flag = false;
        let return_value = 0;

        let wormhole_fee = u256::as_u64(wormhole_data.wormhole_fee);
        if (comsume_value <= wormhole_fee) {
            flag = true;
            return_value = wormhole_fee - comsume_value;
        };
        (flag, src_fee, comsume_value, dst_max_gas)
    }

    public fun estimate_complete_soswap_gas(
        so_data: vector<u8>,
        wormhole_data: NormalizedWormholeData,
        swap_data_dst: vector<u8>
    ): U256 acquires Storage {
        let len = 32 + 32 + 1 + vector::length(&so_data) + 1 + vector::length(&swap_data_dst);
        let s = borrow_global<Storage>(get_resource_address());
        if (table::contains(&s.dst_base_gas, wormhole_data.dst_wormhole_chain_id)) {
            let dst_base_gas = *table::borrow(&s.dst_base_gas, wormhole_data.dst_wormhole_chain_id);
            let dst_gas_per_bytes = *table::borrow(&s.dst_gas_per_bytes, wormhole_data.dst_wormhole_chain_id);
            u256::add(dst_base_gas, u256::mul(dst_gas_per_bytes, u256::from_u64(len)))
        }else {
            u256::zero()
        }
    }

    /// Query gas
    public fun get_dst_gas(dst_wormhole_chain_id: u64): (U256, U256) acquires Storage {
        let dst_wormhole_chain_id = u16::from_u64(dst_wormhole_chain_id);
        let s = borrow_global<Storage>(get_resource_address());
        if (table::contains(&s.dst_base_gas, dst_wormhole_chain_id)) {
            let dst_base_gas = *table::borrow(&s.dst_base_gas, dst_wormhole_chain_id);
            let dst_gas_per_bytes = *table::borrow(&s.dst_gas_per_bytes, dst_wormhole_chain_id);
            (dst_base_gas, dst_gas_per_bytes)
        }else {
            (u256::zero(), u256::zero())
        }
    }

    /// Encode && Decode
    public fun encode_normalized_wormhole_data(wormhole_data: NormalizedWormholeData): vector<u8> {
        let data = vector::empty<u8>();
        serde::serialize_u16(&mut data, wormhole_data.dst_wormhole_chain_id);
        serde::serialize_u256(&mut data, wormhole_data.dst_max_gas_price_in_wei_for_relayer);
        serde::serialize_u256(&mut data, wormhole_data.wormhole_fee);
        serde::serialize_vector_with_length(&mut data, wormhole_data.dst_so_diamond);
        data
    }

    public fun decode_normalized_wormhole_data(data: &vector<u8>): NormalizedWormholeData {
        let len = vector::length(data);
        assert!(len > 0, EINVALID_LENGTH);
        let index = 0;
        let next_len;

        next_len = 2;
        let dst_wormhole_chain_id = serde::deserialize_u16(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 32;
        let dst_max_gas_price_in_wei_for_relayer = serde::deserialize_u256(
            &serde::vector_slice(data, index, index + next_len)
        );
        index = index + next_len;

        next_len = 32;
        let wormhole_fee = serde::deserialize_u256(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        next_len = 8 + serde::get_vector_length(&mut serde::vector_slice(data, index, index + 8));
        let dst_so_diamond = serde::deserialize_vector_with_length(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        assert!(index == len, EINVALID_LENGTH);

        NormalizedWormholeData {
            dst_wormhole_chain_id,
            dst_max_gas_price_in_wei_for_relayer,
            wormhole_fee,
            dst_so_diamond
        }
    }

    /// CrossData
    // 1. dst_max_gas_price INTER_DELIMITER
    // 2. dst_max_gas INTER_DELIMITER
    // 3. transactionId(SoData) INTER_DELIMITER
    // 4. receiver(SoData) INTER_DELIMITER
    // 5. receivingAssetId(SoData) INTER_DELIMITER
    // 6. swapDataLength(u8) INTER_DELIMITER
    // 7. callTo(SwapData) INTER_DELIMITER
    // 8. sendingAssetId(SwapData) INTER_DELIMITER
    // 9. receivingAssetId(SwapData) INTER_DELIMITER
    // 10. callData(SwapData)
    public fun encode_wormhole_payload(
        dst_max_gas_price: U256,
        dst_max_gas: U256,
        so_data: NormalizedSoData,
        swap_data_dst: vector<NormalizedSwapData>
    ): vector<u8> {
        let data = vector::empty<u8>();

        let cache = vector::empty();
        serialize_u256_with_hex_str(&mut cache, dst_max_gas_price);
        serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);


        let cache = vector::empty();
        serialize_u256_with_hex_str(&mut cache, dst_max_gas);
        serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_transaction_id(so_data);
        serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_receiver(so_data);
        serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_receiving_asset_id(so_data);
        serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let swap_len = vector::length(&swap_data_dst);
        if (swap_len > 0) {
            let cache = vector::empty();
            serialize_u256_with_hex_str(&mut cache, u256::from_u64(swap_len));
            serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);
        };

        vector::reverse(&mut swap_data_dst);
        while (!vector::is_empty(&swap_data_dst)) {
            let d = vector::pop_back(&mut swap_data_dst);

            let cache = cross::swap_call_to(d);
            serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_sending_asset_id(d);
            serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_receiving_asset_id(d);
            serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_call_data(d);
            serialize_u16(&mut data, u16::from_u64(vector::length(&cache)));
            vector::append(&mut data, cache);
        };
        data
    }

    public fun vector_copy(buf: &vector<u8>): vector<u8> {
        let data = vector::empty<u8>();
        let i = 0;
        while (i < vector::length(buf)) {
            vector::push_back(&mut data, *vector::borrow(buf, i));
            i = i + 1;
        };
        data
    }

    /// CrossData
    // 1. dst_max_gas_price INTER_DELIMITER
    // 2. dst_max_gas INTER_DELIMITER
    // 3. transactionId(SoData) INTER_DELIMITER
    // 4. receiver(SoData) INTER_DELIMITER
    // 5. receivingAssetId(SoData) INTER_DELIMITER
    // 6. swapDataLength(u8) INTER_DELIMITER
    // 7. callTo(SwapData) INTER_DELIMITER
    // 8. sendingAssetId(SwapData) INTER_DELIMITER
    // 9. receivingAssetId(SwapData) INTER_DELIMITER
    // 10. callData(SwapData)
    public fun decode_wormhole_payload(data: &vector<u8>): (U256, U256, NormalizedSoData, vector<NormalizedSwapData>) {
        let len = vector::length(data);
        assert!(len > 0, EINVALID_LENGTH);

        let index = 0;
        let next_len;

        next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
        index = index + 1;
        let dst_max_gas_price = serde::deserialize_u256_with_hex_str(
            &serde::vector_slice(data, index, index + next_len)
        );
        index = index + next_len;

        next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
        index = index + 1;
        let dst_max_gas = serde::deserialize_u256_with_hex_str(&serde::vector_slice(data, index, index + next_len));
        index = index + next_len;

        // SoData
        next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
        index = index + 1;
        let so_transaction_id = serde::vector_slice(data, index, index + next_len);
        index = index + next_len;

        next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
        index = index + 1;
        let so_receiver = serde::vector_slice(data, index, index + next_len);
        index = index + next_len;

        next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
        index = index + 1;
        let so_receiving_asset_id = serde::vector_slice(data, index, index + next_len);
        index = index + next_len;
        let so_data = cross::padding_so_data(so_transaction_id, so_receiver, so_receiving_asset_id);

        // Skip len
        if (index < len) {
            next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
            index = index + 1;
            index = index + next_len;
        };

        // Swap data
        let swap_data = vector::empty<NormalizedSwapData>();
        while (index < len) {
            next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
            index = index + 1;
            let swap_call_to = serde::vector_slice(data, index, index + next_len);
            index = index + next_len;

            next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
            index = index + 1;
            let swap_sending_asset_id = serde::vector_slice(data, index, index + next_len);
            index = index + next_len;

            next_len = (serde::deserialize_u8(&mut serde::vector_slice(data, index, index + 1)) as u64);
            index = index + 1;
            let swap_receiving_asset_id = serde::vector_slice(data, index, index + next_len);
            index = index + next_len;

            next_len = u16::to_u64(serde::deserialize_u16(&mut serde::vector_slice(data, index, index + 2)));
            index = index + 2;
            let swap_call_data = serde::vector_slice(data, index, index + next_len);
            index = index + next_len;

            vector::push_back(&mut swap_data,
                padding_swap_data(
                    swap_call_to,
                    swap_sending_asset_id,
                    swap_receiving_asset_id,
                    swap_call_data));
        };
        (dst_max_gas_price, dst_max_gas, so_data, swap_data)
    }

    #[test_only]
    public fun construct_normalized_wormhole_data(
        dst_wormhole_chain_id: U16,
        dst_max_gas_price_in_wei_for_relayer: U256,
        wormhole_fee: U256,
        dst_so_diamond: vector<u8>
    ): NormalizedWormholeData {
        NormalizedWormholeData {
            dst_wormhole_chain_id,
            dst_max_gas_price_in_wei_for_relayer,
            wormhole_fee,
            dst_so_diamond,
        }
    }

    #[test]
    fun test_serde_wormhole_data() {
        let wormhole_data = NormalizedWormholeData {
            dst_wormhole_chain_id: u16::from_u64(1),
            dst_max_gas_price_in_wei_for_relayer: u256::from_u64(10000),
            wormhole_fee: u256::from_u64(2389),
            dst_so_diamond: x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        };
        let encode_data = encode_normalized_wormhole_data(wormhole_data);

        let data = x"00010000000000000000000000000000000000000000000000000000000000002710000000000000000000000000000000000000000000000000000000000000095500000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af";
        assert!(data == encode_data, 1);
        assert!(decode_normalized_wormhole_data(&data) == wormhole_data, 1);
    }

    #[test]
    fun test_serde_wormhole_payload() {
        let data = x"00000000000000204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed00000000000000142da7e3a7f21cce79efeb66f3b082196ea0a8b9af0001000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00020000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000000000000000000000000000000000000000000000005f5e100";
        let so_data = cross::decode_normalized_so_data(&data);
        let data = x"000000000000000200000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c8100000000000000204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c81000000000000001a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e00000000000000163078313a3a6f6d6e695f6272696467653a3a5842544300000000000000000000000000000000000000000000000000000002127b390000000000000000583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c617465640000000000000014957eb0316f02ba4a9de3d308742eefd44a3c17190000000000000014957eb0316f02ba4a9de3d308742eefd44a3c171900000000000000142514895c72f50d8bd4b4f9b1110f0d6bd2c975260000000000000014143db3ceefbdfe5631add3e50f7614b6ba708ba700000000000000000000000000000000000000000000000000000001caf4ad0000000000000000146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7";
        let swap_data = cross::decode_normalized_swap_data(&data);
        let dst_max_gas_price = u256::from_u64(10000);
        let dst_max_gas = u256::from_u64(59);

        // Not swap
        let encode_data = encode_wormhole_payload(dst_max_gas_price, dst_max_gas, so_data, vector::empty());
        let data = x"022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c1719";
        assert!(data == encode_data, 1);
        let (v1, v2, v3, v4) = decode_wormhole_payload(&data);
        assert!(v1 == dst_max_gas_price, 1);
        assert!(v2 == dst_max_gas, 1);
        assert!(v3 == padding_so_data(
            cross::so_transaction_id(so_data),
            cross::so_receiver(so_data),
            cross::so_receiving_asset_id(so_data)), 1);
        assert!(v4 == vector::empty(), 1);


        // With swap
        let encode_data = encode_wormhole_payload(dst_max_gas_price, dst_max_gas, so_data, swap_data);
        let data = x"022710013b204450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed142da7e3a7f21cce79efeb66f3b082196ea0a8b9af14957eb0316f02ba4a9de3d308742eefd44a3c17190102204e9fce03284c0ce0b86c88dd5a46f050cad2f4f33c4cdd29d98f501868558c811a3078313a3a6170746f735f636f696e3a3a4170746f73436f696e163078313a3a6f6d6e695f6272696467653a3a5842544300583078346539666365303332383463306365306238366338386464356134366630353063616432663466333363346364643239643938663530313836383535386338313a3a6375727665733a3a556e636f7272656c6174656414957eb0316f02ba4a9de3d308742eefd44a3c1719142514895c72f50d8bd4b4f9b1110f0d6bd2c9752614143db3ceefbdfe5631add3e50f7614b6ba708ba700146ce9e2c8b59bbcf65da375d3d8ab503c8524caf7";
        assert!(data == encode_data, 1);
        let (v1, v2, v3, v4) = decode_wormhole_payload(&data);

        let decode_swap_data = vector::empty<NormalizedSwapData>();
        let i = 0;
        while (i < vector::length(&v4)) {
            vector::push_back(&mut decode_swap_data, padding_swap_data(
                cross::swap_call_to(*vector::borrow(&swap_data, i)),
                cross::swap_sending_asset_id(*vector::borrow(&swap_data, i)),
                cross::swap_receiving_asset_id(*vector::borrow(&swap_data, i)),
                cross::swap_call_data(*vector::borrow(&swap_data, i))
            ));
            i = i + 1;
        } ;

        assert!(v1 == dst_max_gas_price, 1);
        assert!(v2 == dst_max_gas, 1);
        assert!(v3 == padding_so_data(
            cross::so_transaction_id(so_data),
            cross::so_receiver(so_data),
            cross::so_receiving_asset_id(so_data)), 1);
        assert!(v4 == decode_swap_data, 1);
    }
}
