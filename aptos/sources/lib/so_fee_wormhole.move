module omniswap::so_fee_wormhole {
    use std::signer;
    use std::vector;
    use aptos_framework::account;
    use aptos_framework::timestamp;
    use omniswap::serde::serialize_u64;

    const RAY: u64 = 100000000;

    /// Error Codes

    const ENOT_DEPLOYED_ADDRESS: u64 = 0x00;

    const EHAS_INITIALIZE: u64 = 0x01;

    const ENOT_INITIAL: u64 = 0x02;

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
        price_data: PriceData,
        owner: address
    }

    public fun is_initialize(dst_chain_id: u64): bool {
        exists<PriceManager>(get_resource_address(dst_chain_id))
    }

    fun is_owner(account: address, dst_chain_id: u64): bool acquires PriceManager {
        let manager = borrow_global<PriceManager>(get_resource_address(dst_chain_id));
        return manager.owner == account
    }

    public entry fun transfer_owner(account: &signer, dst_chain_id: u64, to: address) acquires PriceManager {
        assert!(is_owner(signer::address_of(account), dst_chain_id), EINVALID_ACCOUNT);
        let manager = borrow_global_mut<PriceManager>(get_resource_address(dst_chain_id));
        manager.owner = to;
    }

    fun get_resource_address(dst_chain_id: u64): address {
        let seed = vector::empty<u8>();
        serialize_u64(&mut seed, dst_chain_id);
        account::create_resource_address(&@omniswap, seed)
    }

    public entry fun initialize(account: &signer, dst_chain_id: u64) {
        assert!(signer::address_of(account) == @omniswap, ENOT_DEPLOYED_ADDRESS);
        assert!(!is_initialize(dst_chain_id), EHAS_INITIALIZE);

        let seed = vector::empty<u8>();
        serialize_u64(&mut seed, dst_chain_id);
        let (resource_signer, _) = account::create_resource_account(account, seed);

        move_to(&resource_signer, PriceManager {
            price_data: PriceData{
                current_price_ratio: 0,
                last_update_timestamp: timestamp::now_seconds()
            },
            owner: @omniswap
        })
    }

    #[legacy_entry_fun]
    public entry fun update_price_ratio(chain_id: u64): u64 acquires PriceManager {
        get_price_ratio(chain_id)
    }

    public entry fun set_price_ratio(account: &signer, chain_id: u64, ratio: u64) acquires PriceManager {
        assert!(is_initialize(chain_id), EHAS_INITIALIZE);
        assert!(is_owner(signer::address_of(account), chain_id), EINVALID_ACCOUNT);

        let manager = borrow_global_mut<PriceManager>(get_resource_address(chain_id));
        manager.price_data.current_price_ratio = ratio;
        manager.price_data.last_update_timestamp = timestamp::now_seconds();
    }

    #[legacy_entry_fun]
    public entry fun get_price_ratio(chain_id: u64): u64 acquires PriceManager {
        assert!(is_initialize(chain_id), EHAS_INITIALIZE);
        let manager = borrow_global_mut<PriceManager>(get_resource_address(chain_id));
        manager.price_data.current_price_ratio
    }
}
