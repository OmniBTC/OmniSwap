from pathlib import Path

from brownie import (
    BulkTransfer,
    MockToken,
    Contract
)

from scripts.helpful_scripts import get_account, read_json, change_network


def bulk_test():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    test_data = [
        [acc.address, acc.address],
        [int(1 * 1e18), int(0.5 * 1e18)]
    ]

    # op
    token_addr = "0x4200000000000000000000000000000000000042"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    print(int(sum(test_data[1]) + 1))
    token.approve(BulkTransfer[-1].address, int(sum(test_data[1]) + 1), {"from": acc})

    BulkTransfer[-1].batchTransferToken(token.address, test_data[0], test_data[1], {"from": acc})


def bulk():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/op_account_20231228.json"))
    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")
    # op
    token_addr = "0x4200000000000000000000000000000000000042"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    token.approve(BulkTransfer[-1].address, sum_balance, {"from": acc})

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        print(f"Bulk op:{round(sum(d1) / 1e18, 2)}")
        BulkTransfer[-1].batchTransferToken(token.address, d0, d1, {"from": acc})
        has_send.extend(d0)


def bulk_pcx():
    '''
    Running 'scripts/bulk.py::bulk_pcx'...
    Acc:0xB45cf380FF9A33c2bf7c41043530dc8Bb2e5295B
    Sum balance:8694533660001, len:3700
    Transaction sent: 0x82eb681ef1e02f5b4e602e7ccfe31cb7e4fa7e4afac8cbb0294526778093065b
      Gas price: 0.05 gwei   Gas limit: 30317   Nonce: 49
      Token.approve confirmed   Block: 12480052   Gas used: 26998 (89.05%)

    Bulk pcx:54935.34
    Transaction sent: 0xa3b3541a2c1f83e80445ff261fcf1e8d1af234bf7ca4c428f88f1e31f2c222fe
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 50
      BulkTransfer.batchTransferToken confirmed   Block: 12480053   Gas used: 13757795 (86.97%)

    Bulk pcx:5000.0
    Transaction sent: 0xebd195161aaf30603f68ea8770e8c20509cdf5fa2ab3c01414ad087decd446fe
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 51
      BulkTransfer.batchTransferToken confirmed   Block: 12480054   Gas used: 13893807 (87.83%)

    Bulk pcx:5000.0
    Transaction sent: 0x82d42d3fc98c23203e5bba18485b944f090abb6f3d3d99ac95e5872dd4e0d87b
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 52
      BulkTransfer.batchTransferToken confirmed   Block: 12480055   Gas used: 13893915 (87.83%)

    Bulk pcx:5000.0
    Transaction sent: 0xf10202607e76b127e4d664475a6f413c2c68b2c06af1f573360f3a7f893b8321
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 53
      BulkTransfer.batchTransferToken confirmed   Block: 12480056   Gas used: 13894083 (87.83%)

    Bulk pcx:5010.0
    Transaction sent: 0x549f7db8e1628e630dc0345b4b8175e501857fa6c47cc76363d3a35e837733fd
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 54
      BulkTransfer.batchTransferToken confirmed   Block: 12480057   Gas used: 13913851 (87.96%)

    Bulk pcx:5000.0
    Transaction sent: 0x78aa19bc0701877b1a488f02c9bb0b7e15a2f8d01821ead40314432ee934c24d
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 55
      BulkTransfer.batchTransferToken confirmed   Block: 12480058   Gas used: 13874111 (87.71%)

    Bulk pcx:5000.0
    Transaction sent: 0x396616b6ea21115c171a2241d2e5989fb6eeb507bea27bb6cf6134ca6ee9564d
      Gas price: 0.05 gwei   Gas limit: 15818996   Nonce: 56
      BulkTransfer.batchTransferToken confirmed   Block: 12480060   Gas used: 13874051 (87.71%)

    Bulk pcx:2000.0
    Transaction sent: 0xd6834e37813507adbf6bdcef551f150e95e85ec740b90726a3ac0d6c0bfecf30
      Gas price: 0.05 gwei   Gas limit: 6204102   Nonce: 57
      BulkTransfer.batchTransferToken confirmed   Block: 12480061   Gas used: 5589244 (90.09%)

    :return:
    '''

    change_network("bevm-main")

    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/20240102-pcx-airdrop-deduplicate-8694533660000.json"))
    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")

    # Bulk
    bulk_addr = '0xaa09eF5707307C112f2A517c95B5E6475c41d1e7'
    bulk_trasfer = Contract.from_abi("BulkTransfer", bulk_addr, BulkTransfer.abi)

    # PCX
    token_addr = "0xf3607524cAB05762cB5F0cAb17e4cA3A0F0b4E87"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    token.approve(bulk_addr, sum_balance, {"from": acc})

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        print(f"Bulk pcx:{round(sum(d1) / 1e8, 2)}")
        bulk_trasfer.batchTransferToken(token.address, d0, d1, {"from": acc})
        has_send.extend(d0)


def bulk_pcx_test():
    change_network("bevm-test")

    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/20240102-pcx-airdrop-deduplicate-8694533660000.json"))
    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")

    # Bulk
    bulk_addr = '0x34F5fA5da2779A88C253c19761446C46153Be5Ed'
    bulk_trasfer = Contract.from_abi("BulkTransfer", bulk_addr, BulkTransfer.abi)

    # Test
    token_addr = "0xC8720E21B9410c142e6D06aA0445B9dCD1C120F9"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    token.approve(bulk_addr, sum_balance, {"from": acc})

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        print(f"Bulk pcx:{round(sum(d1) / 1e8, 2)}")
        bulk_trasfer.batchTransferToken(token.address, d0, d1, {"from": acc})
        has_send.extend(d0)


def bulk_eth():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/op_account_20240528.json"))

    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        BulkTransfer[-1].batchTransferETH(d0, d1,
                                          {"from": acc,
                                           "value": sum(d1)})
        print(f"Send value:{sum(d1)}")
        has_send.extend(d0)


def bulk_bevm():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/bevm_account_20240528.json"))

    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        BulkTransfer[-1].batchTransferETH(d0, d1,
                                          {"from": acc,
                                           "value": sum(d1),
                                           "gas_price": "0.053 gwei"
                                           })
        print(f"Send value:{sum(d1)}")
        has_send.extend(d0)


def bulk_bsc_usdt():
    acc = get_account("bulk_key")
    print(f"Acc:{acc.address}")

    data = read_json(Path(__file__).parent.joinpath("data/bsc_account_20240221.json"))
    data = list(zip(*data))

    sum_balance = int(sum(data[1]) + 1)
    print(f"Sum balance:{sum_balance}, len:{len(data[0])}")
    # op
    token_addr = "0x55d398326f99059fF775485246999027B3197955"
    token = Contract.from_abi("Token", token_addr, MockToken.abi)
    # token.approve(BulkTransfer[-1].address, sum_balance, {"from": acc})

    interval = 500
    has_send = []
    for i in range(0, len(data[0]), interval):
        d0 = list(data[0][i:i + interval])
        d1 = list(data[1][i:i + interval])
        assert len(set(has_send) & set(d0)) == 0
        print(f"Bulk op:{round(sum(d1) / 1e18, 2)}")
        # bulk addr: 0xeD4BE9CF9D19056BeA62cac3CdbAA413B7625561
        BulkTransfer[-1].batchTransferToken(token.address, d0, d1, {"from": acc})
        has_send.extend(d0)
