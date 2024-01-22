module omniswap::so_fee_wormhole {
    use sui::clock::{Self, Clock};
    use sui::object::{Self, UID};
    use sui::table::{Self, Table};
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    const RAY: u64 = 100000000;

    /// Error Codes

    const ENOT_DEPLOYED_ADDRESS: u64 = 0;

    const EHAS_INITIALIZE: u64 = 1;

    const ENOT_INITIAL: u64 = 2;

    const EINVALID_LENGTH: u64 = 3;

    const EINVALID_ACCOUNT: u64 = 4;

    const EINVALID_CHAIN_ID: u64 = 5;

    struct PriceData has store, drop {
        // The currnet price ratio of native coins
        current_price_ratio: u64,
        // Last update timestamp
        last_update_timestamp: u64,
    }

    struct PriceManager has key {
        id: UID,
        price_data: Table<u16, PriceData>,
        owner: address
    }

    fun init(ctx: &mut TxContext) {
        transfer::share_object(PriceManager {
            id: object::new(ctx),
            price_data: table::new(ctx),
            owner: tx_context::sender(ctx)
        })
    }

    public fun get_timestamp(clock: &Clock): u64 {
        clock::timestamp_ms(clock) / 1000
    }

    public fun get_price_ratio(price_manager: &mut PriceManager, chain_id: u16): u64 {
        if (table::contains(&price_manager.price_data, chain_id)) {
            let price_data = table::borrow(&price_manager.price_data, chain_id);
            price_data.current_price_ratio
        } else {
            0
        }
    }

    public entry fun transfer_owner(price_manager: &mut PriceManager, to: address, ctx: &mut TxContext) {
        assert!(price_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);
        price_manager.owner = to;
    }

    public entry fun set_price_ratio(
        clock: &Clock,
        price_manager: &mut PriceManager,
        chain_id: u16,
        ratio: u64,
        ctx: &mut TxContext
    ) {
        assert!(price_manager.owner == tx_context::sender(ctx), EINVALID_ACCOUNT);
        if (!table::contains(&price_manager.price_data, chain_id)) {
            table::add(&mut price_manager.price_data, chain_id, PriceData {
                current_price_ratio: ratio,
                last_update_timestamp: get_timestamp(clock)
            });
        }else {
            let price_data = table::borrow_mut(&mut price_manager.price_data, chain_id);
            price_data.current_price_ratio = ratio;
            price_data.last_update_timestamp = get_timestamp(clock);
        };
    }

    #[test_only]
    public fun init_for_testing(ctx: &mut TxContext) {
        transfer::share_object(PriceManager {
            id: object::new(ctx),
            price_data: table::new(ctx),
            owner: tx_context::sender(ctx)
        })
    }
}
