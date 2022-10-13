module omniswap::so_fee_wormhole_v1 {

    use aptos_std::table::{Table, Self};
    use omniswap::u16::{U16, Self};
    use std::signer;
    use aptos_framework::account;
    use aptos_framework::timestamp;

    const RAY: u64 = 100000000;

    const SEED: vector<u8> = b"wormhole_fee";

    const NOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const HAS_initialize: u64 = 0x01;

    const NOT_initialize: u64 = 0x02;

    const EINVALID_LENGTH: u64 = 0x03;

    const EINVALID_ACCOUNT: u64 = 0x04;

    const EINVALID_CHAIN_ID: u64 = 0x04;

    struct PriceData has store, drop {
        // The currnet price ratio of native coins
        current_price_ratio: u64,
        // Last update timestamp
        last_update_timestamp: u64,
    }

    struct PriceManager has key {
        price_data: Table<U16, PriceData>
    }

    fun get_resource_address(): address {
        account::create_resource_address(&@omniswap, SEED)
    }

    public fun is_initialize(): bool {
        exists<PriceManager>(get_resource_address())
    }

    // Update permission
    fun is_approve(account: address): bool {
        // todo! add permission manage
        account == @omniswap
    }

    public entry fun initialize(account: &signer) {
        assert!(signer::address_of(account) == @omniswap, NOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(), HAS_initialize);

        let (resource_signer, _) = account::create_resource_account(account, SEED);

        move_to(&resource_signer, PriceManager { price_data: table::new() })
    }

    public entry fun get_price_ratio(chain_id: u64): u64 acquires PriceManager {
        let manager = borrow_global_mut<PriceManager>(get_resource_address());

        let chain_id = u16::from_u64(chain_id);
        if (table::contains(&manager.price_data, chain_id)) {
            table::borrow(&manager.price_data, chain_id).current_price_ratio
        }else {
            0
        }
    }

    public entry fun update_price_ratio(chain_id: u64): u64 acquires PriceManager {
        get_price_ratio(chain_id)
    }

    public entry fun set_price_ratio(account: &signer, chain_id: u64, ratio: u64) acquires PriceManager {
        assert!(is_initialize(), NOT_initialize);
        assert!(is_approve(signer::address_of(account)), EINVALID_ACCOUNT);

        let manager = borrow_global_mut<PriceManager>(get_resource_address());

        let chain_id = u16::from_u64(chain_id);

        table::upsert<U16, PriceData>(
            &mut manager.price_data,
            chain_id,
            PriceData { current_price_ratio: ratio, last_update_timestamp: timestamp::now_seconds() });
    }
}
