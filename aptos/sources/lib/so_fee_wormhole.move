module omniswap::so_fee_wormhole {

    use aptos_std::table::{Table, Self};
    use omniswap::u16::{U16, Self};
    use std::signer;
    use aptos_framework::account;
    use aptos_framework::timestamp;

    const RAY: u64 = 100000000;

    const SEED: vector<u8> = b"wormhole_fee";

    /// Error Codes

    const ENOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const EHAS_Initialize: u64 = 0x01;

    const ENOT_Initial: u64 = 0x02;

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
        price_data: Table<U16, PriceData>,
        owner: address
    }

    public fun is_initialize(): bool {
        exists<PriceManager>(get_resource_address())
    }

    fun is_owner(account: address): bool acquires PriceManager {
        let manager = borrow_global<PriceManager>(get_resource_address());
        return manager.owner == account
    }

    fun get_resource_address(): address {
        account::create_resource_address(&@omniswap, SEED)
    }

    public entry fun initialize(account: &signer) {
        assert!(signer::address_of(account) == @omniswap, ENOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(), EHAS_Initialize);

        let (resource_signer, _) = account::create_resource_account(account, SEED);

        move_to(&resource_signer, PriceManager {
            price_data: table::new(),
            owner: @omniswap
        })
    }

    public entry fun update_price_ratio(chain_id: u64): u64 acquires PriceManager {
        get_price_ratio(chain_id)
    }

    public entry fun set_price_ratio(account: &signer, chain_id: u64, ratio: u64) acquires PriceManager {
        assert!(is_initialize(), ENOT_Initial);
        assert!(is_owner(signer::address_of(account)), EINVALID_ACCOUNT);

        let manager = borrow_global_mut<PriceManager>(get_resource_address());

        let chain_id = u16::from_u64(chain_id);

        table::upsert<U16, PriceData>(
            &mut manager.price_data,
            chain_id,
            PriceData { current_price_ratio: ratio, last_update_timestamp: timestamp::now_seconds() });
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
}
