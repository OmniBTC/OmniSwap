module omniswap::helper {
    use sui::coin::Coin;
    use std::vector;

    public fun make_vector<CoinType>(
        coin: Coin<CoinType>
    ): vector<Coin<CoinType>> {
        let result = vector::empty<Coin<CoinType>>();
        vector::push_back(&mut result, coin);
        result
    }
}
