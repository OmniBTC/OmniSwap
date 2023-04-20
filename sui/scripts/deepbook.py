import time

from sui_brownie import sui_brownie, Argument, U16

from scripts import deploy, sui_project


def load_deep_book():
    return sui_brownie.SuiPackage(
        package_id="0xdee9",
        package_name="DeepBook"
    )


def load_sui():
    return sui_brownie.SuiPackage(
        package_id="0x2",
        package_name="Sui"
    )


def claim_faucet(coin_type):
    test_coins = deploy.load_test_coins(is_from_config=True)
    test_coins.faucet.claim(
        deploy.load_test_coin_faucet(is_from_config=True),
        type_arguments=[coin_type],
    )


def create_pool():
    # sui_project.pay_sui(amounts=[int(100 * 1e9)],
    #                     input_coins=["0x000a0a24118e717333b4942afe0ef24910c08a2eac205da9b3841621ce317c17"])
    deep_book_package = sui_brownie.SuiPackage(
        package_id="0xdee9",
        package_name="DeepBook"
    )
    tick_size = 100
    lot_size = 100
    coin = "0xcb3461b7836e63d30678e94013b384cdd90f44ff85c5bd32c9b5d4e58e80806e"
    deep_book_package.clob.create_pool(
        tick_size,
        lot_size,
        coin,
        type_arguments=["0x86f2cb15623a5f42ac119539cf898d7a6d96415233e63195b8e79f4f2b468c3b::btc::BTC",
                        "0x86f2cb15623a5f42ac119539cf898d7a6d96415233e63195b8e79f4f2b468c3b::usdc::USDC"
                        ]
    )


def create_fund_account():
    deep_book_package = load_deep_book()
    sui_package = load_sui()

    sui_project.batch_transaction(
        actual_params=[sui_project.account.account_address],
        transactions=[
            [
                deep_book_package.clob.create_account,
                [],
                []
            ],
            [
                sui_package.transfer.public_transfer,
                [Argument("Result", U16(0)), Argument("Input", U16(0))],
                ["0x000000000000000000000000000000000000000000000000000000000000dee9::custodian::AccountCap"]
            ]
        ]
    )


def deposit_fund():
    deep_book_package = load_deep_book()
    account_cap = deep_book_package.custodian.AccountCap[-1]
    pool_id = sui_project.network_config['pools']['BTC-USDC']['pool_id']
    btc = deploy.btc(is_from_config=True)
    usdc = deploy.usdc(is_from_config=True)
    ty_args = [btc, usdc]

    claim_faucet(deploy.usdc(is_from_config=True))

    claim_faucet(deploy.btc(is_from_config=True))

    result = sui_project.client.suix_getCoins(sui_project.account.account_address, usdc,
                                              None, None)
    coin_usdc = [c["coinObjectId"] for c in result["data"]][-1]
    result = sui_project.client.suix_getCoins(sui_project.account.account_address, btc,
                                              None, None)
    coin_btc = [c["coinObjectId"] for c in result["data"]][-1]
    deep_book_package.clob.deposit_base(
        pool_id,
        coin_btc,
        account_cap,
        type_arguments=ty_args
    )

    deep_book_package.clob.deposit_quote(
        pool_id,
        coin_usdc,
        account_cap,
        type_arguments=ty_args
    )


def create_limit_order():
    deep_book_package = load_deep_book()
    # create_fund_account()
    account_cap = deep_book_package.custodian.AccountCap[-1]
    deposit_fund()
    pool_id = sui_project.network_config['pools']['BTC-USDC']['pool_id']
    ty_args = [deploy.btc(is_from_config=True), deploy.usdc(is_from_config=True)]

    deep_book_package.clob.place_limit_order(
        pool_id,
        100,
        int(1e5),
        True,
        int((time.time() + 100000) * 1000),
        0,
        deploy.clock(),
        account_cap,
        type_arguments=ty_args
    )


if __name__ == "__main__":
    create_limit_order()
