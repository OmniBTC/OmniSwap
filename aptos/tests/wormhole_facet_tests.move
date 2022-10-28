#[test_only]
module omniswap::wormhole_facet_tests {
    use omniswap::wormhole_facet::{init_wormhole, so_swap, encode_normalized_wormhole_data, construct_normalized_wormhole_data, set_wormhole_reserve, set_wormhole_gas, check_relayer_fee, init_so_transfer_event};
    use wormhole::wormhole::init_test;
    use omniswap::cross::{construct_so_data, encode_normalized_so_data, construct_swap_data, NormalizedSwapData, encode_normalized_swap_data};
    use omniswap::u16;
    use omniswap::u256;
    use std::vector;
    use omniswap::so_fee_wormhole::{initialize, set_price_ratio};
    use omniswap::serde::{serialize_u256, serialize_address};
    use aptos_framework::coin;
    use std::signer;
    use aptos_framework::aptos_coin::{AptosCoin, initialize_for_test};
    use aptos_framework::coin::{destroy_mint_cap, destroy_burn_cap};
    use aptos_framework::aptos_account;
    use aptos_framework::timestamp::set_time_has_started_for_testing;
    use token_bridge::token_bridge;
    use test_helpers::test_pool::{initialize_liquidity_pool, create_lp_owner};
    use test_coin_admin::test_coins;
    use test_coin_admin::test_coins::{BTC, USDT};
    use liquidswap::curves::Uncorrelated;
    use liquidswap::liquidity_pool;
    use liquidswap_lp::lp_coin::LP;
    use liquidswap::router;
    use wormhole::state;

    const RAY: u64 = 100000000;

    public fun setup(aptos_framework: &signer, deployer: &signer, omniswap: &signer) {
        // init aptos timestamp
        set_time_has_started_for_testing(aptos_framework);
        // init aptos coin
        let (burn_cap, mint_cap) = initialize_for_test(aptos_framework);
        let apt_coins = coin::mint<AptosCoin>(1000000000000, &mint_cap);
        aptos_account::create_account(signer::address_of(omniswap));
        coin::deposit<AptosCoin>(signer::address_of(omniswap), apt_coins);
        destroy_mint_cap(mint_cap);
        destroy_burn_cap(burn_cap);
        // init wormholo
        init_test(
            1,
            1,
            x"0000000000000000000000000000000000000000000000000000000000000004",
            x"beFA429d57cD18b7F8A4d91A2da9AB4AF05d0FBe",
            0
        );
        // init wormhole tokenbridge
        token_bridge::init_test(deployer);
        // init wormhole so fee
        initialize(omniswap, 2);
        initialize(omniswap, 1);
        set_price_ratio(omniswap, 1, 1 * RAY);
        set_price_ratio(omniswap, 2, 1 * RAY);
        // init wormhole facet
        init_wormhole(omniswap, 22);
        init_so_transfer_event(omniswap);
        set_wormhole_reserve(omniswap, 1 * RAY, 1 * RAY);
        let base_gas = vector::empty<u8>();
        serialize_u256(&mut base_gas, u256::from_u64(1500000));
        let gas_per_bytes = vector::empty<u8>();
        serialize_u256(&mut gas_per_bytes, u256::from_u64(68));
        set_wormhole_gas(omniswap, 2, base_gas, gas_per_bytes);
    }

    public fun setup_liquidswap_pool(): (signer, signer) {
        initialize_liquidity_pool();

        let coin_admin = test_coins::create_admin_with_coins();
        let lp_owner = create_lp_owner();
        (coin_admin, lp_owner)
    }

    public fun create_liquidswap_pool<CoinX, CoinY, PoolType>(coin_admin: &signer, lp_owner: &signer, x_val: u64, y_val: u64) {
        router::register_pool<CoinX, CoinY, PoolType>(lp_owner);

        let lp_owner_addr = signer::address_of(lp_owner);
        if (x_val != 0 && y_val != 0) {
            let x_coins = test_coins::mint<CoinX>(coin_admin, x_val);
            let y_coins = test_coins::mint<CoinY>(coin_admin, y_val);
            let lp_coins =
                liquidity_pool::mint<CoinX, CoinY, PoolType>(x_coins, y_coins);
            coin::register<LP<CoinX, CoinY, PoolType>>(lp_owner);
            coin::deposit<LP<CoinX, CoinY, PoolType>>(lp_owner_addr, lp_coins);
        };
    }

    #[test(aptos_framework = @aptos_framework, deployer = @deployer, omniswap = @omniswap)]
    fun test_so_swap_without_swap(aptos_framework: &signer, deployer: &signer, omniswap: &signer) {
        setup(aptos_framework, deployer, omniswap);

        let input_aptos_val = 100;
        let so_data = construct_so_data(
            x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            u16::from_u64(1),
            b"0x1::aptos_coin::AptosCoin",
            u16::from_u64(2),
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            u256::from_u64(input_aptos_val)
        );

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(0),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        let src_swap_data = vector::empty<NormalizedSwapData>();
        let dst_swap_data = vector::empty<NormalizedSwapData>();

        let (_, relayer_fee, _, _) = check_relayer_fee(so_data, wormhole_data, dst_swap_data);
        let msg_fee = state::get_message_fee();
        let wormhole_fee = msg_fee + relayer_fee + input_aptos_val;

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(wormhole_fee),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        so_swap<AptosCoin, AptosCoin, AptosCoin, AptosCoin>(
            omniswap,
            encode_normalized_so_data(so_data),
            encode_normalized_swap_data(src_swap_data),
            encode_normalized_wormhole_data(wormhole_data),
            encode_normalized_swap_data(dst_swap_data)
        );
    }

    #[test(aptos_framework = @aptos_framework, deployer = @deployer, omniswap = @omniswap, liquidswap = @liquidswap)]
    fun test_so_swap_with_src_swap_two(aptos_framework: &signer, deployer: &signer, omniswap: &signer, liquidswap: &signer) {
        setup(aptos_framework, deployer, omniswap);
        let (coin_admin, lp_owner) = setup_liquidswap_pool();
        create_liquidswap_pool<BTC, USDT, Uncorrelated>(&coin_admin, &lp_owner, 1000, 1000000);

        let input_aptos_val = 100;
        let so_data = construct_so_data(
            x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            u16::from_u64(1),
            b"0x11::test_coins::USDT",
            u16::from_u64(2),
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            u256::from_u64(input_aptos_val)
        );


        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(0),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        // construct src swaps
        let btc_to_swap_val = 1;
        let btc_coins_to_swap = test_coins::mint<BTC>(&coin_admin, btc_to_swap_val);

        coin::register<BTC>(omniswap);
        coin::deposit<BTC>(signer::address_of(omniswap), btc_coins_to_swap);

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
        let src_swap_data = vector<NormalizedSwapData>[swap_data];

        let dst_swap_data = vector::empty<NormalizedSwapData>();

        let (_, relayer_fee, _, _) = check_relayer_fee(so_data, wormhole_data, dst_swap_data);
        let msg_fee = state::get_message_fee();
        let wormhole_fee = msg_fee + relayer_fee + input_aptos_val;

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(wormhole_fee),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        so_swap<BTC, USDT, AptosCoin, AptosCoin>(
            omniswap,
            encode_normalized_so_data(so_data),
            encode_normalized_swap_data(src_swap_data),
            encode_normalized_wormhole_data(wormhole_data),
            encode_normalized_swap_data(dst_swap_data)
        );
    }

    #[test(aptos_framework = @aptos_framework, deployer = @deployer, omniswap = @omniswap)]
    fun test_so_swap_with_dst_swap(aptos_framework: &signer, deployer: &signer, omniswap: &signer) {
        setup(aptos_framework, deployer, omniswap);

        let input_aptos_val = 100;
        let so_data = construct_so_data(
            x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            u16::from_u64(1),
            b"0x1::aptos_coin::AptosCoin",
            u16::from_u64(2),
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            u256::from_u64(input_aptos_val)
        );

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(0),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        let src_swap_data = vector::empty<NormalizedSwapData>();

        let swap_data = construct_swap_data(
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            x"2514895c72f50d8bd4b4f9b1110f0d6bd2c97526",
            x"143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            u256::from_u64(7700000000),
            // liquidswap curve
            x"6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"
        );
        let dst_swap_data = vector<NormalizedSwapData>[swap_data];

        let (_, relayer_fee, _, _) = check_relayer_fee(so_data, wormhole_data, dst_swap_data);
        let msg_fee = state::get_message_fee();
        let wormhole_fee = msg_fee + relayer_fee + input_aptos_val;

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(wormhole_fee),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        so_swap<AptosCoin, AptosCoin, AptosCoin, AptosCoin>(
            omniswap,
            encode_normalized_so_data(so_data),
            encode_normalized_swap_data(src_swap_data),
            encode_normalized_wormhole_data(wormhole_data),
            encode_normalized_swap_data(dst_swap_data)
        );
    }

    #[test(aptos_framework = @aptos_framework, deployer = @deployer, omniswap = @omniswap, liquidswap = @liquidswap)]
    fun test_so_swap_with_src_swap_and_dst_swap(aptos_framework: &signer, deployer: &signer, omniswap: &signer, liquidswap: &signer) {
        setup(aptos_framework, deployer, omniswap);
        let (coin_admin, lp_owner) = setup_liquidswap_pool();
        create_liquidswap_pool<BTC, USDT, Uncorrelated>(&coin_admin, &lp_owner, 1000, 1000000);

        let so_data = construct_so_data(
            x"4450040bc7ea55def9182559ceffc0652d88541538b30a43477364f475f4a4ed",
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af",
            u16::from_u64(1),
            b"0x11::test_coins::USDT",
            u16::from_u64(2),
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            u256::from_u64(100)
        );

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(0),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        // construct src swaps
        let btc_to_swap_val = 1;
        let btc_coins_to_swap = test_coins::mint<BTC>(&coin_admin, btc_to_swap_val);

        coin::register<BTC>(omniswap);
        coin::deposit<BTC>(signer::address_of(omniswap), btc_coins_to_swap);

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
        let src_swap_data = vector<NormalizedSwapData>[swap_data];

        let swap_data = construct_swap_data(
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            x"957Eb0316f02ba4a9De3D308742eefd44a3c1719",
            x"2514895c72f50d8bd4b4f9b1110f0d6bd2c97526",
            x"143db3CEEfbdfe5631aDD3E50f7614B6ba708BA7",
            u256::from_u64(7700000000),
            // liquidswap curve
            x"6cE9E2c8b59bbcf65dA375D3d8AB503c8524caf7"
        );
        let dst_swap_data = vector<NormalizedSwapData>[swap_data];

        let (_, relayer_fee, _, _) = check_relayer_fee(so_data, wormhole_data, dst_swap_data);
        let msg_fee = state::get_message_fee();
        let wormhole_fee = msg_fee + relayer_fee;

        let wormhole_data = construct_normalized_wormhole_data(
            u16::from_u64(2),
            u256::from_u64(100000),
            u256::from_u64(wormhole_fee),
            x"2dA7e3a7F21cCE79efeb66f3b082196EA0A8B9af"
        );

        so_swap<BTC, USDT, AptosCoin, AptosCoin>(
            omniswap,
            encode_normalized_so_data(so_data),
            encode_normalized_swap_data(src_swap_data),
            encode_normalized_wormhole_data(wormhole_data),
            encode_normalized_swap_data(dst_swap_data)
        );
    }
}
