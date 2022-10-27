module omniswap_mock::setup {

    use aptos_framework::managed_coin;
    use aptos_framework::coin;
    use aptos_framework::account;
    use liquidswap::scripts;
    use liquidswap::curves::{Uncorrelated, Stable};
    use std::signer;
    use liquidswap::liquidity_pool;
    use aptos_framework::aptos_coin::AptosCoin;
    use liquidswap::coin_helper;

    const SEED: vector<u8> = b"omniswap_mock";

    const MUST_DEPLOYER: u64 = 0;

    const NOT_INITIALIZE: u64 = 1;

    const HAS_INITIALIZE: u64 = 2;

    struct XBTC {}

    struct USDT {}

    struct USDC {}

    struct SignerCapability has key {
        signer_cap: account::SignerCapability,
        deployer: address,
    }

    fun get_resource_address(): address {
        account::create_resource_address(&@omniswap_mock, SEED)
    }

    public entry fun initialize(account: &signer) acquires SignerCapability {
        assert!(signer::address_of(account) == @omniswap_mock, MUST_DEPLOYER);
        let resource = get_resource_address();
        let resource_signer;
        if (exists<SignerCapability>(resource)) {
            resource_signer = get_resouce_signer();
        }else {
            let signer_cap;
            (resource_signer, signer_cap) = account::create_resource_account(account, SEED);
            move_to(&resource_signer, SignerCapability { signer_cap, deployer: @omniswap_mock });
        };

        if (!coin::is_coin_initialized<XBTC>()) {
            managed_coin::initialize<XBTC>(account, b"XBTC", b"XBTC", 8, true);
        };
        if (!coin::is_coin_initialized<USDC>()) {
            managed_coin::initialize<USDC>(account, b"USDC", b"USDC", 8, true);
        };
        if (!coin::is_coin_initialized<USDT>()) {
            managed_coin::initialize<USDT>(account, b"USDT", b"USDT", 8, true);
        };

        if (!coin::is_account_registered<XBTC>(resource)) {
            coin::register<XBTC>(&resource_signer);
        };
        if (!coin::is_account_registered<USDC>(resource)) {
            coin::register<USDC>(&resource_signer);
        };
        if (!coin::is_account_registered<USDT>(resource)) {
            coin::register<USDT>(&resource_signer);
        };

        managed_coin::mint<XBTC>(account, resource, 1000000000000000000);
        managed_coin::mint<USDC>(account, resource, 1000000000000000000);
        managed_coin::mint<USDT>(account, resource, 1000000000000000000);
    }

    fun get_resouce_signer(): signer acquires SignerCapability {
        assert!(exists<SignerCapability>(get_resource_address()), NOT_INITIALIZE);
        let resource = get_resource_address();
        let deploying_cap = borrow_global<SignerCapability>(resource);
        account::create_signer_with_capability(&deploying_cap.signer_cap)
    }

    public entry fun add_liquidity<X, Y, Curve>(account: &signer, x_val: u64, y_val: u64) {
        if (coin_helper::is_sorted<X, Y>()) {
            if (!liquidity_pool::is_pool_exists<X, Y, Curve>()) {
                scripts::register_pool<X, Y, Curve>(account);
            };
            if (x_val > 0 || y_val > 0) {
                scripts::add_liquidity<X, Y, Curve>(account, x_val, 0, y_val, 0);
            }
        }else {
            if (!liquidity_pool::is_pool_exists<Y, X, Curve>()) {
                scripts::register_pool<Y, X, Curve>(account);
            };
            if (x_val > 0 || y_val > 0) {
                scripts::add_liquidity<Y, X, Curve>(account, x_val, 0, y_val, 0);
            }
        }
    }

    public entry fun setup_omniswap_enviroment(account: &signer) acquires SignerCapability {
        let account_addr = signer::address_of(account);
        if (!coin::is_account_registered<XBTC>(account_addr)) {
            coin::register<XBTC>(account);
        };
        if (!coin::is_account_registered<USDC>(account_addr)) {
            coin::register<USDC>(account);
        };
        if (!coin::is_account_registered<USDT>(account_addr)) {
            coin::register<USDT>(account);
        };
        coin::transfer<XBTC>(&get_resouce_signer(), account_addr, 10000000000);
        coin::transfer<USDC>(&get_resouce_signer(), account_addr, 20000 * 10000000000);
        coin::transfer<USDT>(&get_resouce_signer(), account_addr, 20000 * 10000000000);

        add_liquidity<XBTC, AptosCoin, Uncorrelated>(account, 10000000, 100000000);
        add_liquidity<USDT, XBTC, Uncorrelated>(account, 20000 * 1000000000, 1000000000);
        add_liquidity<USDC, USDT, Stable>(account, 10000000000, 10000000000);
    }
}
