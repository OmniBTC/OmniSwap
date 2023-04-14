module omniswap_mock::setup {

    use omniswap_mock::faucet::Faucet;
    use sui::tx_context::TxContext;
    use omniswap_mock::pool::create_pool;
    use omniswap_mock::coins::{USDC, USDT, BTC};
    use omniswap_mock::faucet;
    use sui::transfer;
    use sui::tx_context;

    const MUST_DEPLOYER: u64 = 0;

    const NOT_INITIALIZE: u64 = 1;

    const HAS_INITIALIZE: u64 = 2;

    /// A witness type for the pool creation;
    //  The pool provider's identifier.
    struct OmniSwapMock has drop {}

    public fun setup_pool(faucet: &mut Faucet, ctx: &mut TxContext) {
        let usdt = faucet::force_mint<USDT>(faucet, 100000, ctx);
        let usdc = faucet::force_mint<USDC>(faucet, 100000, ctx);
        let usdc_usdt_lp = create_pool<OmniSwapMock, USDT, USDC>(OmniSwapMock{},usdt, usdc,3, ctx);

        let btc = faucet::force_mint<BTC>(faucet, 3, ctx);
        let usdt = faucet::force_mint<USDT>(faucet, 100000, ctx);
        let btc_usdt_lp = create_pool<OmniSwapMock, BTC, USDT>(OmniSwapMock{}, btc, usdt, 3, ctx);

        let btc = faucet::force_mint<BTC>(faucet, 3, ctx);
        let usdc = faucet::force_mint<USDC>(faucet, 100000, ctx);
        let btc_usdc_lp = create_pool<OmniSwapMock, BTC, USDC>(OmniSwapMock{}, btc, usdc, 3, ctx);

        let deployer = tx_context::sender(ctx);
        transfer::public_transfer(usdc_usdt_lp, deployer);
        transfer::public_transfer(btc_usdt_lp, deployer);
        transfer::public_transfer(btc_usdc_lp, deployer);
    }
}
