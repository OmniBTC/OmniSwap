module omniswap::swap {
    use omniswap::cross::{SwapData, Self};
    use liquidswap::curves::{Stable, Uncorrelated};
    use std::vector;
    use omniswap::serde;
    use aptos_framework::coin;
    use omniswap::u256;
    use liquidswap::router;
    use aptos_framework::coin::Coin;

    const EINVALID_LENGTH: u64 = 0x00;

    const EINVALID_SWAP_ROUTER: u64 = 0x01;

    const EINVALID_SWAP_TOKEN: u64 = 0x02;

    const EINVALID_SWAP_CURVE: u64 = 0x03;

    public fun right_token<X>(token: vector<u8>): bool {
        let data = vector::empty();
        serde::serialize_type<X>(&mut data);
        if (data == token) {
            true
        }else {
            false
        }
    }

    public fun swap_by_account<X, Y>(account: &signer, data: SwapData): Coin<Y> {
        if (@liquidswap == serde::deserialize_address(&cross::swap_call_to(data))) {
            assert!(right_token<X>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
            assert!(right_token<Y>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);
            let coin_val = u256::as_u64(cross::swap_from_amount(data));
            let coin_x = coin::withdraw<X>(account, coin_val);

            if (right_token<Stable>(cross::swap_call_data(data))) {
                router::swap_exact_coin_for_coin<X, Y, Stable>(
                    coin_x,
                    0,
                )
            }else if (right_token<Uncorrelated>(cross::swap_call_data(data))) {
                router::swap_exact_coin_for_coin<X, Y, Uncorrelated>(
                    coin_x,
                    0,
                )
            }else {
                abort EINVALID_SWAP_CURVE
            }
        }else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_by_coin<X, Y>(coin_x: Coin<X>, data: SwapData): Coin<Y> {
        if (@liquidswap == serde::deserialize_address(&cross::swap_call_to(data))) {
            assert!(right_token<X>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
            assert!(right_token<Y>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

            if (right_token<Stable>(cross::swap_call_data(data))) {
                router::swap_exact_coin_for_coin<X, Y, Stable>(
                    coin_x,
                    0,
                )
            }else if (right_token<Uncorrelated>(cross::swap_call_data(data))) {
                router::swap_exact_coin_for_coin<X, Y, Uncorrelated>(
                    coin_x,
                    0,
                )
            }else {
                abort EINVALID_SWAP_CURVE
            }
        }else {
            abort EINVALID_SWAP_ROUTER
        }
    }

    public fun swap_two<X, Y>(account: &signer, swap_data: vector<SwapData>): Coin<Y> {
        assert!(vector::length(&swap_data) == 1, EINVALID_LENGTH);
        swap_by_account<X, Y>(account, *vector::borrow(&mut swap_data, 0))
    }

    public fun swap_three<X, Y, Z>(account: &signer, swap_data: vector<SwapData>): Coin<Z> {
        assert!(vector::length(&swap_data) == 2, EINVALID_LENGTH);
        let coin_y = swap_by_account<X, Y>(account, *vector::borrow(&mut swap_data, 0));
        swap_by_coin<Y, Z>(coin_y, *vector::borrow(&mut swap_data, 1))
    }

    public fun swap_four<X, Y, Z, M>(account: &signer, swap_data: vector<SwapData>): Coin<M> {
        assert!(vector::length(&swap_data) == 3, EINVALID_LENGTH);
        let coin_y = swap_by_account<X, Y>(account, *vector::borrow(&mut swap_data, 0));
        let coin_z = swap_by_coin<Y, Z>(coin_y, *vector::borrow(&mut swap_data, 1));
        swap_by_coin<Z, M>(coin_z, *vector::borrow(&mut swap_data, 2))
    }
}
