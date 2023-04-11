#[test_only]
module omniswap::swap_tests {
    use std::signer;

    use aptos_framework::coin;
    use liquidswap_lp::lp_coin::LP;

    use liquidswap::curves::{Uncorrelated, Stable};
    use liquidswap::liquidity_pool;
    use liquidswap::router;
    use test_coin_admin::test_coins::{Self, USDT, BTC, USDC};
    use test_helpers::test_pool;
    use omniswap::cross::construct_swap_data;
    use std::vector;
    use omniswap::serde::serialize_address;
    use omniswap::u256;
    use omniswap::swap::{swap_by_account, swap_by_coin};

    const ERR_COIN_OUT_NUM_LESS_THAN_EXPECTED_MINIMUM: u64 = 205;

    public fun register_pool_with_liquidity(x_val: u64, y_val: u64): (signer, signer) {
        let (coin_admin, lp_owner) = test_pool::setup_coins_and_lp_owner();

        router::register_pool<BTC, USDT, Uncorrelated>(&lp_owner);

        let lp_owner_addr = signer::address_of(&lp_owner);
        if (x_val != 0 && y_val != 0) {
            let btc_coins = test_coins::mint<BTC>(&coin_admin, x_val);
            let usdt_coins = test_coins::mint<USDT>(&coin_admin, y_val);
            let lp_coins =
                liquidity_pool::mint<BTC, USDT, Uncorrelated>(btc_coins, usdt_coins);
            coin::register<LP<BTC, USDT, Uncorrelated>>(&lp_owner);
            coin::deposit<LP<BTC, USDT, Uncorrelated>>(lp_owner_addr, lp_coins);
        };

        (coin_admin, lp_owner)
    }

    public fun register_stable_pool_with_liquidity(x_val: u64, y_val: u64): (signer, signer) {
        let (coin_admin, lp_owner) = test_pool::setup_coins_and_lp_owner();
        router::register_pool<USDC, USDT, Stable>(&lp_owner);
        let lp_owner_addr = signer::address_of(&lp_owner);
        if (x_val != 0 && y_val != 0) {
            let usdc_coins = test_coins::mint<USDC>(&coin_admin, x_val);
            let usdt_coins = test_coins::mint<USDT>(&coin_admin, y_val);
            let lp_coins =
                liquidity_pool::mint<USDC, USDT, Stable>(usdc_coins, usdt_coins);
            coin::register<LP<USDC, USDT, Stable>>(&lp_owner);
            coin::deposit<LP<USDC, USDT, Stable>>(lp_owner_addr, lp_coins);
        };

        (coin_admin, lp_owner)
    }

    #[test(liquidswap=@liquidswap)]
    fun test_swap_stable_coin_by_account_with_enough_min_amount(liquidswap: &signer) {
    	let (coin_admin, _) = register_stable_pool_with_liquidity(10000, 10000);
        let usdc_to_swap_val = 100;
        let usdc_coins_to_swap = test_coins::mint<USDC>(&coin_admin, usdc_to_swap_val);

        coin::register<USDC>(&coin_admin);
        coin::deposit<USDC>(signer::address_of(&coin_admin), usdc_coins_to_swap);

        let usdt_to_get_val = router::get_amount_out<USDC, USDT, Stable>(usdc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::USDC",
            b"0x11::test_coins::USDT",
            u256::from_u64(usdc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Stable,100"
        );
        let usdt_coins = swap_by_account<USDC, USDT>(&coin_admin, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }

    #[test(liquidswap=@liquidswap)]
    #[expected_failure(abort_code=205)]
    fun test_swap_stable_coin_by_account_with_less_min_amount(liquidswap: &signer) {
    	let (coin_admin, _) = register_stable_pool_with_liquidity(10000, 10000);
        let usdc_to_swap_val = 100;
        let usdc_coins_to_swap = test_coins::mint<USDC>(&coin_admin, usdc_to_swap_val);

        coin::register<USDC>(&coin_admin);
        coin::deposit<USDC>(signer::address_of(&coin_admin), usdc_coins_to_swap);

        let usdt_to_get_val = router::get_amount_out<USDC, USDT, Stable>(usdc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::USDC",
            b"0x11::test_coins::USDT",
            u256::from_u64(usdc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Stable,1000"
        );
        let usdt_coins = swap_by_account<USDC, USDT>(&coin_admin, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }

    #[test(liquidswap=@liquidswap)]
    fun test_swap_stable_coin_by_account(liquidswap: &signer) {
    	let (coin_admin, _) = register_stable_pool_with_liquidity(10000, 10000);
        let usdc_to_swap_val = 100;
        let usdc_coins_to_swap = test_coins::mint<USDC>(&coin_admin, usdc_to_swap_val);

        coin::register<USDC>(&coin_admin);
        coin::deposit<USDC>(signer::address_of(&coin_admin), usdc_coins_to_swap);

        let usdt_to_get_val = router::get_amount_out<USDC, USDT, Stable>(usdc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::USDC",
            b"0x11::test_coins::USDT",
            u256::from_u64(usdc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Stable"
        );
        let usdt_coins = swap_by_account<USDC, USDT>(&coin_admin, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }

    #[test(liquidswap=@liquidswap)]
    fun test_swap_uncorrelated_coin_by_account(liquidswap: &signer) {
        let (coin_admin, _) = register_pool_with_liquidity(100, 3000000);

        let btc_to_swap_val = 1;
        let btc_coins_to_swap = test_coins::mint<BTC>(&coin_admin, btc_to_swap_val);

        coin::register<BTC>(&coin_admin);
        coin::deposit<BTC>(signer::address_of(&coin_admin), btc_coins_to_swap);

        let usdt_to_get_val = router::get_amount_out<BTC, USDT, Uncorrelated>(btc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::BTC",
            b"0x11::test_coins::USDT",
            u256::from_u64(btc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Uncorrelated"
        );
        let usdt_coins = swap_by_account<BTC, USDT>(&coin_admin, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }

    #[test(liquidswap=@liquidswap)]
    fun test_swap_stable_coin_by_coin(liquidswap: &signer) {
        let (coin_admin, _) = register_stable_pool_with_liquidity(10000, 10000);

        let usdc_to_swap_val = 100;
        let usdc_coins_to_swap = test_coins::mint<USDC>(&coin_admin, usdc_to_swap_val);

        let usdt_to_get_val = router::get_amount_out<USDC, USDT, Stable>(usdc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::USDC",
            b"0x11::test_coins::USDT",
            u256::from_u64(usdc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Stable"
        );
        let usdt_coins = swap_by_coin<USDC, USDT>(usdc_coins_to_swap, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }

    #[test(liquidswap=@liquidswap)]
    fun test_swap_uncorrelated_coin_by_coin(liquidswap: &signer) {
        let (coin_admin, _) = register_pool_with_liquidity(100, 3000000);

        let btc_to_swap_val = 1;
        let btc_coins_to_swap = test_coins::mint<BTC>(&coin_admin, btc_to_swap_val);

        let usdt_to_get_val = router::get_amount_out<BTC, USDT, Uncorrelated>(btc_to_swap_val);

        let router_address_bytes = vector::empty<u8>();
        serialize_address(&mut router_address_bytes, signer::address_of(liquidswap));
        let swap_data = construct_swap_data(
            router_address_bytes,
            router_address_bytes,
            b"0x11::test_coins::BTC",
            b"0x11::test_coins::USDT",
            u256::from_u64(btc_to_swap_val),
            b"0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Uncorrelated"
        );
        let usdt_coins = swap_by_coin<BTC, USDT>(btc_coins_to_swap, swap_data);
        assert!(coin::value(&usdt_coins) == usdt_to_get_val, 0);

        test_coins::burn(&coin_admin, usdt_coins);
    }
}
