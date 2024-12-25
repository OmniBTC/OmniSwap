
from brownie import (
    SoDiamond,
    Contract,
    AllowanceFacet,
)

from scripts.helpful_scripts import get_account, change_network


def clear_allowance():
    change_network("arbitrum-main")

    account = get_account()
    so_diamond = SoDiamond[-1]
    proxy_diamond = Contract.from_abi(
        "AllowanceFacet", so_diamond.address, AllowanceFacet.abi
    )

    # arbitrum

    proxy_diamond.clearAllowance(
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f", # WBTC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564", # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d", # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64", # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", # WETH.e
        [
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64", # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", # USDT
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564", # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d", # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64", # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", # USDC.e
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564", # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", # SushiswapV2
            "0xc873fEcbd354f5A56E00E710B90EF4201db2448d", # CamelotV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64", # OpenOcean
        ],
        {"from": account}
    )

    proxy_diamond.clearAllowance(
        "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", # USDC
        [
            "0xE592427A0AEce92De3Edee1F18E0157C05861564", # UniswapV3
            "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", # SushiswapV2
            "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5", # KyberSwap
            "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64", # OpenOcean
        ],
        {"from": account}
    )