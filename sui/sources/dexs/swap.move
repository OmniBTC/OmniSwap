module omniswap::swap {
    use std::type_name;
    use std::vector;

    use cetus_clmm::config::GlobalConfig;
    use cetus_clmm::pool::{Self as cetus_pool, Pool as CetusPool};
    use deepbook::clob;
    use deepbook::clob::Pool as DeepbookPool;
    use deepbook::clob_v2;
    use deepbook::clob_v2::Pool as DeepbookV2Pool;
    use deepbook::custodian_v2::AccountCap;
    use omniswap::cross::{Self, NormalizedSwapData};
    use omniswap::serde;
    use sui::balance;
    use sui::clock::Clock;
    use sui::coin::{Self, Coin};
    use sui::tx_context::TxContext;

    const RAY: u64 = 100000000;

    // Swap call data delimiter, represent ","
    const DELIMITER: u8 = 44;

    /// Error Codes
    const EINVALID_LENGTH: u64 = 0;

    const EINVALID_SWAP_ROUTER: u64 = 1;

    const EINVALID_SWAP_TOKEN: u64 = 2;

    const EINVALID_SWAP_CURVE: u64 = 3;

    const EINVALID_SWAP_ROUTER_DELEGATE: u64 = 4;

    const ESWAP_AMOUNT_TOO_LOW: u64 = 5;

    const EREPAY_NOT_ENOUGH: u64 = 6;

    const MIN_SQRT_PRICE: u128 = 4295048016;

    const MAX_SQRT_PRICE: u128 = 79226673515401279992447579055;

    /// Swap Name
    const DEEPBOOK_SWAP: vector<u8> = b"DeepBook";
    const DEEPBOOK_V2_SWAP: vector<u8> = b"DeepBookV2";
    const CETUS_SWAP: vector<u8> = b"Cetus";

    /// Ensuring the origin of tokens
    public fun right_type<X>(token: vector<u8>): bool {
        let data = type_name::get<X>();
        let data = type_name::into_string(data);
        let data = std::ascii::into_bytes(data);
        if (data == token) {
            true
        }else {
            false
        }
    }

    public fun get_cetus_amount_in<BaseAsset, QuoteAsset>(
        pool: &CetusPool<BaseAsset, QuoteAsset>,
        a2b: bool,
        amount: u64,
    ): u64 {
        let calculated_result = cetus_pool::calculate_swap_result<BaseAsset, QuoteAsset>(
            pool,
            a2b,
            false,
            amount,
        );
        cetus_pool::calculated_swap_result_amount_in(&calculated_result)
    }

    public fun get_cetus_amount_out<BaseAsset, QuoteAsset>(
        pool: &CetusPool<BaseAsset, QuoteAsset>,
        a2b: bool,
        amount: u64,
    ): u64 {
        let calculated_result = cetus_pool::calculate_swap_result<BaseAsset, QuoteAsset>(
            pool,
            a2b,
            true,
            amount,
        );
        cetus_pool::calculated_swap_result_amount_out(&calculated_result)
    }

    public fun swap_for_base_asset_by_cetus<BaseAsset, QuoteAsset>(
        config: &GlobalConfig,
        pool: &mut CetusPool<BaseAsset, QuoteAsset>,
        input_coin: Coin<QuoteAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<QuoteAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<BaseAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };
        assert!(swap_name == CETUS_SWAP, EINVALID_SWAP_ROUTER);

        let input_amount = coin::value(&input_coin);
        let input_balance = coin::into_balance(input_coin);
        let (base, quote, flash) = cetus_pool::flash_swap<BaseAsset, QuoteAsset>(
            config,
            pool,
            false,
            true,
            input_amount,
            MAX_SQRT_PRICE,
            clock
        );
        let repay_amount = cetus_pool::swap_pay_amount<BaseAsset, QuoteAsset>(
            &flash
        );
        assert!(repay_amount <= input_amount, EREPAY_NOT_ENOUGH);
        let repay_coin = balance::split(&mut input_balance, repay_amount);
        balance::join(&mut quote, input_balance);

        cetus_pool::repay_flash_swap<BaseAsset, QuoteAsset>(
            config,
            pool,
            balance::zero(),
            repay_coin,
            flash
        );

        let min_amount = (((repay_amount as u256) * (RAY as u256) / (input_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
        let swap_amount = balance::value(&base);
        assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
        (coin::from_balance(base, ctx), coin::from_balance(quote, ctx), swap_amount)
    }

    public fun swap_for_quote_asset_by_cetus<BaseAsset, QuoteAsset>(
        config: &GlobalConfig,
        pool: &mut CetusPool<BaseAsset, QuoteAsset>,
        input_coin: Coin<BaseAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<BaseAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<QuoteAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };
        assert!(swap_name == CETUS_SWAP, EINVALID_SWAP_ROUTER);

        let input_amount = coin::value(&input_coin);
        let input_balance = coin::into_balance(input_coin);
        let (base, quote, flash) = cetus_pool::flash_swap<BaseAsset, QuoteAsset>(
            config,
            pool,
            true,
            true,
            input_amount,
            MIN_SQRT_PRICE,
            clock
        );
        let repay_amount = cetus_pool::swap_pay_amount<BaseAsset, QuoteAsset>(
            &flash
        );
        assert!(repay_amount <= input_amount, EREPAY_NOT_ENOUGH);
        let repay_coin = balance::split(&mut input_balance, repay_amount);
        balance::join(&mut base, input_balance);
        cetus_pool::repay_flash_swap<BaseAsset, QuoteAsset>(
            config,
            pool,
            repay_coin,
            balance::zero(),
            flash
        );

        let min_amount = (((repay_amount as u256) * (RAY as u256) / (input_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
        let swap_amount = balance::value(&quote);
        assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
        (coin::from_balance(base, ctx), coin::from_balance(quote, ctx), swap_amount)
    }

    public fun swap_for_base_asset_by_deepbook<BaseAsset, QuoteAsset>(
        pool: &mut DeepbookPool<BaseAsset, QuoteAsset>,
        input_coin: Coin<QuoteAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<QuoteAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<BaseAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };

        if (swap_name == DEEPBOOK_SWAP) {
            let input_quote_amount = coin::value(&input_coin);
            let (base_asset, quote_asset, swap_amount) = clob::swap_exact_quote_for_base(
                pool,
                input_quote_amount,
                clock,
                input_coin,
                ctx
            );
            let left_quote_amount = coin::value(&quote_asset);
            let swap_quote_amount = input_quote_amount - left_quote_amount;
            let min_amount = (((swap_quote_amount as u256) * (RAY as u256) / (input_quote_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
            assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
            (base_asset, quote_asset, swap_amount)
        }else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_for_quote_asset_by_deepbook<BaseAsset, QuoteAsset>(
        pool: &mut DeepbookPool<BaseAsset, QuoteAsset>,
        input_coin: Coin<BaseAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<BaseAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<QuoteAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };

        if (swap_name == DEEPBOOK_SWAP) {
            let input_base_amount = coin::value(&input_coin);
            let quote_coin = coin::zero<QuoteAsset>(ctx);
            let (base_asset, quote_asset, swap_amount) = clob::swap_exact_base_for_quote(
                pool,
                input_base_amount,
                input_coin,
                quote_coin,
                clock,
                ctx
            );
            let left_base_amount = coin::value(&base_asset);
            let swap_base_amount = input_base_amount - left_base_amount;
            let min_amount = (((swap_base_amount as u256) * (RAY as u256) / (input_base_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
            assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
            (base_asset, quote_asset, swap_amount)
        } else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_for_base_asset_by_deepbook_v2<BaseAsset, QuoteAsset>(
        pool: &mut DeepbookV2Pool<BaseAsset, QuoteAsset>,
        input_coin: Coin<QuoteAsset>,
        account_cap: &AccountCap,
        client_order_id: u64,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<QuoteAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<BaseAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };

        if (swap_name == DEEPBOOK_V2_SWAP) {
            let input_quote_amount = coin::value(&input_coin);
            let (base_asset, quote_asset, swap_amount) = clob_v2::swap_exact_quote_for_base(
                pool,
                client_order_id,
                account_cap,
                input_quote_amount,
                clock,
                input_coin,
                ctx
            );
            let left_quote_amount = coin::value(&quote_asset);
            let swap_quote_amount = input_quote_amount - left_quote_amount;
            let min_amount = (((swap_quote_amount as u256) * (RAY as u256) / (input_quote_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
            assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
            (base_asset, quote_asset, swap_amount)
        }else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_for_quote_asset_by_deepbook_v2<BaseAsset, QuoteAsset>(
        pool: &mut DeepbookV2Pool<BaseAsset, QuoteAsset>,
        input_coin: Coin<BaseAsset>,
        account_cap: &AccountCap,
        client_order_id: u64,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        assert!(right_type<BaseAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<QuoteAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let swap_name;
        if (flag) {
            swap_name = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            swap_name = raw_call_data;
        };

        if (swap_name == DEEPBOOK_V2_SWAP) {
            let input_base_amount = coin::value(&input_coin);
            let quote_coin = coin::zero<QuoteAsset>(ctx);
            let (base_asset, quote_asset, swap_amount) = clob_v2::swap_exact_base_for_quote(
                pool,
                client_order_id,
                account_cap,
                input_base_amount,
                input_coin,
                quote_coin,
                clock,
                ctx
            );
            let left_base_amount = coin::value(&base_asset);
            let swap_base_amount = input_base_amount - left_base_amount;
            let min_amount = (((swap_base_amount as u256) * (RAY as u256) / (input_base_amount as u256) * (min_amount as u256) / (RAY as u256)) as u64);
            assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
            (base_asset, quote_asset, swap_amount)
        } else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun ascii_to_u64(data: vector<u8>): u64 {
        let len = vector::length(&data);
        let amount = 0;
        let i = 0;
        while (i < len) {
            let m = *vector::borrow(&data, i);
            if ((m < 48) || (m > 57)) {
                return 0
            };
            let d = ((m - 48) as u64);
            amount = amount * 10 + d;
            i = i + 1;
        };
        amount
    }
}
