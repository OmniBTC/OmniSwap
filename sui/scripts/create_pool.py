from pathlib import Path

from sui_brownie import sui_brownie
from scripts import sui_project


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


if __name__ == "__main__":
    create_pool()
