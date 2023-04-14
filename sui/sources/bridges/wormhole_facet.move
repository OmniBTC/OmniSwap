module omniswap::wormhole_facet {
    use wormhole::state;
    use wormhole::external_address;

    use token_bridge::complete_transfer_with_payload;
    use token_bridge::transfer_with_payload;

    use omniswap::cross;
    use omniswap::cross::{NormalizedSoData, NormalizedSwapData, padding_swap_data};
    use omniswap::so_fee_wormhole;
    use omniswap::swap::right_type;
    #[test_only]
    use omniswap::cross::padding_so_data;
    use sui::table::Table;
    use sui::object::UID;
    use wormhole::emitter::{EmitterCap};
    use sui::tx_context::TxContext;
    use sui::transfer;
    use sui::object;
    use sui::tx_context;
    use wormhole::emitter;
    use sui::table;
    use std::vector;
    use omniswap::serde;
    use omniswap::so_fee_wormhole::PriceManager;
    use wormhole::state::State as WormholeState;
    use token_bridge::state::State as TokenBridgeState;
    use sui::sui::SUI;
    use sui::coin::Coin;
    use sui::coin;
    use token_bridge::transfer_tokens_with_payload;
    use wormhole::bytes32;
    use sui::clock::Clock;
    use sui::event;


    const RAY: u64 = 100000000;

    const U64_MAX: u64 = 18446744073709551615;

    // Data delimiter, represent ";"
    const INTER_DELIMITER: u8 = 59;

    /// Errors Code
    const ENOT_DEPLOYED_ADDRESS: u64 = 0;

    const EHAS_INITIALIZE: u64 = 1;

    const ENOT_INITIALIZE: u64 = 2;

    const EINVALID_LENGTH: u64 = 3;

    const EINVALID_ACCOUNT: u64 = 4;

    const EINVALID_CHAIN_ID: u64 = 5;

    const ECHECK_FEE_FAIL: u64 = 6;

    const EAMOUNT_NOT_ENOUGH: u64 = 7;

    const EAMOUNT_MUST_ZERO: u64 = 8;

    /// Storage

    /// The so fee of cross token
    struct WormholeFee has key {
        id: UID,
        fee: u64,
        beneficiary: address
    }

    struct Storage has key {
        id: UID,
        // wormhole emitter capability
        emitter_cap: EmitterCap,
        // current wormhole chain id, sui 21
        src_wormhole_chain_id: u16,
        // actual relayer fee scale factor
        actual_reserve: u64,
        // estimate relayer fee scale factor
        estimate_reserve: u64,
        // target chain minimum consumption of gas
        dst_base_gas: Table<u16, u256>,
        // target chain gas per bytes
        dst_gas_per_bytes: Table<u16, u256>,
    }


    /// Some parameters needed to use wormhole
    struct NormalizedWormholeData has drop, copy {
        // destination wormhole chain id
        dst_wormhole_chain_id: u16,
        // gas price of the target chain
        dst_max_gas_price_in_wei_for_relayer: u256,
        // payment required for aptos coin
        wormhole_fee: u256,
        // destination chain sodiamond address
        dst_so_diamond: vector<u8>,
    }

    /// Own wormhole emitter capability
    struct WormholeFacetManager has key {
        id: UID,
        owner: address
    }

    /// Events

    struct TransferFromWormholeEvent has copy, drop {
        src_wormhole_chain_id: u16,
        dst_wormhole_chain_id: u16,
        sequence: u64
    }

    struct SoTransferStarted has copy, drop {
        transaction_id: vector<u8>,
    }

    struct SoTransferCompleted has copy, drop {
        transaction_id: vector<u8>,
        actual_receiving_amount: u64,
    }

    fun init(ctx: &mut TxContext) {
        transfer::share_object(WormholeFacetManager {
            id: object::new(ctx),
            owner: tx_context::sender(ctx)
        })
    }


    /// Helpers
    public entry fun transfer_owner(facet_manager: &mut WormholeFacetManager, to: address, ctx: &mut TxContext) {
        assert!(tx_context::sender(ctx) == facet_manager.owner, EINVALID_ACCOUNT);
        facet_manager.owner = to;
    }

    public entry fun transfer_beneficiary(wormhole_fee: &mut WormholeFee, to: address, ctx: &mut TxContext) {
        assert!(wormhole_fee.beneficiary == tx_context::sender(ctx), EINVALID_ACCOUNT);
        wormhole_fee.beneficiary = to;
    }

    public fun merge_coin<CoinType>(
        coins: vector<Coin<CoinType>>,
        amount: u64,
        ctx: &mut TxContext
    ): Coin<CoinType> {
        let len = vector::length(&coins);
        if (len > 0) {
            vector::reverse(&mut coins);
            let base_coin = vector::pop_back(&mut coins);
            while (!vector::is_empty(&coins)) {
                coin::join(&mut base_coin, vector::pop_back(&mut coins));
            };
            vector::destroy_empty(coins);
            let sum_amount = coin::value(&base_coin);
            let split_amount = amount;
            if (amount == U64_MAX) {
                split_amount = sum_amount;
            };
            assert!(sum_amount >= split_amount, EAMOUNT_NOT_ENOUGH);
            if (coin::value(&base_coin) > split_amount) {
                let split_coin = coin::split(&mut base_coin, split_amount, ctx);
                transfer::public_transfer(base_coin, tx_context::sender(ctx));
                split_coin
            }else {
                base_coin
            }
        }else {
            vector::destroy_empty(coins);
            assert!(amount == 0, EAMOUNT_MUST_ZERO);
            coin::zero<CoinType>(ctx)
        }
    }

    public entry fun set_so_fees(wormhole_fee: &mut WormholeFee, fee: u64, ctx: &mut TxContext)  {
        assert!(wormhole_fee.beneficiary == tx_context::sender(ctx), EINVALID_ACCOUNT);
        wormhole_fee.fee = fee;
    }

    public fun get_so_fees(wormhole_fee: &mut WormholeFee): u64 {
        wormhole_fee.fee
    }

    /// Inits

    /// Set the wormhole chain id used by the current chain
    public entry fun init_wormhole(facet_manager: &mut WormholeFacetManager, state: &mut WormholeState,wormhole_chain_id: u16, ctx: &mut TxContext) {
        assert!(tx_context::sender(ctx) == facet_manager.owner, ENOT_DEPLOYED_ADDRESS);
        let deployer = tx_context::sender(ctx);
        transfer::share_object(Storage {
            id: object::new(ctx),
            emitter_cap: emitter::new(state, ctx),
            src_wormhole_chain_id: wormhole_chain_id,
            actual_reserve: 0,
            estimate_reserve: 0,
            dst_base_gas: table::new(ctx),
            dst_gas_per_bytes: table::new(ctx),
        });
        transfer::share_object(WormholeFee {
            id: object::new(ctx),
            beneficiary: deployer,
            fee: 0
        });
    }


    /// Set relayer fee scale factor
    public entry fun set_wormhole_reserve(
        facet_manager: &mut WormholeFacetManager,
        storage: &mut Storage,
        actual_reserve: u64,
        estimate_reserve: u64,
        ctx: &mut TxContext
    ) {
        assert!(facet_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);

        storage.actual_reserve = actual_reserve;
        storage.estimate_reserve = estimate_reserve;
    }

    /// Set destination chain's minimum gas and gas per bytes
    public entry fun set_wormhole_gas(
        storage: &mut Storage,
        facet_manager: &mut WormholeFacetManager,
        dst_wormhole_chain_id: u16,
        base_gas: u256,
        gas_per_bytes: u256,
        ctx: &mut TxContext
    ) {
        assert!(facet_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);
        if (table::contains(&storage.dst_base_gas, dst_wormhole_chain_id)) {
            table::remove(&mut storage.dst_base_gas, dst_wormhole_chain_id);
        };
        if (table::contains(&storage.dst_gas_per_bytes, dst_wormhole_chain_id)) {
            table::remove(&mut storage.dst_gas_per_bytes, dst_wormhole_chain_id);
        };
        table::add(&mut storage.dst_base_gas, dst_wormhole_chain_id, base_gas);
        table::add(&mut storage.dst_gas_per_bytes, dst_wormhole_chain_id, gas_per_bytes);
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
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        so_data: vector<u8>,
        _swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        brige_fee_coins: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);
        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, _, dst_max_gas) = check_relayer_fee(storage,wormhole_state,price_manager ,so_data, wormhole_data, swap_data_dst);
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let brigde_fees = merge_coin(brige_fee_coins, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut brigde_fees, state::message_fee(wormhole_state), ctx);
        let relay_fee_coin = brigde_fees;
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        // let sequence: u64;
        // if (vector::length(&swap_data_src) > 0) {
        //     let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);
        //     if (vector::length(&swap_data_src) == 1) {
        //         let coin_y = swap::swap_two_by_account<X, Y>(account, swap_data_src);
        //         sequence = transfer_tokens::transfer_tokens_with_payload(
        //             emitter_cap,
        //             coin_y,
        //             wormhole_fee,
        //             wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
        //             external_address::from_bytes(wormhole_data.dst_so_diamond),
        //             0,
        //             payload
        //         );
        //     }else if (vector::length(&swap_data_src) == 2) {
        //         let coin_z = swap::swap_three_by_account<X, Y, Z>(account, swap_data_src);
        //         sequence = transfer_tokens::transfer_tokens_with_payload(
        //             emitter_cap,
        //             coin_z,
        //             wormhole_fee,
        //             wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
        //             external_address::from_bytes(wormhole_data.dst_so_diamond),
        //             0,
        //             payload
        //         );
        //     }else if (vector::length(&swap_data_src) == 3) {
        //         let coin_m = swap::swap_four_by_account<X, Y, Z, M>(account, swap_data_src);
        //         sequence = transfer_tokens::transfer_tokens_with_payload(
        //             emitter_cap,
        //             coin_m,
        //             wormhole_fee,
        //             wormhole_u16::from_u64(u16::to_u64(wormhole_data.dst_wormhole_chain_id)),
        //             external_address::from_bytes(wormhole_data.dst_so_diamond),
        //             0,
        //             payload
        //         );
        //     }else {
        //         abort EINVALID_LENGTH
        //     }
        // }else {
        let coin_val = (cross::so_amount(so_data) as u64);
        let coin_x = merge_coin(coins_x, coin_val, ctx);
        let (sequence, dust) = transfer_tokens_with_payload::transfer_tokens_with_payload(
            token_bridge_state,
            &storage.emitter_cap,
            wormhole_state,
            coin_x,
            wormhole_fee_coin,
            wormhole_data.dst_wormhole_chain_id,
            external_address::new(bytes32::from_bytes(wormhole_data.dst_so_diamond)),
            payload,
            0,
            clock
        );
        coin::destroy_zero(dust);
        // };
        //
        event::emit(
            SoTransferStarted {
                transaction_id: cross::so_transaction_id(so_data),
            }
        );

        event::emit(
            TransferFromWormholeEvent {
                src_wormhole_chain_id: storage.src_wormhole_chain_id,
                dst_wormhole_chain_id: wormhole_data.dst_wormhole_chain_id,
                sequence
            }
        );
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap<X, Y, Z, M>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    )  {
        let (coin_x, payload, _) = complete_transfer_with_payload::complete_transfer_with_payload<X>(
            token_bridge_state,
            &storage.emitter_cap,
            wormhole_state,
            vaa,
            clock,
            ctx
        );

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees(wormhole_fee) as u128) / (RAY as u128)) as u64);
        let beneficiary = wormhole_fee.beneficiary;
        if (so_fee > 0 && so_fee <= x_val) {
            let coin_fee = coin::split<X>(&mut coin_x, so_fee, ctx);
            transfer::public_transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, _) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        // if (vector::length(&swap_data_dst) > 0) {
        //     if (vector::length(&swap_data_dst) == 1) {
        //         let coin_y = swap::swap_two_by_coin<X, Y>(coin_x, swap_data_dst);
        //
        //         receiving_amount = coin::value(&coin_y);
        //         transfer(coin_y, receiver);
        //     }else if (vector::length(&swap_data_dst) == 2) {
        //         let coin_z = swap::swap_three_by_coin<X, Y, Z>(coin_x, swap_data_dst);
        //
        //         receiving_amount = coin::value(&coin_z);
        //         transfer(coin_z, receiver);
        //     }else if (vector::length(&swap_data_dst) == 3) {
        //         let coin_m = swap::swap_four_by_coin<X, Y, Z, M>(coin_x, swap_data_dst);
        //
        //         receiving_amount = coin::value(&coin_m);
        //         transfer(coin_m, receiver);
        //     }else {
        //         abort EINVALID_LENGTH
        //     }
        // }else {
        transfer::public_transfer(coin_x, receiver);
        // };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        )
    }

    /// To avoid wormhole payload data construction errors, lock the token and allow the owner to handle
    /// it manually.
    public entry fun complete_so_swap_by_admin<X, Y, Z, M>(
        storage: &mut Storage,
        facet_manager: &mut WormholeFacetManager,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        to: address,
        clock: &Clock,
        ctx: &mut TxContext
    )  {
        assert!(facet_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);
        let (coin_x, _, _) = complete_transfer_with_payload::complete_transfer_with_payload<X>(
            token_bridge_state,
            &storage.emitter_cap,
            wormhole_state,
            vaa,
            clock,
            ctx
        );

        let x_val = coin::value(&coin_x);
        let so_fee = (((x_val as u128) * (get_so_fees(wormhole_fee) as u128) / (RAY as u128)) as u64);
        let beneficiary = wormhole_fee.beneficiary;
        if (so_fee > 0 && so_fee <= x_val) {
            let coin_fee = coin::split<X>(&mut coin_x, so_fee, ctx);
            transfer::public_transfer(coin_fee, beneficiary);
        };

        transfer::public_transfer(coin_x, to);
    }

    // public entry fun complete_so_swap_by_emitter<X, Y, Z, M>(
    //     account: &signer,
    //     vaa: vector<u8>,
    //     to: address
    // ) acquires WormholeFacetManager, WormholeFee {
    //     assert!(is_initialize(), ENOT_INITIALIZE);
    //
    //     let emitter_cap = &borrow_global<WormholeFacetManager>(signer::address_of(account)).emitter_cap;
    //     let (coin_x, _) = complete_transfer_with_payload::submit_vaa<X>(vaa, emitter_cap);
    //
    //     let x_val = coin::value(&coin_x);
    //     let so_fee = (((x_val as u128) * (get_so_fees() as u128) / (RAY as u128)) as u64);
    //     let beneficiary = get_beneficiary_address();
    //     if (so_fee > 0 && so_fee <= x_val && is_transfer<X>(beneficiary)) {
    //         let coin_fee = coin::extract(&mut coin_x, so_fee);
    //         transfer(coin_fee, beneficiary);
    //     };
    //
    //     transfer(coin_x, to);
    // }

    /// Swap Helpers

    /// Ensure that there is a minimal cost to help Relayer complete transactions in the destination chain.
    public fun check_relayer_fee(
        storage: &mut Storage,
        state: &mut WormholeState,
        price_manager: &mut PriceManager,
        so_data: NormalizedSoData,
        wormhole_data: NormalizedWormholeData,
        swap_data_dst: vector<NormalizedSwapData>
    ): (bool, u64, u64, u256) {
        let actual_reserve = storage.actual_reserve;

        let ratio = so_fee_wormhole::get_price_ratio(price_manager, wormhole_data.dst_wormhole_chain_id);

        let dst_max_gas = estimate_complete_soswap_gas(
            storage,
            cross::encode_normalized_so_data(so_data),
            wormhole_data,
            cross::encode_normalized_swap_data(swap_data_dst)
        );
        let dst_fee = wormhole_data.dst_max_gas_price_in_wei_for_relayer * dst_max_gas;

        let one = (RAY as u256);
        let src_fee = dst_fee * (ratio as u256);
        src_fee = src_fee / one;
        src_fee = src_fee * (actual_reserve as u256);
        src_fee = src_fee / one;

        // Evm chain, decimal change
        src_fee = src_fee / 10000000000;

        let comsume_value = state::message_fee(state);

        if (right_type<SUI>(cross::so_sending_asset_id(so_data))) {
            comsume_value = comsume_value + (cross::so_amount(so_data) as u64);
        };

        let src_fee = (src_fee as u64);
        comsume_value = comsume_value + src_fee;

        let flag = false;
        let return_value = 0;

        let wormhole_fee = (wormhole_data.wormhole_fee as u64);
        if (comsume_value <= wormhole_fee) {
            flag = true;
            return_value = wormhole_fee - comsume_value;
        };
        (flag, src_fee, return_value, dst_max_gas)
    }

    public fun estimate_complete_soswap_gas(
        storage: &mut Storage,
        so_data: vector<u8>,
        wormhole_data: NormalizedWormholeData,
        swap_data_dst: vector<u8>
    ): u256 {
        let len = 32 + 32 + 1 + vector::length(&so_data) + 1 + vector::length(&swap_data_dst);
        if (table::contains(&storage.dst_base_gas, wormhole_data.dst_wormhole_chain_id)) {
            let dst_base_gas = *table::borrow(&storage.dst_base_gas, wormhole_data.dst_wormhole_chain_id);
            let dst_gas_per_bytes = *table::borrow(&storage.dst_gas_per_bytes, wormhole_data.dst_wormhole_chain_id);
            dst_base_gas + dst_gas_per_bytes * (len as u256)
        }else {
            0
        }
    }

    /// Query gas
    public fun get_dst_gas(storage: &mut Storage, dst_wormhole_chain_id: u16): (u256, u256) {
        if (table::contains(&storage.dst_base_gas, dst_wormhole_chain_id)) {
            let dst_base_gas = *table::borrow(&storage.dst_base_gas, dst_wormhole_chain_id);
            let dst_gas_per_bytes = *table::borrow(&storage.dst_gas_per_bytes, dst_wormhole_chain_id);
            (dst_base_gas, dst_gas_per_bytes)
        }else {
            (0, 0)
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
        dst_max_gas_price: u256,
        dst_max_gas: u256,
        so_data: NormalizedSoData,
        swap_data_dst: vector<NormalizedSwapData>
    ): vector<u8> {
        let data = vector::empty<u8>();

        let cache = vector::empty();
        serde::serialize_u256_with_hex_str(&mut cache, dst_max_gas_price);
        serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);


        let cache = vector::empty();
        serde::serialize_u256_with_hex_str(&mut cache, dst_max_gas);
        serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_transaction_id(so_data);
        serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_receiver(so_data);
        serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let cache = cross::so_receiving_asset_id(so_data);
        serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
        vector::append(&mut data, cache);

        let swap_len = vector::length(&swap_data_dst);
        if (swap_len > 0) {
            let cache = vector::empty();
            serde::serialize_u256_with_hex_str(&mut cache, (swap_len as u256));
            serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);
        };

        vector::reverse(&mut swap_data_dst);
        while (!vector::is_empty(&swap_data_dst)) {
            let d = vector::pop_back(&mut swap_data_dst);

            let cache = cross::swap_call_to(d);
            serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_sending_asset_id(d);
            serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_receiving_asset_id(d);
            serde::serialize_u8(&mut data, (vector::length(&cache) as u8));
            vector::append(&mut data, cache);

            let cache = cross::swap_call_data(d);
            serde::serialize_u16(&mut data, (vector::length(&cache) as u16));
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
    public fun decode_wormhole_payload(data: &vector<u8>): (u256, u256, NormalizedSoData, vector<NormalizedSwapData>) {
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

            next_len = (serde::deserialize_u16(&mut serde::vector_slice(data, index, index + 2)) as u64);
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
        dst_wormhole_chain_id: u16,
        dst_max_gas_price_in_wei_for_relayer: u256,
        wormhole_fee: u256,
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
            dst_wormhole_chain_id: 1,
            dst_max_gas_price_in_wei_for_relayer: 10000,
            wormhole_fee: 2389,
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
        let dst_max_gas_price = 10000;
        let dst_max_gas = 59;

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
