#[test_only]
module omniswap::swap_tests {

    use deepbook::clob_v2::{Self, Pool, USD};
    use deepbook::custodian_v2;
    use omniswap::cross;
    use omniswap::swap;
    use sui::clock::Clock;
    use sui::coin;
    use sui::sui::SUI;
    use sui::test_scenario;
    use sui::transfer;

    const REFERENCE_TAKER_FEE_RATE: u64 = 5000000;
    const REFERENCE_MAKER_REBATE_RATE: u64 = 2500000;
    const FLOAT_SCALING: u64 = 1000000000;


    #[test]
    public fun test_swap_for_base_asset_by_deepbook_v2() {
        let sender = @0xA;

        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        clob_v2::setup_test(REFERENCE_TAKER_FEE_RATE, REFERENCE_MAKER_REBATE_RATE, scenario, sender);

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let base_coin = coin::mint_for_testing<SUI>(1000, ctx);
            clob_v2::deposit_base<SUI, USD>(&mut pool, base_coin, &account_cap);
            clob_v2::place_limit_order<SUI, USD>(
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

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let quote_coin = coin::mint_for_testing<USD>(1000, ctx);
            let swap_data = cross::construct_swap_data(
                x"dee9",
                x"dee9",
                b"000000000000000000000000000000000000000000000000000000000000dee9::clob_v2::USD",
                b"0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                1000,
                b"DeepBookV2,0"
            );

            let (base_coin, left_quote_coin, swap_value) = swap::swap_for_base_asset_by_deepbook_v2<SUI, USD>(
                &mut pool,
                quote_coin,
                &account_cap,
                1,
                swap_data,
                &clock,
                ctx
            );


            let fee = 1000 * REFERENCE_TAKER_FEE_RATE / FLOAT_SCALING;
            assert!(coin::value(&base_coin) == 1000 - fee, 201);
            assert!(coin::value(&left_quote_coin) == 0, 202);
            assert!(swap_value == 1000 - fee, 203);

            coin::burn_for_testing(base_coin);
            coin::burn_for_testing(left_quote_coin);

            custodian_v2::delete_account_cap(account_cap);

            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };

        test_scenario::end(scenario_val);
    }

    #[test]
    public fun test_swap_for_quote_asset_by_deepbook_v2() {
        let sender = @0xA;

        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        clob_v2::setup_test(REFERENCE_TAKER_FEE_RATE, REFERENCE_MAKER_REBATE_RATE, scenario, sender);

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let quote_coin = coin::mint_for_testing<USD>(1000, ctx);
            clob_v2::deposit_quote<SUI, USD>(&mut pool, quote_coin, &account_cap);
            clob_v2::place_limit_order<SUI, USD>(
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

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let base_coin = coin::mint_for_testing<SUI>(1000, ctx);
            let swap_data = cross::construct_swap_data(
                x"dee9",
                x"dee9",
                b"0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                b"000000000000000000000000000000000000000000000000000000000000dee9::clob_v2::USD",
                1000,
                b"DeepBookV2,0"
            );

            let (left_base_coin, quote_coin, swap_value) = swap::swap_for_quote_asset_by_deepbook_v2<SUI, USD>(
                &mut pool,
                base_coin,
                &account_cap,
                0,
                swap_data,
                &clock,
                ctx
            );

            let fee = 1000 * REFERENCE_TAKER_FEE_RATE / FLOAT_SCALING;
            assert!(coin::value(&quote_coin) == 1000 - fee, 201);
            assert!(coin::value(&left_base_coin) == 0, 202);
            assert!(swap_value == 1000 - fee, 203);


            coin::burn_for_testing(quote_coin);
            coin::burn_for_testing(left_base_coin);

            custodian_v2::delete_account_cap(account_cap);

            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };

        test_scenario::end(scenario_val);
    }

    #[test]
    public fun test_swap_with_left_coin() {
        let sender = @0xA;

        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        clob_v2::setup_test(REFERENCE_TAKER_FEE_RATE, REFERENCE_MAKER_REBATE_RATE, scenario, sender);

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let quote_coin = coin::mint_for_testing<USD>(1000, ctx);
            clob_v2::deposit_quote<SUI, USD>(&mut pool, quote_coin, &account_cap);
            clob_v2::place_limit_order<SUI, USD>(
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

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let base_coin = coin::mint_for_testing<SUI>(10000, ctx);
            let swap_data = cross::construct_swap_data(
                x"dee9",
                x"dee9",
                b"0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                b"000000000000000000000000000000000000000000000000000000000000dee9::clob_v2::USD",
                10000,
                b"DeepBookV2,9000"
            );

            let (left_base_coin, quote_coin, swap_value) = swap::swap_for_quote_asset_by_deepbook_v2<SUI, USD>(
                &mut pool,
                base_coin,
                &account_cap,
                1,
                swap_data,
                &clock,
                ctx
            );

            let fee = 1000 * REFERENCE_TAKER_FEE_RATE / FLOAT_SCALING;
            assert!(coin::value(&quote_coin) == 1000 - fee, 201);
            assert!(coin::value(&left_base_coin) == 9000, 202);
            assert!(swap_value == 1000 - fee, 203);

            coin::burn_for_testing(quote_coin);
            coin::burn_for_testing(left_base_coin);

            custodian_v2::delete_account_cap(account_cap);

            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };

        test_scenario::end(scenario_val);
    }

    #[test]
    #[expected_failure(abort_code = swap::ESWAP_AMOUNT_TOO_LOW)]
    public fun test_swap_with_less_min_amount() {
        let sender = @0xA;

        let scenario_val = test_scenario::begin(sender);
        let scenario = &mut scenario_val;

        clob_v2::setup_test(REFERENCE_TAKER_FEE_RATE, REFERENCE_MAKER_REBATE_RATE, scenario, sender);

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let quote_coin = coin::mint_for_testing<USD>(1000, ctx);
            clob_v2::deposit_quote<SUI, USD>(&mut pool, quote_coin, &account_cap);
            clob_v2::place_limit_order<SUI, USD>(
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

        test_scenario::next_tx(scenario, sender);
        {
            let pool = test_scenario::take_shared<Pool<SUI, USD>>(scenario);
            let clock = test_scenario::take_shared<Clock>(scenario);
            let ctx = test_scenario::ctx(scenario);
            let account_cap = clob_v2::create_account(ctx);
            let base_coin = coin::mint_for_testing<SUI>(1000, ctx);
            let swap_data = cross::construct_swap_data(
                x"dee9",
                x"dee9",
                b"0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
                b"000000000000000000000000000000000000000000000000000000000000dee9::clob_v2::USD",
                1000,
                b"DeepBookV2,1000"
            );

            let (left_base_coin, quote_coin, swap_value) = swap::swap_for_quote_asset_by_deepbook_v2<SUI, USD>(
                &mut pool,
                base_coin,
                &account_cap,
                1,
                swap_data,
                &clock,
                ctx
            );

            let fee = 1000 * REFERENCE_TAKER_FEE_RATE / FLOAT_SCALING;
            assert!(coin::value(&quote_coin) == 1000 - fee, 201);
            assert!(coin::value(&left_base_coin) == 0, 202);
            assert!(swap_value == 1000 - fee, 203);

            coin::burn_for_testing(quote_coin);
            coin::burn_for_testing(left_base_coin);

            custodian_v2::delete_account_cap(account_cap);

            test_scenario::return_shared(pool);
            test_scenario::return_shared(clock);
        };

        test_scenario::end(scenario_val);
    }
}
