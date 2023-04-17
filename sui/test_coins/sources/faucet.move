// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0
module test_coins::faucet {
    use std::ascii::String;
    use std::type_name;

    use sui::bag::{Self, Bag};
    use sui::balance::{Self, Supply};
    use sui::coin::{Self, TreasuryCap, Coin};
    use sui::object::{Self, UID};
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};
    use sui::vec_set::{Self, VecSet};
    use test_coins::coins::get_coins;

    const ONE_COIN: u64 = 100000000;

    const ERR_NO_PERMISSIONS: u64 = 1;
    const ERR_NOT_ENOUGH_COINS: u64 = 2;

    struct Faucet has key {
        id: UID,
        coins: Bag,
        creator: address,
        admins: VecSet<address>
    }

    fun init(
        ctx: &mut TxContext
    ) {
        let admins = vec_set::empty<address>();
        transfer::share_object(
            Faucet {
                id: object::new(ctx),
                coins: get_coins(ctx),
                creator: tx_context::sender(ctx),
                admins
            }
        )
    }

    public entry fun add_admin(
        faucet: &mut Faucet,
        new_admin: address,
        ctx: &mut TxContext
    ) {
        assert!(faucet.creator == tx_context::sender(ctx), ERR_NO_PERMISSIONS);
        vec_set::insert(&mut faucet.admins, new_admin)
    }

    public entry fun remove_admin(
        faucet: &mut Faucet,
        old_admin: address,
        ctx: &mut TxContext
    ) {
        assert!(faucet.creator == tx_context::sender(ctx), ERR_NO_PERMISSIONS);
        vec_set::remove(&mut faucet.admins, &old_admin)
    }

    public entry fun add_supply<T>(
        faucet: &mut Faucet,
        treasury_cap: TreasuryCap<T>,
    ) {
        let supply = coin::treasury_into_supply(treasury_cap);

        bag::add(
            &mut faucet.coins,
            type_name::into_string(type_name::get<T>()),
            supply
        )
    }

    public entry fun claim<T>(
        faucet: &mut Faucet,
        ctx: &mut TxContext,
    ) {
        let coin_name = type_name::into_string(type_name::get<T>());
        assert!(
            bag::contains_with_type<String, Supply<T>>(&faucet.coins, coin_name),
            ERR_NOT_ENOUGH_COINS
        );

        let mut_supply = bag::borrow_mut<String, Supply<T>>(
            &mut faucet.coins,
            coin_name
        );

        let minted_balance = balance::increase_supply(
            mut_supply,
            ONE_COIN
        );

        transfer::public_transfer(
            coin::from_balance(minted_balance, ctx),
            tx_context::sender(ctx)
        )
    }

    public entry fun force_claim<T>(
        faucet: &mut Faucet,
        amount: u64,
        ctx: &mut TxContext,
    ) {
        let operator = tx_context::sender(ctx);
        assert!(
            faucet.creator == operator
                || vec_set::contains(&faucet.admins, &operator),
            ERR_NO_PERMISSIONS
        );

        let coin_name = type_name::into_string(type_name::get<T>());
        assert!(
            bag::contains_with_type<String, Supply<T>>(&faucet.coins, coin_name),
            ERR_NOT_ENOUGH_COINS
        );

        let mut_supply = bag::borrow_mut<String, Supply<T>>(
            &mut faucet.coins,
            coin_name
        );

        let minted_balance = balance::increase_supply(
            mut_supply,
            amount * ONE_COIN
        );

        transfer::public_transfer(
            coin::from_balance(minted_balance, ctx),
            operator
        )
    }

    public fun force_mint<T>(
        faucet: &mut Faucet,
        amount: u64,
        ctx: &mut TxContext,
    ): Coin<T> {
        let operator = tx_context::sender(ctx);
        assert!(
            faucet.creator == operator
                || vec_set::contains(&faucet.admins, &operator),
            ERR_NO_PERMISSIONS
        );

        let coin_name = type_name::into_string(type_name::get<T>());
        assert!(
            bag::contains_with_type<String, Supply<T>>(&faucet.coins, coin_name),
            ERR_NOT_ENOUGH_COINS
        );

        let mut_supply = bag::borrow_mut<String, Supply<T>>(
            &mut faucet.coins,
            coin_name
        );

        let minted_balance = balance::increase_supply(
            mut_supply,
            amount * ONE_COIN
        );

        coin::from_balance(minted_balance, ctx)
    }
}
