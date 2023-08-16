module omniswap::external_interface {

    use omniswap::wormhole_facet::{Self, Storage};
    use cetus_clmm::pool::{Pool as CetusPool};
    use deepbook::clob_v2::Pool as DeepbookV2Pool;
    use omniswap::swap;
    use omniswap::so_fee_wormhole::PriceManager;
    use wormhole::state::{State as WormholeState};
    use sui::event;
    use deepbook::clob_v2;
    use std::option;
    use sui::clock::Clock;

    struct Relayer has copy, drop {
        src_fee: u64,
        consume_value: u64,
        dst_max_gas: u256
    }

    struct AmountOut has copy, drop {
        amount: u64
    }

    struct AmountIn has copy, drop {
        amount: u64
    }

    struct DeepBookMarketPrice  has copy, drop {
        best_bid_price: u64,
        best_ask_price: u64
    }

    struct DeepBookLevelBidSide  has copy, drop {
        price: vector<u64>,
        depth: vector<u64>
    }

    struct DeepBookLevelAskSide  has copy, drop {
        price: vector<u64>,
        depth: vector<u64>
    }

    public fun estimate_relayer_fee(
        storage: &mut Storage,
        state: &mut WormholeState,
        price_manager: &mut PriceManager,
        so_data: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
    ) {
        let (src_fee, consume_value, dst_max_gas) = wormhole_facet::estimate_relayer_fee(
            storage,
            state,
            price_manager,
            so_data,
            wormhole_data,
            swap_data_dst
        );
        event::emit(
            Relayer {
                src_fee,
                consume_value,
                dst_max_gas
            }
        )
    }

    public fun get_cetus_amount_in<BaseAsset, QuoteAsset>(
        pool: &CetusPool<BaseAsset, QuoteAsset>,
        a2b: bool,
        amount: u64,
    ) {
        let amount = swap::get_cetus_amount_in(pool, a2b, amount);
        event::emit(AmountIn {
            amount
        });
    }

    public fun get_cetus_amount_out<BaseAsset, QuoteAsset>(
        pool: &CetusPool<BaseAsset, QuoteAsset>,
        a2b: bool,
        amount: u64,
    ) {
        let amount = swap::get_cetus_amount_out(pool, a2b, amount);
        event::emit(AmountOut { amount });
    }

    /// Query the market price of order book
    /// returns (best_bid_price, best_ask_price) if there exists
    /// bid/ask order in the order book, otherwise returns None
    public fun get_market_price<BaseAsset, QuoteAsset>(
        pool: &DeepbookV2Pool<BaseAsset, QuoteAsset>
    ) {
        let (best_bid_price, best_ask_price) = clob_v2::get_market_price<BaseAsset, QuoteAsset>(pool);
        let bid_price;
        if (option::is_some<u64>(&best_bid_price)) {
            bid_price = option::destroy_some<u64>(best_bid_price);
        }else {
            bid_price = 0;
        };
        let ask_price;
        if (option::is_some<u64>(&best_ask_price)) {
            ask_price = option::destroy_some<u64>(best_ask_price);
        }else {
            ask_price = 0;
        };
        event::emit(
            DeepBookMarketPrice {
                best_bid_price: bid_price,
                best_ask_price: ask_price
            }
        )
    }

    /// Enter a price range and return the level2 order depth of all valid prices within this price range in bid side
    /// returns two vectors of u64
    /// The previous is a list of all valid prices
    /// The latter is the corresponding depth list
    public fun get_level2_book_status_bid_side<BaseAsset, QuoteAsset>(
        pool: &DeepbookV2Pool<BaseAsset, QuoteAsset>,
        price_low: u64,
        price_high: u64,
        clock: &Clock
    ) {
        let (price, depth) = clob_v2::get_level2_book_status_bid_side<BaseAsset, QuoteAsset>(
            pool,
            price_low,
            price_high,
            clock
        );

        event::emit(
            DeepBookLevelBidSide {
                price,
                depth
            }
        )
    }

    /// Enter a price range and return the level2 order depth of all valid prices within this price range in ask side
    /// returns two vectors of u64
    /// The previous is a list of all valid prices
    /// The latter is the corresponding depth list
    public fun get_level2_book_status_ask_side<BaseAsset, QuoteAsset>(
        pool: &DeepbookV2Pool<BaseAsset, QuoteAsset>,
        price_low: u64,
        price_high: u64,
        clock: &Clock
    ) {
        let (price, depth) = clob_v2::get_level2_book_status_ask_side<BaseAsset, QuoteAsset>(
            pool,
            price_low,
            price_high,
            clock
        );

        event::emit(
            DeepBookLevelAskSide {
                price,
                depth
            }
        )
    }
}
