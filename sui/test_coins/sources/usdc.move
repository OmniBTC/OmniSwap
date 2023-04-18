// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0
module test_coins::usdc {
    use std::option;

    use sui::coin;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    friend test_coins::faucet;

    ////////////////////////////////////
    struct USDC has drop {}

    ////////////////////////////////////

    fun init(usdc_witness: USDC, ctx: &mut TxContext) {
        let (cap, metadata) = coin::create_currency(
            usdc_witness,
            6,
            b"USDC",
            b"USD Coin",
            b"https://www.centre.io/",
            option::none(),
            ctx
        );
        transfer::public_share_object(metadata);
        transfer::public_transfer(cap, tx_context::sender(ctx));
    }
}