module omniswap::external_interface {

    use omniswap::wormhole_facet::{Self, Storage};
    use cetus_clmm::pool::{Pool as CetusPool};
    use omniswap::swap;
    use omniswap::so_fee_wormhole::PriceManager;
    use wormhole::state::{State as WormholeState};
    use sui::event;

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
}
