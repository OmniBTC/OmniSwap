// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0
module test_coins::usdt {
    use std::option;

    use sui::coin;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    friend test_coins::faucet;

    ////////////////////////////////////
    struct USDT has drop {}

    ////////////////////////////////////

    fun init(usdt_witness: USDT, ctx: &mut TxContext) {
        let (cap, metadata) = coin::create_currency(
            usdt_witness,
            6,
            b"USDT",
            b"Tether USD stablecoin",
            b"https://tether.to/",
            option::none(),
            ctx
        );
        transfer::public_share_object(metadata);
        transfer::public_transfer(cap, tx_context::sender(ctx));
    }
}
