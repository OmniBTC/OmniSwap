module omniswap::swap {
    use std::type_name;
    use std::vector;

    use deepbook::clob::{Self, Pool};
    use omniswap::cross::{Self, NormalizedSwapData};
    use omniswap::serde;
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

    /// Swap Name
    const DEEPBOOK_SWAP: vector<u8> = b"DeepBook";

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

    public fun swap_for_base_asset<BaseAsset, QuoteAsset>(
        pool: &mut Pool<BaseAsset, QuoteAsset>,
        input_coin: Coin<QuoteAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        // assert!(right_type<QuoteAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        // assert!(right_type<BaseAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

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
            let min_amount = swap_quote_amount * RAY / input_quote_amount * min_amount / RAY;
            assert!(swap_amount >= min_amount, ESWAP_AMOUNT_TOO_LOW);
            (base_asset, quote_asset, swap_amount)
        } else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_for_quote_asset<BaseAsset, QuoteAsset>(
        pool: &mut Pool<BaseAsset, QuoteAsset>,
        input_coin: Coin<BaseAsset>,
        data: NormalizedSwapData,
        clock: &Clock,
        ctx: &mut TxContext
    ): (Coin<BaseAsset>, Coin<QuoteAsset>, u64) {
        // assert!(right_type<BaseAsset>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        // assert!(right_type<QuoteAsset>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

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
            let min_amount = swap_base_amount * RAY / input_base_amount * min_amount / RAY;
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
