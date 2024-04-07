#[test_only]
module omniswap::wormhole_facet_tests {
    use std::type_name;
    use std::vector;

    use deepbook::clob_v2::{Self, Pool};
    use omniswap::cross::{Self, NormalizedSwapData};
    use omniswap::so_fee_wormhole::{Self, PriceManager};
    use omniswap::wormhole_facet::{Self, DeepbookV2Storage, Storage, WormholeFacetManager, WormholeFee};
    use sui::address;
    use sui::clock::{Self, Clock};
    use sui::coin;
    use sui::sui::SUI;
    use sui::test_scenario::{Self, Scenario};
    use sui::transfer;
    use token_bridge::coin_native_10::{Self, COIN_NATIVE_10};
    use token_bridge::coin_native_4::{Self, COIN_NATIVE_4};
    use token_bridge::state::State as TokenBridgeState;
    use token_bridge::token_bridge_scenario;
    use wormhole::state::{Self, State as WormholeState};

    const RAY: u64 = 100000000;
    const REFERENCE_TAKER_FEE_RATE: u64 = 5000000;
    const REFERENCE_MAKER_REBATE_RATE: u64 = 2500000;
    const FLOAT_SCALING: u64 = 1000000000;
    const FEE_AMOUNT_FOR_CREATE_POOL: u64 = 100 * 1000000000; // 100 SUI

    public fun setup_facet(scenario: &mut Scenario) {
        let sender = test_scenario::sender(scenario);

        token_bridge_scenario::set_up_wormhole_and_token_bridge(scenario, 0);
        coin_native_4::init_and_register(scenario, sender);
        coin_native_10::init_and_register(scenario, sender);

        test_scenario::next_tx(scenario, sender);
        {
            let ctx = test_scenario::ctx(scenario);
            wormhole_facet::init_for_testing(ctx);
            so_fee_wormhole::init_for_testing(ctx);
            clock::share_for_testing(clock::create_for_testing(test_scenario::ctx(scenario)));
        };

        test_scenario::next_tx(scenario, sender);
        {
            let facet_manager = test_scenario::take_shared<WormholeFacetManager>(scenario);
            let wormhole_state = test_scenario::take_shared<WormholeState>(scenario);
            let token_bridge_state = test_scenario::take_shared<TokenBridgeState>(scenario);

            wormhole_facet::init_wormhole(
                &mut facet_manager,
                &mut wormhole_state,
                21,
                test_scenario::ctx(scenario)
            );

            test_scenario::return_shared(facet_manager);
            test_scenario::return_shared(wormhole_state);
            test_scenario::return_shared(token_bridge_state);
        };

        test_scenario::next_tx(scenario, sender);
        {
            let wormhole_facet_manager = test_scenario::take_shared<WormholeFacetManager>(scenario);
            let facet_storage = test_scenario::take_shared<Storage>(scenario);
            let wormhole_fee = test_scenario::take_shared<WormholeFee>(scenario);
            let price_manager = test_scenario::take_shared<PriceManager>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);

            wormhole_facet::set_so_fees(&mut wormhole_fee, 0, ctx);
            so_fee_wormhole::set_price_ratio(&clock, &mut price_manager, 0, 1 * RAY, ctx);
            so_fee_wormhole::set_price_ratio(&clock, &mut price_manager, 1, 1 * RAY, ctx);
            so_fee_wormhole::set_price_ratio(&clock, &mut price_manager, 2, 1 * RAY, ctx);
            wormhole_facet::set_wormhole_reserve(
                &mut wormhole_facet_manager,
                &mut facet_storage,
                1 * RAY,
                1 * RAY,
                ctx
            );
            wormhole_facet::set_wormhole_gas(&mut facet_storage, &mut wormhole_facet_manager, 2, 1500000, 68, ctx);

            test_scenario::return_shared(wormhole_facet_manager);
            test_scenario::return_shared(facet_storage);
            test_scenario::return_shared(wormhole_fee);
            test_scenario::return_shared(price_manager);
            test_scenario::return_shared(clock);
        };
    }

    public fun setup_deepbook_v2_storage(scenario: &mut Scenario) {
        let sender = test_scenario::sender(scenario);
        test_scenario::next_tx(scenario, sender);
        {
            let wormhole_facet_manager = test_scenario::take_shared<WormholeFacetManager>(scenario);
            let ctx = test_scenario::ctx(scenario);

            wormhole_facet::init_deepbook_v2(&mut wormhole_facet_manager, ctx);

            test_scenario::return_shared(wormhole_facet_manager);
        };
    }


    public fun setup_swap_for_base_asset_by_deepbook(scenario: &mut Scenario) {
        let sender = test_scenario::sender(scenario);
        test_scenario::next_tx(scenario, sender);
        {
            let ctx = test_scenario::ctx(scenario);
            clob_v2::create_pool<COIN_NATIVE_4, COIN_NATIVE_10>(
                1 * FLOAT_SCALING,
                1,
                coin::mint_for_testing<SUI>(FEE_AMOUNT_FOR_CREATE_POOL, ctx),
                ctx
            );
        };

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<COIN_NATIVE_4, COIN_NATIVE_10>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let base_coin = coin::mint_for_testing<COIN_NATIVE_4>(1000, ctx);

            clob_v2::deposit_base<COIN_NATIVE_4, COIN_NATIVE_10>(&mut pool, base_coin, &account_cap);
            clob_v2::place_limit_order<COIN_NATIVE_4, COIN_NATIVE_10>(
                &mut pool,
                1,
                1 * FLOAT_SCALING,
                1000,
                0,
                false,
                1000,
                0,
                &clock,
                &account_cap,
                ctx
            );

            transfer::public_transfer(account_cap, sender);
            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };
    }

    public fun setup_swap_for_quote_asset_by_deepbook(scenario: &mut Scenario) {
        let sender = test_scenario::sender(scenario);
        test_scenario::next_tx(scenario, sender);
        {
            let ctx = test_scenario::ctx(scenario);
            clob_v2::create_pool<COIN_NATIVE_4, COIN_NATIVE_10>(
                1 * FLOAT_SCALING,
                1,
                coin::mint_for_testing<SUI>(FEE_AMOUNT_FOR_CREATE_POOL, ctx),
                ctx
            );
        };

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<COIN_NATIVE_4, COIN_NATIVE_10>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let quote_coin = coin::mint_for_testing<COIN_NATIVE_10>(1000, ctx);

            clob_v2::deposit_quote<COIN_NATIVE_4, COIN_NATIVE_10>(&mut pool, quote_coin, &account_cap);
            clob_v2::place_limit_order<COIN_NATIVE_4, COIN_NATIVE_10>(
                &mut pool,
                1,
                1 * FLOAT_SCALING,
                1000,
                0,
                true,
                1000,
                0,
                &clock,
                &account_cap,
                ctx
            );

            transfer::public_transfer(account_cap, sender);
            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };
    }

    public fun get_asset_id<T>(): vector<u8> {
        let data = type_name::get<T>();
        let data = type_name::into_string(data);
        std::ascii::into_bytes(data)
    }

    #[test]
    public fun test_so_swap_without_swap() {
        let sender = @0xA;
        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        setup_facet(scenario);
        setup_swap_for_base_asset_by_deepbook(scenario);

        test_scenario::next_tx(scenario, sender);
        {
            let wormhole_state = test_scenario::take_shared<WormholeState>(scenario);
            let facet_storage = test_scenario::take_shared<Storage>(scenario);
            let price_manager = test_scenario::take_shared<PriceManager>(scenario);
            let token_bridge_state = test_scenario::take_shared<TokenBridgeState>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let wormhole_fee = test_scenario::take_shared<WormholeFee>(scenario);

            let ctx = test_scenario::ctx(scenario);
            let input_sui_val = 100;
            let input_coin = coin::mint_for_testing<COIN_NATIVE_4>(100, ctx);
            let so_data = cross::construct_so_data(
                x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                1,
                get_asset_id<COIN_NATIVE_4>(),
                2,
                x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
                (input_sui_val as u256)
            );

            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                0,
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            let src_swap_data = vector::empty<NormalizedSwapData>();
            let dst_swap_data = vector::empty<NormalizedSwapData>();

            let (_, relayer_fee, _, _) = wormhole_facet::check_relayer_fee(
                &mut facet_storage,
                &mut wormhole_state,
                &mut price_manager,
                so_data,
                wormhole_data,
                dst_swap_data
            );
            let msg_fee = state::message_fee(&mut wormhole_state);
            let wormhole_fee_amount = msg_fee + relayer_fee + input_sui_val;

            let fee_coin = coin::mint_for_testing<SUI>(wormhole_fee_amount, ctx);
            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                (wormhole_fee_amount as u256),
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            wormhole_facet::so_swap_without_swap<COIN_NATIVE_4>(
                &mut wormhole_state,
                &mut token_bridge_state,
                &mut facet_storage,
                &clock,
                &mut price_manager,
                &mut wormhole_fee,
                cross::encode_normalized_so_data(so_data),
                cross::encode_normalized_swap_data(src_swap_data),
                wormhole_facet::encode_normalized_wormhole_data(wormhole_data),
                cross::encode_normalized_swap_data(dst_swap_data),
                vector[input_coin],
                vector[fee_coin],
                ctx
            );

            test_scenario::return_shared(wormhole_state);
            test_scenario::return_shared(facet_storage);
            test_scenario::return_shared(price_manager);
            test_scenario::return_shared(token_bridge_state);
            test_scenario::return_shared(clock);
            test_scenario::return_shared(wormhole_fee);
        };

        test_scenario::end(scenario_val);
    }

    #[test]
    public fun test_so_swap_for_deepbook_v2_base_asset() {
        let sender = @0xA;
        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        setup_facet(scenario);
        setup_swap_for_base_asset_by_deepbook(scenario);
        setup_deepbook_v2_storage(scenario);

        test_scenario::next_tx(scenario, sender);
        {
            let wormhole_state = test_scenario::take_shared<WormholeState>(scenario);
            let facet_storage = test_scenario::take_shared<Storage>(scenario);
            let deepbook_v2_storage = test_scenario::take_shared<DeepbookV2Storage>(scenario);
            let price_manager = test_scenario::take_shared<PriceManager>(scenario);
            let token_bridge_state = test_scenario::take_shared<TokenBridgeState>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let wormhole_fee = test_scenario::take_shared<WormholeFee>(scenario);
            let pool = test_scenario::take_shared<Pool<COIN_NATIVE_4, COIN_NATIVE_10>>(scenario);

            let ctx = test_scenario::ctx(scenario);
            let input_val = 100;
            let input_coin = coin::mint_for_testing<COIN_NATIVE_10>(100, ctx);
            let so_data = cross::construct_so_data(
                x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                1,
                get_asset_id<COIN_NATIVE_10>(),
                2,
                x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
                (input_val as u256)
            );

            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                0,
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            let swap_data = cross::construct_swap_data(
                address::to_bytes(@deepbook),
                address::to_bytes(@deepbook),
                get_asset_id<COIN_NATIVE_10>(),
                get_asset_id<COIN_NATIVE_4>(),
                100,
                b"DeepBookV2,0"
            );

            let src_swap_data = vector[swap_data];

            let dst_swap_data = vector::empty<NormalizedSwapData>();

            let (_, relayer_fee, _, _) = wormhole_facet::check_relayer_fee(
                &mut facet_storage,
                &mut wormhole_state,
                &mut price_manager,
                so_data,
                wormhole_data,
                dst_swap_data
            );
            let msg_fee = state::message_fee(&mut wormhole_state);
            let wormhole_fee_amount = msg_fee + relayer_fee + input_val;

            let fee_coin = coin::mint_for_testing<SUI>(wormhole_fee_amount, ctx);
            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                (wormhole_fee_amount as u256),
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            wormhole_facet::so_swap_for_deepbook_v2_base_asset<COIN_NATIVE_4, COIN_NATIVE_10>(
                &mut facet_storage,
                &mut wormhole_fee,
                &mut price_manager,
                &mut pool,
                &mut wormhole_state,
                &mut token_bridge_state,
                &mut deepbook_v2_storage,
                cross::encode_normalized_so_data(so_data),
                cross::encode_normalized_swap_data(src_swap_data),
                wormhole_facet::encode_normalized_wormhole_data(wormhole_data),
                cross::encode_normalized_swap_data(dst_swap_data),
                vector[input_coin],
                vector[fee_coin],
                &clock,
                ctx
            );

            test_scenario::return_shared(wormhole_state);
            test_scenario::return_shared(facet_storage);
            test_scenario::return_shared(deepbook_v2_storage);
            test_scenario::return_shared(price_manager);
            test_scenario::return_shared(token_bridge_state);
            test_scenario::return_shared(clock);
            test_scenario::return_shared(wormhole_fee);
            test_scenario::return_shared(pool);
        };

        test_scenario::end(scenario_val);
    }

    #[test]
    public fun test_so_swap_for_deepbook_v2_quote_asset() {
        let sender = @0xA;
        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        setup_facet(scenario);
        setup_swap_for_base_asset_by_deepbook(scenario);
        setup_deepbook_v2_storage(scenario);

        test_scenario::next_tx(scenario, sender);
        {
            let wormhole_state = test_scenario::take_shared<WormholeState>(scenario);
            let facet_storage = test_scenario::take_shared<Storage>(scenario);
            let deepbook_v2_storage = test_scenario::take_shared<DeepbookV2Storage>(scenario);
            let price_manager = test_scenario::take_shared<PriceManager>(scenario);
            let token_bridge_state = test_scenario::take_shared<TokenBridgeState>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let wormhole_fee = test_scenario::take_shared<WormholeFee>(scenario);
            let pool = test_scenario::take_shared<Pool<COIN_NATIVE_4, COIN_NATIVE_10>>(scenario);

            let ctx = test_scenario::ctx(scenario);
            let input_val = 100;
            let input_coin = coin::mint_for_testing<COIN_NATIVE_4>(100, ctx);
            let so_data = cross::construct_so_data(
                x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
                1,
                get_asset_id<COIN_NATIVE_4>(),
                2,
                x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
                (input_val as u256)
            );

            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                0,
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            let swap_data = cross::construct_swap_data(
                address::to_bytes(@deepbook),
                address::to_bytes(@deepbook),
                get_asset_id<COIN_NATIVE_4>(),
                get_asset_id<COIN_NATIVE_10>(),
                100,
                b"DeepBookV2,0"
            );

            let src_swap_data = vector[swap_data];

            let dst_swap_data = vector::empty<NormalizedSwapData>();

            let (_, relayer_fee, _, _) = wormhole_facet::check_relayer_fee(
                &mut facet_storage,
                &mut wormhole_state,
                &mut price_manager,
                so_data,
                wormhole_data,
                dst_swap_data
            );
            let msg_fee = state::message_fee(&mut wormhole_state);
            let wormhole_fee_amount = msg_fee + relayer_fee + input_val;

            let fee_coin = coin::mint_for_testing<SUI>(wormhole_fee_amount, ctx);
            let wormhole_data = wormhole_facet::construct_normalized_wormhole_data(
                2,
                100000,
                (wormhole_fee_amount as u256),
                x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
            );

            wormhole_facet::so_swap_for_deepbook_v2_quote_asset<COIN_NATIVE_4, COIN_NATIVE_10>(
                &mut facet_storage,
                &mut wormhole_fee,
                &mut price_manager,
                &mut pool,
                &mut wormhole_state,
                &mut deepbook_v2_storage,
                &mut token_bridge_state,
                cross::encode_normalized_so_data(so_data),
                cross::encode_normalized_swap_data(src_swap_data),
                wormhole_facet::encode_normalized_wormhole_data(wormhole_data),
                cross::encode_normalized_swap_data(dst_swap_data),
                vector[input_coin],
                vector[fee_coin],
                &clock,
                ctx
            );

            test_scenario::return_shared(wormhole_state);
            test_scenario::return_shared(facet_storage);
            test_scenario::return_shared(deepbook_v2_storage);
            test_scenario::return_shared(price_manager);
            test_scenario::return_shared(token_bridge_state);
            test_scenario::return_shared(clock);
            test_scenario::return_shared(wormhole_fee);
            test_scenario::return_shared(pool);
        };

        test_scenario::end(scenario_val);
    }
}
