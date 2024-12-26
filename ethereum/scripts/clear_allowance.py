from brownie import (
    SoDiamond,
    Contract,
    AllowanceFacet,
)

from scripts.helpful_scripts import get_account, change_network


def clear_ethereum_allowance(proxy_diamond, account):
    change_network("ethereum-main")

    proxy_diamond.clearAllowance(
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # UniswapV2
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # UniswapV2
        ],
        {"from": account}
    )


def clear_bsc_allowance(proxy_diamond, account):
    change_network("bsc-main")

    proxy_diamond.clearAllowance(
        "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",  # WETH
        [
            "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwapV2
            "0x1b81D678ffb9C0263b24A97847620C99d213eB14",  # PancakeSwapV3
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",  # USDC
        [
            "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwapV2
            "0x1b81D678ffb9C0263b24A97847620C99d213eB14",  # PancakeSwapV3
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x55d398326f99059fF775485246999027B3197955",  # USDT
        [
            "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwapV2
            "0x1b81D678ffb9C0263b24A97847620C99d213eB14",  # PancakeSwapV3
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",  # BUSD
        [
            "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwapV2
            "0x1b81D678ffb9C0263b24A97847620C99d213eB14",  # PancakeSwapV3
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )


def clear_base_allowance(proxy_diamond, account):
    change_network("base-main")

    proxy_diamond.clearAllowance(
        "0x4200000000000000000000000000000000000006",  # WETH
        [
            "0xFB7eF66a7e61224DD6FcD0D7d9C3be5C8B049b9f",  # SushiswapV3
            "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",  # BaseswapV2
            "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",  # Aerodrome
            "0x2626664c2603336E57B271c5C0b26F421741e481",  # UniswapV3
            "0x8c1A3cF8f83074169FE5D7aD50B978e1cD6b37c7",  # AlienbaseV2
            "0xaaa3b1F1bd7BCc97fD1917c18ADE665C5D31F066",  # SwapBasedV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC
        [
            "0xFB7eF66a7e61224DD6FcD0D7d9C3be5C8B049b9f",  # SushiswapV3
            "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",  # BaseswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )



def clear_avalanche_allowance(proxy_diamond, account):
    change_network("avalanche-main")

    def clear_base_allowance(proxy_diamond, account):
        change_network("base-main")

    proxy_diamond.clearAllowance(
        "0x4200000000000000000000000000000000000006",  # WETH
        [
            "0xFB7eF66a7e61224DD6FcD0D7d9C3be5C8B049b9f",  # SushiswapV3
            "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",  # BaseswapV2
            "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",  # Aerodrome
            "0x2626664c2603336E57B271c5C0b26F421741e481",  # UniswapV3
            "0x8c1A3cF8f83074169FE5D7aD50B978e1cD6b37c7",  # AlienbaseV2
            "0xaaa3b1F1bd7BCc97fD1917c18ADE665C5D31F066",  # SwapBasedV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",  # WETH
        [
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",  # USDC
        [
            "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",  # PangolinV2
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",  # USDT
        [
            "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",  # PangolinV2
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",  # WETH.e
        [
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",  # USDC.e
        [
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xc7198437980c041c805A1EDcbA50c1Ce5db95118",  # USDT.e
        [
            "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoeV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )


def clear_polygon_allowance(proxy_diamond, account):
    change_network("polygon-main")

    proxy_diamond.clearAllowance(
        "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",  # WETH
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )


def clear_arbitrum_allowance(proxy_diamond, account):
    change_network("arbitrum-main")

    proxy_diamond.clearAllowance(
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",  # WBTC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",  # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH.e
        [
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # USDT
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",  # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC.e
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",  # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )


def clear_optimism_allowance(proxy_diamond, account):
    change_network("optimism-main")

    proxy_diamond.clearAllowance(
        "0x4200000000000000000000000000000000000006",  # WETH
        [
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",  # USDT
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0xE6Df0BB08e5A97b40B21950a0A51b94c4DbA0Ff6",  # ZipSwapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x7f5c764cbc14f9669b88837ca1490cca17c31607",  # USDC.e
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0xE6Df0BB08e5A97b40B21950a0A51b94c4DbA0Ff6",  # ZipSwapV2
            "0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858",  # Velodrome
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # USDC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # UniswapV3
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",  # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64",  # OpenOcean
        ],
        {"from": account}
    )


def clear_zksync_allowance(proxy_diamond, account):
    change_network("zksync-main")

    proxy_diamond.clearAllowance(
        "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",  # WETH
        [
            "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",  # SyncSwap
            "0x8B791913eB07C32779a16750e3868aA8495F5964",  # MuteIO
            "0x3F95eF3f2eAca871858dbE20A93c01daF6C2e923",  # KyberSwap
            "0x36A1aCbbCAfca2468b85011DDD16E7Cb4d673230",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x493257fd37edb34451f62edf8d2a0c418852ba4c",  # USDT
        [
            "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",  # SyncSwap
            "0x8B791913eB07C32779a16750e3868aA8495F5964",  # MuteIO
            "0x3F95eF3f2eAca871858dbE20A93c01daF6C2e923",  # KyberSwap
            "0x36A1aCbbCAfca2468b85011DDD16E7Cb4d673230",  # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",  # USDC
        [
            "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",  # SyncSwap
            "0x8B791913eB07C32779a16750e3868aA8495F5964",  # MuteIO
            "0x3F95eF3f2eAca871858dbE20A93c01daF6C2e923",  # KyberSwap
            "0x36A1aCbbCAfca2468b85011DDD16E7Cb4d673230",  # OpenOcean
        ],
        {"from": account}
    )


def clear_allowance():
    account = get_account()
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "AllowanceFacet", so_diamond.address, AllowanceFacet.abi
    )

    clear_ethereum_allowance(proxy_diamond, account)
    clear_bsc_allowance(proxy_diamond, account)
    clear_base_allowance(proxy_diamond, account)
    clear_avalanche_allowance(proxy_diamond, account)
    clear_polygon_allowance(proxy_diamond, account)
    # clear_arbitrum_allowance(proxy_diamond, account)
    clear_optimism_allowance(proxy_diamond, account)
    clear_zksync_allowance(proxy_diamond, account)
