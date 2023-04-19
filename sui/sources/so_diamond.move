module omniswap::so_diamond {
    use std::type_name;
    use std::vector;

    use deepbook::clob::Pool;
    use omniswap::so_fee_wormhole::PriceManager;
    use omniswap::wormhole_facet::{Self, Storage, WormholeFee};
    use sui::clock::Clock;
    use sui::coin::Coin;
    use sui::sui::SUI;
    use sui::tx_context::TxContext;
    use token_bridge::state::State as TokenBridgeState;
    use wormhole::state::State as WormholeState;

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized.
    public entry fun so_swap_via_wormhole<X>(
        wormhole_state: &mut WormholeState,
        token_bridge_state: &mut TokenBridgeState,
        storage: &mut Storage,
        clock: &Clock,
        price_manager: &mut PriceManager,
        wromhole_fee: &mut WormholeFee,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>,
        coins_x: vector<Coin<X>>,
        coins_sui: vector<Coin<SUI>>,
        ctx: &mut TxContext
    ) {
        if (type_name::get<X>() != type_name::get<SUI>()) {
            wormhole_facet::so_swap_without_swap<X>(
                wormhole_state,
                token_bridge_state,
                storage,
                clock,
                price_manager,
                wromhole_fee,
                so_data,
                swap_data_src,
                wormhole_data,
                swap_data_dst,
                coins_x,
                coins_sui,
                ctx
            );
        }else {
            vector::destroy_empty(coins_x);
            wormhole_facet::so_swap_from_sui(
                wormhole_state,
                token_bridge_state,
                storage,
                clock,
                price_manager,
                wromhole_fee,
                so_data,
                swap_data_src,
                wormhole_data,
                swap_data_dst,
                coins_sui,
                ctx
            );
        }
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap<X, Y>(
        storage: &mut Storage,
        token_bridge_state: &mut TokenBridgeState,
        wormhole_state: &WormholeState,
        wormhole_fee: &mut WormholeFee,
        pool_xy: &mut Pool<X, Y>,
        vaa: vector<u8>,
        clock: &Clock,
        ctx: &mut TxContext
    ) {
        wormhole_facet::complete_so_swap<X, Y>(
            storage,
            token_bridge_state,
            wormhole_state,
            wormhole_fee,
            pool_xy,
            vaa,
            clock,
            ctx
        );
    }
}
