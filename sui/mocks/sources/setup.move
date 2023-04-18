module omniswap_mock::setup {
    use omniswap_mock::pool::create_pool;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};
    use test_coins::btc::BTC;
    use test_coins::faucet::{Self, Faucet};
    use test_coins::usdc::USDC;
    use test_coins::usdt::USDT;

    const MUST_DEPLOYER: u64 = 0;

    const NOT_INITIALIZE: u64 = 1;

    const HAS_INITIALIZE: u64 = 2;

    /// A witness type for the pool creation;
    //  The pool provider's identifier.
    struct OmniSwapMock has drop {}

    public entry fun setup_pool(faucet: &mut Faucet, ctx: &mut TxContext) {
        let usdt = faucet::force_mint<USDT>(faucet, 100000, ctx);
        let usdc = faucet::force_mint<USDC>(faucet, 100000, ctx);
        let usdc_usdt_lp = create_pool<OmniSwapMock, USDT, USDC>(OmniSwapMock {}, usdt, usdc, 3, ctx);

        let btc = faucet::force_mint<BTC>(faucet, 3, ctx);
        let usdt = faucet::force_mint<USDT>(faucet, 100000, ctx);
        let btc_usdt_lp = create_pool<OmniSwapMock, BTC, USDT>(OmniSwapMock {}, btc, usdt, 3, ctx);

        let usdc = faucet::force_mint<USDC>(faucet, 100000, ctx);
        let btc = faucet::force_mint<BTC>(faucet, 3, ctx);
        let usdc_btc_lp = create_pool<OmniSwapMock, USDC, BTC>(OmniSwapMock {}, usdc, btc, 3, ctx);

        let deployer = tx_context::sender(ctx);
        transfer::public_transfer(usdc_usdt_lp, deployer);
        transfer::public_transfer(btc_usdt_lp, deployer);
        transfer::public_transfer(usdc_btc_lp, deployer);
    }
}
