// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0
module test_coins::coins {
    use std::type_name::{into_string, get};

    use sui::bag::{Self, Bag};
    use sui::balance;
    use sui::tx_context::TxContext;

    friend test_coins::faucet;

    ////////////////////////////////////
    struct USDT has drop {}

    struct XBTC has drop {}

    struct BTC has drop {}

    struct ETH has drop {}

    struct BNB has drop {}

    struct WBTC has drop {}

    struct USDC has drop {}

    struct DAI has drop {}

    struct MATIC has drop {}

    struct APT has drop {}

    ////////////////////////////////////

    public(friend) fun get_coins(ctx: &mut TxContext): Bag {
        let coins = bag::new(ctx);

        bag::add(&mut coins, into_string(get<XBTC>()), balance::create_supply(XBTC {}));
        bag::add(&mut coins, into_string(get<ETH>()), balance::create_supply(ETH {}));
        bag::add(&mut coins, into_string(get<BNB>()), balance::create_supply(BNB {}));
        bag::add(&mut coins, into_string(get<WBTC>()), balance::create_supply(WBTC {}));
        bag::add(&mut coins, into_string(get<DAI>()), balance::create_supply(DAI {}));
        bag::add(&mut coins, into_string(get<MATIC>()), balance::create_supply(MATIC {}));
        bag::add(&mut coins, into_string(get<APT>()), balance::create_supply(APT {}));

        coins
    }
}
