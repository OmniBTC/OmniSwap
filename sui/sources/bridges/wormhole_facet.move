module omniswap::wormhole_facet {
    use std::ascii::String;
    use std::bcs;
    use std::type_name;
    use std::vector;

    use cetus_clmm::config::GlobalConfig;
    use cetus_clmm::pool::Pool as CetusPool;
    use deepbook::clob::Pool as DeepbookPool;
    use deepbook::clob_v2;
    use deepbook::clob_v2::Pool as DeepbookV2Pool;
    use deepbook::custodian_v2;
    use deepbook::custodian_v2::AccountCap;
    use omniswap::cross::{Self, NormalizedSoData, NormalizedSwapData, padding_swap_data};
    use omniswap::serde;
    use omniswap::so_fee_wormhole::{Self, PriceManager};
    use omniswap::swap;
    use sui::clock::Clock;
    use sui::coin::{Self, Coin};
    use sui::dynamic_field;
    use sui::event;
    use sui::object::{Self, ID, UID};
    use sui::sui::SUI;
    use sui::table::{Self, Table};
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};
    use token_bridge::complete_transfer_with_payload;
    use token_bridge::state::{Self as bridge_state, State as TokenBridgeState};
    use token_bridge::transfer_tokens_with_payload;
    use token_bridge::transfer_with_payload::{Self, TransferWithPayload};
    use token_bridge::vaa as bridge_vaa;
    use wormhole::emitter::{Self, EmitterCap};
    use wormhole::publish_message;
    use wormhole::state::{Self, State as WormholeState};
    use wormhole::vaa;

    #[test_only]
    use omniswap::cross::padding_so_data;
    use std::ascii;

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

    const EAMOUNT_NOT_NEAT: u64 = 9;

    const ETYPE: u64 = 10;

    const ESWAP_LENGTH: u64 = 11;

    const EMULTISWAP_STEP: u64 = 12;

    const ENOT_POOL_LOT_SIZE: u64 = 13;

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

    /// Deepbook v2 storage
    struct DeepbookV2Storage has key {
        id: UID,
        // deepbook_v2 account cap
        account_cap: AccountCap,
        // deepbook_v2 client order id
        client_order_id: u64
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
        owner: address,
        relayer: address
    }

    /// Multi swap result
    struct MultiSwapData<phantom X> {
        receiver: address,
        input_coin: Coin<X>,
        left_swap_data: vector<NormalizedSwapData>,
    }

    /// Multi src data
    struct MultiSrcData {
        wormhole_fee_coin: Coin<SUI>,
        wormhole_data: NormalizedWormholeData,
        relay_fee: u64,
        payload: vector<u8>,
    }

    /// Multi dst data
    struct MultiDstData {
        tx_id: vector<u8>,
    }

    /// DeepBookV2 lot size
    struct LotSize has store {
        data: Table<address, u64>
    }

    /// GenericData
    struct GenericData {
        tx_id: vector<u8>,
        from_asset_id: String,
        from_amount: u64,
    }

    /// Events

    struct TransferFromWormholeEvent has copy, drop {
        src_wormhole_chain_id: u16,
        dst_wormhole_chain_id: u16,
        sequence: u64
    }


    struct SoSwappedGeneric has copy, drop {
        to_asset_id: String,
        to_amount: u64,
        receiver: address
    }

    struct SoSwappedGenericV2 has copy, drop {
        transaction_id: vector<u8>,
        from_asset_id: String,
        from_amount: u64,
        to_asset_id: String,
        to_amount: u64,
        receiver: address
    }

    struct SoTransferStarted has copy, drop {
        transaction_id: vector<u8>,
    }

    struct SoTransferCompleted has copy, drop {
        transaction_id: vector<u8>,
        actual_receiving_amount: u64,
    }

    struct SrcAmount has copy, drop {
        relayer_fee: u64,
        cross_amount: u64
    }

    struct DstAmount has copy, drop {
        so_fee: u64
    }

    struct OrignEvnet has copy, drop {
        tx_sender: address,
        so_receiver: vector<u8>,
        token: String,
        amount: u64
    }

    struct RelayerEvnet has copy, drop {
        status: String,
        receiving_asset_id: String,
        receiving_amount: u64,
    }

    struct RelayerEvnetV2 has copy, drop {
        transaction_id: vector<u8>,
        status: String,
        receiving_asset_id: String,
        receiving_amount: u64,
    }

    struct SwapEvent has copy, drop {
        src_token: String,
        dst_token: String,
        src_input_amount: u64,
        dst_output_amount: u64,
        src_remain_amount: u64
    }

    fun init(ctx: &mut TxContext) {
        transfer::share_object(WormholeFacetManager {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
            relayer: tx_context::sender(ctx),
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

    public entry fun set_relayer(facet_manager: &mut WormholeFacetManager, relayer: address, ctx: &mut TxContext) {
        assert!(tx_context::sender(ctx) == facet_manager.owner, EINVALID_ACCOUNT);
        facet_manager.relayer = relayer;
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

    public fun process_left_coin<X>(coin_x: Coin<X>, receiver: address) {
        if (coin::value(&coin_x) > 0) {
            transfer::public_transfer(coin_x, receiver);
        } else {
            coin::destroy_zero(coin_x);
        }
    }

    public entry fun set_so_fees(wormhole_fee: &mut WormholeFee, fee: u64, ctx: &mut TxContext) {
        assert!(wormhole_fee.beneficiary == tx_context::sender(ctx), EINVALID_ACCOUNT);
        wormhole_fee.fee = fee;
    }

    public fun get_so_fees(wormhole_fee: &mut WormholeFee): u64 {
        wormhole_fee.fee
    }

    /// Inits

    /// Set deepbook_v2 account cap
    public entry fun init_deepbook_v2(
        facet_manager: &mut WormholeFacetManager,
        ctx: &mut TxContext
    ) {
        assert!(tx_context::sender(ctx) == facet_manager.owner, ENOT_DEPLOYED_ADDRESS);
        let owner_account = clob_v2::create_account(ctx);
        let deepbook_account = custodian_v2::create_child_account_cap(&owner_account, ctx);
        transfer::public_transfer(owner_account, facet_manager.owner);
        transfer::share_object(
            DeepbookV2Storage {
                id: object::new(ctx),
                account_cap: deepbook_account,
                client_order_id: 0
            }
        )
    }

    /// Add deepbook lot size
    entry fun add_deepbook_v2_lot_size(
        facet_manager: &WormholeFacetManager,
        deepbook_v2_storage: &mut DeepbookV2Storage,
        pool_ids: vector<address>,
        lot_sizes: vector<u64>,
        ctx: &mut TxContext
    ) {
        assert!(tx_context::sender(ctx) == facet_manager.owner, ENOT_DEPLOYED_ADDRESS);
        assert!(vector::length(&pool_ids) == vector::length(&lot_sizes), EINVALID_LENGTH);
        if (!dynamic_field::exists_(&deepbook_v2_storage.id, b"LotSize")) {
            dynamic_field::add(&mut deepbook_v2_storage.id, b"LotSize", LotSize {
                data: table::new(ctx)
            });
        };
        let storage = &mut dynamic_field::borrow_mut<vector<u8>, LotSize>(&mut deepbook_v2_storage.id, b"LotSize").data;
        while (!vector::is_empty(&pool_ids)) {
            let pool_id = vector::pop_back(&mut pool_ids);
            let lot_size = vector::pop_back(&mut lot_sizes);
            if (table::contains(storage, pool_id)) {
                table::remove(storage, pool_id);
            };
            table::add(storage, pool_id, lot_size);
        }
    }

    public fun get_deepbook_v2_lot_size(
        deepbook_v2_storage: &DeepbookV2Storage,
        pool_id: ID
    ): u64 {
        let pool_id = object::id_to_address(&pool_id);
        let storage = &dynamic_field::borrow<vector<u8>, LotSize>(&deepbook_v2_storage.id, b"LotSize").data;
        assert!(table::contains(storage, pool_id), ENOT_POOL_LOT_SIZE);
        *table::borrow(storage, pool_id)
    }

    /// Set the wormhole chain id used by the current chain
    public entry fun init_wormhole(
        facet_manager: &mut WormholeFacetManager,
        state: &mut WormholeState,
        wormhole_chain_id: u16,
        ctx: &mut TxContext
    ) {
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

    fun tranfer_token<X>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        coin_x: Coin<X>,
        wormhole_data: NormalizedWormholeData,
        payload: vector<u8>,
        wormhole_fee_coin: Coin<SUI>
    ): (u64, Coin<X>) {
        let asset_info = bridge_state::verified_asset(token_bridge_state);

        let (
            prepared_transfer,
            dust
        ) =
            transfer_tokens_with_payload::prepare_transfer(
                &storage.emitter_cap,
                asset_info,
                coin_x,
                wormhole_data.dst_wormhole_chain_id,
                wormhole_data.dst_so_diamond,
                payload,
                0,
            );

        let prepared_msg = transfer_tokens_with_payload::transfer_tokens_with_payload(
            token_bridge_state,
            prepared_transfer
        );

        let sequence = publish_message::publish_message(
            wormhole_state,
            wormhole_fee_coin,
            prepared_msg,
            clock
        );
        (sequence, dust)
    }

    public entry fun so_swap_without_swap<X>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        assert!(vector::length(&swap_data_src) == 0, ESWAP_LENGTH);
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_val
            }
        );

        let coin_x = merge_coin(coins_x, coin_val, ctx);

        let bridge_amount = coin::value(&coin_x);
        let (sequence, dust) = tranfer_token<X>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_x,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(dust, tx_context::sender(ctx));

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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized, and all of this data can be serialized and
    /// deserialized in the methods found here.
    public entry fun so_swap_for_deepbook_base_asset<X, Y>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookPool<X, Y>,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_y: vector<Coin<Y>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: coin_val
            }
        );

        let coin_y = merge_coin(coins_y, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_deepbook<X, Y>(
            pool_xy,
            coin_y,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        let bridge_amount = coin::value(&coin_x);
        let (sequence, dust) = tranfer_token<X>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_x,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(left_coin_y, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));

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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    public entry fun so_swap_for_deepbook_quote_asset<X, Y>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookPool<X, Y>,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_val
            }
        );

        let coin_x = merge_coin(coins_x, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (letf_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_deepbook<X, Y>(
            pool_xy,
            coin_x,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        let bridge_amount = coin::value(&coin_y);
        let (sequence, dust) = tranfer_token<Y>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_y,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(letf_coin_x, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));

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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized, and all of this data can be serialized and
    /// deserialized in the methods found here.
    public entry fun so_swap_for_deepbook_v2_base_asset<X, Y>(
        storage: &mut Storage,
        wromhole_fee: &mut WormholeFee,
        price_manager: &mut PriceManager,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        deepbook_v2_storage: &mut DeepbookV2Storage,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_y: vector<Coin<Y>>,
        coins_sui: vector<Coin<SUI>>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: coin_val
            }
        );

        let coin_y = merge_coin(coins_y, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_deepbook_v2<X, Y>(
            pool_xy,
            coin_y,
            &deepbook_v2_storage.account_cap,
            deepbook_v2_storage.client_order_id,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;

        let bridge_amount = coin::value(&coin_x);
        let (sequence, dust) = tranfer_token<X>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_x,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(left_coin_y, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));

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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    public fun split_deepbook_coin<X>(
        deepbook_v2_storage: &DeepbookV2Storage,
        pool_xy: ID,
        input_coin: Coin<X>,
        ctx: &mut TxContext
    ): (Coin<X>, Coin<X>) {
        let lot_size = get_deepbook_v2_lot_size(
            deepbook_v2_storage,
            pool_xy
        );
        let coin_val = coin::value(&input_coin);
        let remain = coin_val % lot_size;
        let remain_coin = coin::split(&mut input_coin, remain, ctx);
        (input_coin, remain_coin)
    }

    public entry fun so_swap_for_deepbook_v2_quote_asset<X, Y>(
        storage: &mut Storage,
        wromhole_fee: &mut WormholeFee,
        price_manager: &mut PriceManager,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        wormhole_state: &mut WormholeState,
        deepbook_v2_storage: &mut DeepbookV2Storage,
        token_bridge_state: &mut TokenBridgeState,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_val
            }
        );

        let coin_x = merge_coin(coins_x, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (coin_x, remain_coin) = split_deepbook_coin(
            deepbook_v2_storage,
            object::id(pool_xy),
            coin_x,
            ctx
        );
        let (letf_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_deepbook_v2<X, Y>(
            pool_xy,
            coin_x,
            &deepbook_v2_storage.account_cap,
            deepbook_v2_storage.client_order_id,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;

        let bridge_amount = coin::value(&coin_y);
        let (sequence, dust) = tranfer_token<Y>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_y,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(letf_coin_x, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));
        process_left_coin(remain_coin, tx_context::sender(ctx));

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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized, and all of this data can be serialized and
    /// deserialized in the methods found here.
    public entry fun so_swap_for_cetus_base_asset<X, Y>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_y: vector<Coin<Y>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: coin_val
            }
        );

        let coin_y = merge_coin(coins_y, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_cetus<X, Y>(
            config,
            pool_xy,
            coin_y,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        let bridge_amount = coin::value(&coin_x);
        let (sequence, dust) = tranfer_token<X>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_x,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(left_coin_y, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));


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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    public entry fun so_swap_for_cetus_quote_asset<X, Y>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_val
            }
        );

        let coin_x = merge_coin(coins_x, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);

        assert!(vector::length(&swap_data_src) == 1, ESWAP_LENGTH);
        let (letf_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_cetus<X, Y>(
            config,
            pool_xy,
            coin_x,
            *vector::borrow(&swap_data_src, 0),
            clock,
            ctx
        );
        let bridge_amount = coin::value(&coin_y);
        let (sequence, dust) = tranfer_token<Y>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_y,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(letf_coin_x, tx_context::sender(ctx));
        process_left_coin(dust, tx_context::sender(ctx));


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

        event::emit(
            SrcAmount {
                relayer_fee: fee,
                cross_amount: bridge_amount
            }
        );
    }

    /// multi_swap_v2 -> multi_swap_for_cetus_base_asset -> complete_multi_swap
    public fun multi_swap_v2<X>(
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        coins_x: vector<Coin<X>>,
        ctx: &mut TxContext
    ): (MultiSwapData<X>, GenericData) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);
        let coin_amount = (cross::so_amount(so_data) as u64);
        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: bcs::to_bytes(&tx_context::sender(ctx)),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_amount
            }
        );

        let coin_x = merge_coin(coins_x, coin_amount, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = cross::decode_normalized_swap_data(&mut swap_data_src);
        assert!(vector::length(&swap_data_src) > 0, EMULTISWAP_STEP);

        let multi_swap_data = MultiSwapData<X> {
            receiver: tx_context::sender(ctx),
            input_coin: coin_x,
            left_swap_data: swap_data_src,
        };

        let generic_data = GenericData {
            tx_id: cross::so_transaction_id(so_data),
            from_asset_id: type_name::into_string(type_name::get<X>()),
            from_amount: coin_amount
        };
        (multi_swap_data, generic_data)
    }

    /// multi_swap -> multi_swap_for_cetus_base_asset -> complete_multi_swap
    public fun multi_swap<X>(
        _swap_data_src: vector<u8>,
        _coins_x: vector<Coin<X>>,
        _coin_amount: u64,
        _ctx: &mut TxContext
    ): MultiSwapData<X> {
        abort 0
    }

    /// so_multi_swap -> multi_swap_for_cetus_base_asset -> complete_multi_src_swap
    public fun so_multi_swap<X>(
        wormhole_state: &mut WormholeState,
        storage: &mut Storage,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ): (MultiSwapData<X>, MultiSrcData) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let (flag, fee, consume_value, dst_max_gas) = check_relayer_fee(
            storage,
            wormhole_state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        assert!(flag, ECHECK_FEE_FAIL);

        let payload = encode_wormhole_payload(
            wormhole_data.dst_max_gas_price_in_wei_for_relayer,
            dst_max_gas,
            so_data,
            swap_data_dst
        );

        let comsume_sui = merge_coin(coins_sui, consume_value, ctx);
        let relay_fee_coin = coin::split<SUI>(&mut comsume_sui, fee, ctx);
        let wormhole_fee_coin = coin::split<SUI>(&mut comsume_sui, state::message_fee(wormhole_state), ctx);
        transfer::public_transfer(relay_fee_coin, wromhole_fee.beneficiary);

        let coin_val = (cross::so_amount(so_data) as u64);
        assert!(coin::value(&comsume_sui) == 0, EAMOUNT_NOT_NEAT);
        coin::destroy_zero(comsume_sui);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: coin_val
            }
        );

        let coin_x = merge_coin(coins_x, coin_val, ctx);

        // X is quote asset, Y is base asset
        // use base asset to cross chain
        let swap_data_src = if (vector::is_empty(&swap_data_src)) {
            vector::empty<NormalizedSwapData>()
        }else {
            cross::decode_normalized_swap_data(&mut swap_data_src)
        };

        let multi_swap_data = MultiSwapData<X> {
            receiver: tx_context::sender(ctx),
            input_coin: coin_x,
            left_swap_data: swap_data_src,
        };

        let multi_src_data = MultiSrcData {
            wormhole_fee_coin,
            wormhole_data,
            relay_fee: fee,
            payload,
        };

        event::emit(
            SoTransferStarted {
                transaction_id: cross::so_transaction_id(so_data),
            }
        );

        (multi_swap_data, multi_src_data)
    }

    public fun multi_swap_for_deepbook_v2_base_asset<X, Y>(
        deepbook_v2_storage: &mut DeepbookV2Storage,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        multi_swap_data: MultiSwapData<Y>,
        clock: &Clock,
        ctx: &mut TxContext
    ): MultiSwapData<X> {
        assert!(vector::length(&multi_swap_data.left_swap_data) > 0, EMULTISWAP_STEP);
        let (receiver, coin_y, left_swap_data) = destroy_multi_swap_data(
            multi_swap_data
        );
        let swap_data = vector::remove(&mut left_swap_data, 0);

        let src_token = type_name::into_string(type_name::get<Y>());
        let dst_token = type_name::into_string(type_name::get<X>());
        let src_input_amount = coin::value(&coin_y);

        let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_deepbook_v2<X, Y>(
            pool_xy,
            coin_y,
            &deepbook_v2_storage.account_cap,
            deepbook_v2_storage.client_order_id,
            swap_data,
            clock,
            ctx
        );
        let dst_output_amount = coin::value(&coin_x);
        let src_remain_amount = coin::value(&left_coin_y);
        event::emit(
            SwapEvent {
                src_token,
                dst_token,
                src_input_amount,
                dst_output_amount,
                src_remain_amount
            }
        );

        deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;

        process_left_coin(left_coin_y, receiver);
        MultiSwapData<X> {
            receiver,
            input_coin: coin_x,
            left_swap_data,
        }
    }

    public fun multi_swap_for_deepbook_v2_quote_asset<X, Y>(
        deepbook_v2_storage: &mut DeepbookV2Storage,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        multi_swap_data: MultiSwapData<X>,
        clock: &Clock,
        ctx: &mut TxContext
    ): MultiSwapData<Y> {
        assert!(vector::length(&multi_swap_data.left_swap_data) > 0, EMULTISWAP_STEP);
        let (receiver, coin_x, left_swap_data) = destroy_multi_swap_data(
            multi_swap_data
        );
        let swap_data = vector::remove(&mut left_swap_data, 0);
        let (coin_x, remain_coin) = split_deepbook_coin(
            deepbook_v2_storage,
            object::id(pool_xy),
            coin_x,
            ctx
        );

        let src_token = type_name::into_string(type_name::get<X>());
        let dst_token = type_name::into_string(type_name::get<Y>());
        let src_input_amount = coin::value(&coin_x);
        let (left_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_deepbook_v2<X, Y>(
            pool_xy,
            coin_x,
            &deepbook_v2_storage.account_cap,
            deepbook_v2_storage.client_order_id,
            swap_data,
            clock,
            ctx
        );

        let dst_output_amount = coin::value(&coin_y);
        let src_remain_amount = coin::value(&left_coin_x) + coin::value(&remain_coin);
        event::emit(
            SwapEvent {
                src_token,
                dst_token,
                src_input_amount,
                dst_output_amount,
                src_remain_amount
            }
        );

        deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;

        process_left_coin(left_coin_x, receiver);
        process_left_coin(remain_coin, receiver);
        MultiSwapData<Y> {
            receiver,
            input_coin: coin_y,
            left_swap_data,
        }
    }

    public fun multi_swap_for_cetus_base_asset<X, Y>(
        global_config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        multi_swap_data: MultiSwapData<Y>,
        clock: &Clock,
        ctx: &mut TxContext
    ): MultiSwapData<X> {
        assert!(vector::length(&multi_swap_data.left_swap_data) > 0, EMULTISWAP_STEP);
        let (receiver, coin_y, left_swap_data) = destroy_multi_swap_data(
            multi_swap_data
        );
        let swap_data = vector::remove(&mut left_swap_data, 0);

        let src_token = type_name::into_string(type_name::get<Y>());
        let dst_token = type_name::into_string(type_name::get<X>());
        let src_input_amount = coin::value(&coin_y);

        let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_cetus<X, Y>(
            global_config,
            pool_xy,
            coin_y,
            swap_data,
            clock,
            ctx
        );

        let dst_output_amount = coin::value(&coin_x);
        let src_remain_amount = coin::value(&left_coin_y) ;
        event::emit(
            SwapEvent {
                src_token,
                dst_token,
                src_input_amount,
                dst_output_amount,
                src_remain_amount
            }
        );

        process_left_coin(left_coin_y, receiver);
        MultiSwapData<X> {
            receiver,
            input_coin: coin_x,
            left_swap_data,
        }
    }

    public fun multi_swap_for_cetus_quote_asset<X, Y>(
        global_config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        multi_swap_data: MultiSwapData<X>,
        clock: &Clock,
        ctx: &mut TxContext
    ): MultiSwapData<Y> {
        assert!(vector::length(&multi_swap_data.left_swap_data) > 0, EMULTISWAP_STEP);
        let (receiver, coin_x, left_swap_data) = destroy_multi_swap_data(
            multi_swap_data
        );
        let swap_data = vector::remove(&mut left_swap_data, 0);

        let src_token = type_name::into_string(type_name::get<X>());
        let dst_token = type_name::into_string(type_name::get<Y>());
        let src_input_amount = coin::value(&coin_x);

        let (left_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_cetus<X, Y>(
            global_config,
            pool_xy,
            coin_x,
            swap_data,
            clock,
            ctx
        );

        let dst_output_amount = coin::value(&coin_y);
        let src_remain_amount = coin::value(&left_coin_x);
        event::emit(
            SwapEvent {
                src_token,
                dst_token,
                src_input_amount,
                dst_output_amount,
                src_remain_amount
            }
        );

        process_left_coin(left_coin_x, receiver);
        MultiSwapData<Y> {
            receiver,
            input_coin: coin_y,
            left_swap_data,
        }
    }

    public fun complete_multi_swap<X>(
        multi_swap_data: MultiSwapData<X>,
    ) {
        assert!(vector::length(&multi_swap_data.left_swap_data) == 0, EMULTISWAP_STEP);
        let (receiver, coin_x, swap_data) = destroy_multi_swap_data(multi_swap_data);
        vector::destroy_empty(swap_data);
        event::emit(SoSwappedGeneric {
            to_asset_id: type_name::into_string(type_name::get<X>()),
            to_amount: coin::value(&coin_x),
            receiver
        });
        transfer::public_transfer(coin_x, receiver)
    }

    public fun complete_multi_swap_v2<X>(
        multi_swap_data: MultiSwapData<X>,
        generic_data: GenericData
    ) {
        assert!(vector::length(&multi_swap_data.left_swap_data) == 0, EMULTISWAP_STEP);
        let (receiver, coin_x, swap_data) = destroy_multi_swap_data(multi_swap_data);
        vector::destroy_empty(swap_data);
        let (tx_id, from_asset_id, from_amount) = destroy_generic_data(generic_data);
        event::emit(SoSwappedGenericV2 {
            transaction_id: tx_id,
            from_asset_id,
            from_amount,
            to_asset_id: type_name::into_string(type_name::get<X>()),
            to_amount: coin::value(&coin_x),
            receiver
        });
        transfer::public_transfer(coin_x, receiver)
    }

    public fun complete_multi_src_swap<X>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        multi_swap_data: MultiSwapData<X>,
        multi_src_data: MultiSrcData,
        clock: &Clock
    ) {
        assert!(vector::length(&multi_swap_data.left_swap_data) == 0, EMULTISWAP_STEP);
        let (receiver, coin_x, swap_data) = destroy_multi_swap_data(multi_swap_data);
        let (wormhole_fee_coin, wormhole_data, relay_fee, payload) = destroy_multi_src_data(multi_src_data);
        vector::destroy_empty(swap_data);
        let bridge_amount = coin::value(&coin_x);
        let (sequence, dust) = tranfer_token<X>(
            wormhole_state,
            token_bridge_state,
            storage,
            clock,
            coin_x,
            wormhole_data,
            payload,
            wormhole_fee_coin
        );
        bridge_amount = bridge_amount - coin::value(&dust);
        process_left_coin(dust, receiver);

        event::emit(
            TransferFromWormholeEvent {
                src_wormhole_chain_id: storage.src_wormhole_chain_id,
                dst_wormhole_chain_id: wormhole_data.dst_wormhole_chain_id,
                sequence
            }
        );

        event::emit(
            SrcAmount {
                relayer_fee: relay_fee,
                cross_amount: bridge_amount
            }
        );
    }

    fun destroy_multi_swap_data<X>(
        multi_swap_data: MultiSwapData<X>
    ): (address, Coin<X>, vector<NormalizedSwapData>) {
        let MultiSwapData<X> {
            receiver,
            input_coin,
            left_swap_data,
        } = multi_swap_data;
        (receiver, input_coin, left_swap_data)
    }

    fun destroy_generic_data(data: GenericData): (vector<u8>, String, u64) {
        let GenericData {
            tx_id,
            from_asset_id,
            from_amount
        } = data;
        (tx_id, from_asset_id, from_amount)
    }

    fun destroy_multi_src_data(
        multi_src_data: MultiSrcData
    ): (Coin<SUI>, NormalizedWormholeData, u64, vector<u8>) {
        let MultiSrcData {
            wormhole_fee_coin,
            wormhole_data,
            relay_fee,
            payload
        } = multi_src_data;
        (wormhole_fee_coin, wormhole_data, relay_fee, payload)
    }

    fun destroy_multi_dst_data(
        multi_dst_data: MultiDstData
    ): (vector<u8>) {
        let MultiDstData {
            tx_id,
        } = multi_dst_data;
        (tx_id)
    }

    fun complete_transfer<X>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<X>, TransferWithPayload) {
        let verified_vaa = vaa::parse_and_verify(wormhole_state, vaa, clock);
        let msg = bridge_vaa::verify_only_once(token_bridge_state, verified_vaa);
        let receipt =
            complete_transfer_with_payload::authorize_transfer<X>(
                token_bridge_state,
                msg,
                ctx
            );
        let (
            bridged,
            parsed_transfer,
            _
        ) = complete_transfer_with_payload::redeem_coin(&storage.emitter_cap, receipt);
        (bridged, parsed_transfer)
    }

    public fun complete_so_multi_swap<X>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ): (MultiSwapData<X>, MultiDstData) {
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));
        assert!(vector::length(&swap_data_dst) > 0, EMULTISWAP_STEP);

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));

        event::emit(DstAmount {
            so_fee
        });

        (
            MultiSwapData<X> {
                receiver,
                input_coin: coin_x,
                left_swap_data: swap_data_dst,
            },
            MultiDstData {
                tx_id: cross::so_transaction_id(so_data)
            }
        )
    }

    public fun complete_multi_dst_swap<X>(
        multi_swap_data: MultiSwapData<X>,
        multi_dst_data: MultiDstData,
    ) {
        assert!(vector::length(&multi_swap_data.left_swap_data) == 0, EMULTISWAP_STEP);
        let (receiver, coin_x, left_swap_data) = destroy_multi_swap_data(multi_swap_data);
        let tx_id = destroy_multi_dst_data(multi_dst_data);

        vector::destroy_empty(left_swap_data);
        let receiving_amount = coin::value(&coin_x);
        transfer::public_transfer(coin_x, receiver);

        event::emit(
            SoTransferCompleted {
                transaction_id: tx_id,
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: tx_id,
                status: ascii::string(b"All"),
                receiving_asset_id: type_name::into_string(type_name::get<X>()),
                receiving_amount
            }
        );
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_without_swap<X>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        assert!(vector::length(&swap_data_dst) == 0, ESWAP_LENGTH);
        transfer::public_transfer(coin_x, receiver);

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id: type_name::into_string(type_name::get<X>()),
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_deepbook_v2_quote_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        deepbook_v2_storage: &mut DeepbookV2Storage,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        let receiving_asset_id = type_name::into_string(type_name::get<X>());
        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);
            let (coin_x, remain_coin) = split_deepbook_coin(
                deepbook_v2_storage,
                object::id(pool_xy),
                coin_x,
                ctx
            );

            let src_token = type_name::into_string(type_name::get<X>());
            let dst_token = type_name::into_string(type_name::get<Y>());
            let src_input_amount = coin::value(&coin_x);

            let (left_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_deepbook_v2<X, Y>(
                pool_xy,
                coin_x,
                &deepbook_v2_storage.account_cap,
                deepbook_v2_storage.client_order_id,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_y);
            let src_remain_amount = coin::value(&left_coin_x) + coin::value(&remain_coin);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;
            receiving_amount = coin::value(&coin_y);
            receiving_asset_id = type_name::into_string(type_name::get<Y>());
            transfer::public_transfer(coin_y, receiver);
            process_left_coin(left_coin_x, receiver);
            process_left_coin(remain_coin, receiver);
        } else {
            transfer::public_transfer(coin_x, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(RelayerEvnetV2 {
            transaction_id: cross::so_transaction_id(so_data),
            status: ascii::string(b"All"),
            receiving_asset_id,
            receiving_amount
        }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_deepbook_v2_base_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookV2Pool<X, Y>,
        deepbook_v2_storage: &mut DeepbookV2Storage,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_y, payload) = complete_transfer<Y>(
            storage,
            token_bridge_state,
            wormhole_state,
            vaa,
            clock,
            ctx
        );

        let y_val = coin::value(&coin_y);


        let so_fee = (((y_val as u128) * (get_so_fees(wormhole_fee) as u128) / (RAY as u128)) as u64);
        let beneficiary = wormhole_fee.beneficiary;
        if (so_fee > 0 && so_fee <= y_val) {
            let coin_fee = coin::split<Y>(&mut coin_y, so_fee, ctx);
            transfer::public_transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: y_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_y);
        let receiving_asset_id = type_name::into_string(type_name::get<Y>());
        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);

            let src_token = type_name::into_string(type_name::get<Y>());
            let dst_token = type_name::into_string(type_name::get<X>());
            let src_input_amount = coin::value(&coin_y);

            let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_deepbook_v2<X, Y>(
                pool_xy,
                coin_y,
                &deepbook_v2_storage.account_cap,
                deepbook_v2_storage.client_order_id,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_x);
            let src_remain_amount = coin::value(&left_coin_y);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            deepbook_v2_storage.client_order_id = deepbook_v2_storage.client_order_id + 1;
            receiving_amount = coin::value(&coin_x);
            receiving_asset_id = type_name::into_string(type_name::get<X>());
            transfer::public_transfer(coin_x, receiver);
            process_left_coin(left_coin_y, receiver);
        } else {
            transfer::public_transfer(coin_y, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id,
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_deepbook_quote_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookPool<X, Y>,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        let receiving_asset_id = type_name::into_string(type_name::get<X>());

        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);

            let src_token = type_name::into_string(type_name::get<X>());
            let dst_token = type_name::into_string(type_name::get<Y>());
            let src_input_amount = coin::value(&coin_x);

            let (left_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_deepbook<X, Y>(
                pool_xy,
                coin_x,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_y);
            let src_remain_amount = coin::value(&left_coin_x);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            receiving_amount = coin::value(&coin_y);
            receiving_asset_id = type_name::into_string(type_name::get<Y>());
            transfer::public_transfer(coin_y, receiver);
            process_left_coin(left_coin_x, receiver);
        } else {
            transfer::public_transfer(coin_x, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id,
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_deepbook_base_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        pool_xy: &mut DeepbookPool<X, Y>,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_y, payload) = complete_transfer<Y>(
            storage,
            token_bridge_state,
            wormhole_state,
            vaa,
            clock,
            ctx
        );

        let y_val = coin::value(&coin_y);

        let so_fee = (((y_val as u128) * (get_so_fees(wormhole_fee) as u128) / (RAY as u128)) as u64);
        let beneficiary = wormhole_fee.beneficiary;
        if (so_fee > 0 && so_fee <= y_val) {
            let coin_fee = coin::split<Y>(&mut coin_y, so_fee, ctx);
            transfer::public_transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: y_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_y);
        let receiving_asset_id = type_name::into_string(type_name::get<Y>());

        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);

            let src_token = type_name::into_string(type_name::get<Y>());
            let dst_token = type_name::into_string(type_name::get<X>());
            let src_input_amount = coin::value(&coin_y);

            let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_deepbook<X, Y>(
                pool_xy,
                coin_y,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_x);
            let src_remain_amount = coin::value(&left_coin_y);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            receiving_amount = coin::value(&coin_x);
            receiving_asset_id = type_name::into_string(type_name::get<X>());

            transfer::public_transfer(coin_x, receiver);
            process_left_coin(left_coin_y, receiver);
        } else {
            transfer::public_transfer(coin_y, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id,
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_cetus_quote_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_x);
        let receiving_asset_id = type_name::into_string(type_name::get<X>());

        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);

            let src_token = type_name::into_string(type_name::get<X>());
            let dst_token = type_name::into_string(type_name::get<Y>());
            let src_input_amount = coin::value(&coin_x);

            let (left_coin_x, coin_y, _) = swap::swap_for_quote_asset_by_cetus<X, Y>(
                config,
                pool_xy,
                coin_x,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_y);
            let src_remain_amount = coin::value(&left_coin_x);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            receiving_amount = coin::value(&coin_y);
            receiving_asset_id = type_name::into_string(type_name::get<Y>());

            transfer::public_transfer(coin_y, receiver);
            process_left_coin(left_coin_x, receiver);
        } else {
            transfer::public_transfer(coin_x, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id,
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_for_cetus_base_asset<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        config: &GlobalConfig,
        pool_xy: &mut CetusPool<X, Y>,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        let (coin_y, payload) = complete_transfer<Y>(
            storage,
            token_bridge_state,
            wormhole_state,
            vaa,
            clock,
            ctx
        );

        let y_val = coin::value(&coin_y);


        let so_fee = (((y_val as u128) * (get_so_fees(wormhole_fee) as u128) / (RAY as u128)) as u64);
        let beneficiary = wormhole_fee.beneficiary;
        if (so_fee > 0 && so_fee <= y_val) {
            let coin_fee = coin::split<Y>(&mut coin_y, so_fee, ctx);
            transfer::public_transfer(coin_fee, beneficiary);
        };

        let (_, _, so_data, swap_data_dst) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<Y>()),
                amount: y_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));
        let receiving_amount = coin::value(&coin_y);
        let receiving_asset_id = type_name::into_string(type_name::get<Y>());

        if (vector::length(&swap_data_dst) > 0) {
            assert!(vector::length(&swap_data_dst) == 1, ESWAP_LENGTH);

            let src_token = type_name::into_string(type_name::get<Y>());
            let dst_token = type_name::into_string(type_name::get<X>());
            let src_input_amount = coin::value(&coin_y);

            let (coin_x, left_coin_y, _) = swap::swap_for_base_asset_by_cetus<X, Y>(
                config,
                pool_xy,
                coin_y,
                *vector::borrow(&swap_data_dst, 0),
                clock,
                ctx
            );

            let dst_output_amount = coin::value(&coin_x);
            let src_remain_amount = coin::value(&left_coin_y);
            event::emit(
                SwapEvent {
                    src_token,
                    dst_token,
                    src_input_amount,
                    dst_output_amount,
                    src_remain_amount
                }
            );

            receiving_amount = coin::value(&coin_x);
            receiving_asset_id = type_name::into_string(type_name::get<X>());

            transfer::public_transfer(coin_x, receiver);
            process_left_coin(left_coin_y, receiver);
        } else {
            transfer::public_transfer(coin_y, receiver);
        };

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"All"),
                receiving_asset_id,
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To avoid wormhole payload data construction errors, lock the token and allow the owner to handle
    /// it manually.
    public entry fun complete_so_swap_by_admin<X>(
        storage: &mut Storage,
        facet_manager: &mut WormholeFacetManager,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        to: address,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        assert!(facet_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        let receiving_amount = coin::value(&coin_x);
        transfer::public_transfer(coin_x, to);

        let (_, _, so_data, _) = decode_wormhole_payload(&transfer_with_payload::payload(&payload));

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"Part"),
                receiving_asset_id: type_name::into_string(type_name::get<X>()),
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// To avoid swap min amount errors, allow relayer to compensate
    public entry fun complete_so_swap_by_relayer<X>(
        storage: &mut Storage,
        facet_manager: &mut WormholeFacetManager,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        assert!(tx_context::sender(ctx) == facet_manager.relayer, EINVALID_ACCOUNT);
        let (coin_x, payload) = complete_transfer<X>(
            storage,
            token_bridge_state,
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

        event::emit(
            OrignEvnet {
                tx_sender: tx_context::sender(ctx),
                so_receiver: cross::so_receiver(so_data),
                token: type_name::into_string(type_name::get<X>()),
                amount: x_val
            }
        );

        let receiver = serde::deserialize_address(&cross::so_receiver(so_data));

        let receiving_amount = coin::value(&coin_x);
        transfer::public_transfer(coin_x, receiver);

        event::emit(
            SoTransferCompleted {
                transaction_id: cross::so_transaction_id(so_data),
                actual_receiving_amount: receiving_amount
            }
        );

        event::emit(
            RelayerEvnetV2 {
                transaction_id: cross::so_transaction_id(so_data),
                status: ascii::string(b"Part"),
                receiving_asset_id: type_name::into_string(type_name::get<X>()),
                receiving_amount
            }
        );

        event::emit(DstAmount {
            so_fee
        });
    }

    /// Swap Helpers

    /// Ensure that there is a minimal cost to help Relayer complete transactions in the destination chain.
    public fun estimate_relayer_fee(
        storage: &mut Storage,
        state: &mut WormholeState,
        price_manager: &mut PriceManager,
        so_data: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
    ): (u64, u64, u256) {
        let so_data = cross::decode_normalized_so_data(&mut so_data);

        let wormhole_data = decode_normalized_wormhole_data(&wormhole_data);

        let swap_data_dst = if (vector::length(&swap_data_dst) > 0) {
            cross::decode_normalized_swap_data(&mut swap_data_dst)
        }else {
            vector::empty()
        };

        let estimate_reserve = storage.estimate_reserve;

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
        src_fee = src_fee * (estimate_reserve as u256);
        src_fee = src_fee / one;

        if (wormhole_data.dst_wormhole_chain_id == 22) {
            // Aptos chain, decimal * 10
            src_fee = src_fee * 10;
        }else {
            // Evm chain, decimal / 1e9
            src_fee = src_fee / 1000000000;
        };

        let consume_value = state::message_fee(state);

        let src_fee = (src_fee as u64);
        consume_value = consume_value + src_fee;

        (src_fee, consume_value, dst_max_gas)
    }

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

        if (wormhole_data.dst_wormhole_chain_id == 22) {
            // Aptos chain, decimal * 10
            src_fee = src_fee * 10;
        }else {
            // Evm chain, decimal / 1e9
            src_fee = src_fee / 1000000000;
        };

        let consume_value = state::message_fee(state);

        let src_fee = (src_fee as u64);
        consume_value = consume_value + src_fee;

        let flag = false;
        // let return_value = 0;

        let wormhole_fee = (wormhole_data.wormhole_fee as u64);
        if (consume_value <= wormhole_fee) {
            flag = true;
            // return_value = wormhole_fee - consume_value;
        };
        (flag, src_fee, consume_value, dst_max_gas)
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

    #[test_only]
    public fun init_for_testing(ctx: &mut TxContext) {
        transfer::share_object(WormholeFacetManager {
            id: object::new(ctx),
            owner: tx_context::sender(ctx),
            relayer: tx_context::sender(ctx),
        })
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
