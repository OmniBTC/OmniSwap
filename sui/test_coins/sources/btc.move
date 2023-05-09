// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0
module test_coins::btc {
    use std::option;

    use sui::coin;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    friend test_coins::faucet;

    ////////////////////////////////////

    /// Witness
    struct BTC has drop {}

    ////////////////////////////////////

    fun init(btc_witness: BTC, ctx: &mut TxContext) {
        let (cap, metadata) = coin::create_currency(
            btc_witness,
            8,
            b"BTC",
            b"Bitcoin",
            b"https://bitcoin.org/",
            option::none(),
            ctx
        );
        transfer::public_share_object(metadata);
        transfer::public_transfer(cap, tx_context::sender(ctx));
    }
}