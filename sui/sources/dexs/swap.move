module omniswap::swap {
    use std::type_name;
    use std::vector;
    use omniswap::serde;
    use omniswap::cross;
    use sui::coin::Coin;
    use omniswap::cross::NormalizedSwapData;
    use omniswap_mock::pool;
    use omniswap_mock::pool::Pool;
    use sui::tx_context::TxContext;
    use omniswap_mock::setup::OmniSwapMock;

    // Swap call data delimiter, represent ","
    const DELIMITER: u8 = 44;

    /// Error Codes
    const EINVALID_LENGTH: u64 = 0x00;

    const EINVALID_SWAP_ROUTER: u64 = 0x01;

    const EINVALID_SWAP_TOKEN: u64 = 0x02;

    const EINVALID_SWAP_CURVE: u64 = 0x03;

    const EINVALID_SWAP_ROUTER_DELEGATE: u64 = 0x04;

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

    /// Coins need to be removed from the account first and then swap using the coins.
    public fun swap_by_coin<X, Y>(pool: &mut Pool<OmniSwapMock, X, Y> , input_coin: Coin<X>, data: NormalizedSwapData, ctx: &mut TxContext): Coin<Y> {
        assert!(@omniswap_mock == serde::deserialize_address(&cross::swap_call_to(data)), EINVALID_SWAP_ROUTER);
        assert!(right_type<X>(cross::swap_sending_asset_id(data)), EINVALID_SWAP_TOKEN);
        assert!(right_type<Y>(cross::swap_receiving_asset_id(data)), EINVALID_SWAP_TOKEN);

        let raw_call_data = cross::swap_call_data(data);
        let min_amount = 0;
        let (flag, index) = vector::index_of(&raw_call_data, &DELIMITER);
        let call_data;
        if (flag) {
            call_data = serde::vector_slice(&raw_call_data, 0, index);
            let len = vector::length(&raw_call_data);
            if (index + 1 < len) {
                min_amount = ascii_to_u64(serde::vector_slice(&raw_call_data, index + 1, len));
            }
        }else {
            call_data = raw_call_data;
        };

        pool::swap_token_x(pool, input_coin, ctx)
    }

    public fun swap_two_by_coin<X, Y>(pool: &mut Pool<OmniSwapMock, X, Y>, coins: Coin<X>, swap_data: vector<NormalizedSwapData>, ctx: &mut TxContext): Coin<Y> {
        assert!(vector::length(&swap_data) == 1, EINVALID_LENGTH);
        swap_by_coin<X, Y>(pool, coins, *vector::borrow(&mut swap_data, 0), ctx)
    }

    public fun swap_three_by_coin<X, Y, Z>(pool_xy: &mut Pool<OmniSwapMock, X, Y>, pool_yz: &mut Pool<OmniSwapMock, Y, Z>,coins: Coin<X>, swap_data: vector<NormalizedSwapData>, ctx: &mut TxContext): Coin<Z> {
        assert!(vector::length(&swap_data) == 2, EINVALID_LENGTH);
        let coin_y = swap_by_coin<X, Y>(pool_xy, coins, *vector::borrow(&mut swap_data, 0), ctx);
        swap_by_coin<Y, Z>(pool_yz, coin_y, *vector::borrow(&mut swap_data, 1), ctx)
    }


    public fun swap_four_by_coin<X, Y, Z, M>(pool_xy: &mut Pool<OmniSwapMock, X, Y>, pool_yz: &mut Pool<OmniSwapMock, Y, Z>, pool_zm: &mut Pool<OmniSwapMock, Z,M>, coins: Coin<X>, swap_data: vector<NormalizedSwapData>, ctx: &mut TxContext): Coin<M> {
        assert!(vector::length(&swap_data) == 3, EINVALID_LENGTH);
        let coin_y = swap_by_coin<X, Y>(pool_xy, coins, *vector::borrow(&mut swap_data, 0), ctx);
        let coin_z = swap_by_coin<Y, Z>(pool_yz, coin_y, *vector::borrow(&mut swap_data, 1), ctx);
        swap_by_coin<Z, M>(pool_zm, coin_z, *vector::borrow(&mut swap_data, 2), ctx)
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
