import requests
from typing import Dict
from dataclasses import dataclass

@dataclass
class ChainConfig:
    chain_id: int
    rpc_url: str
    tokens: Dict[str, str]  # token_symbol -> address mapping
    so_diamond: str  # SoDiamond contract address
    swaps: Dict[str, str]  # swap_protocol_name -> address mapping


class SoDiamondAllowanceChecker:
    def __init__(self, config: ChainConfig):
        self.config = config
        self._decimals_cache = {}  # Cache for token decimals

    def _make_rpc_call(self, method_signature: str, to_address: str, params: list = None) -> str:
        """
        Make a generic RPC call to the blockchain

        Args:
            method_signature: The 4-byte signature of the method to call
            to_address: The contract address to call
            params: List of parameters to pass to the method

        Returns:
            The hex string result from the RPC call
        """
        if params is None:
            params = []

        data = method_signature + ''.join([p[2:].zfill(64) for p in params])

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": to_address,
                "data": data
            }, "latest"],
            "id": 1
        }

        response = requests.post(self.config.rpc_url, json=payload)
        return response.json().get("result")

    def _get_token_decimals(self, token_address: str) -> int:
        """
        Get token decimals with caching

        Args:
            token_address: The token contract address

        Returns:
            The number of decimals for the token

        Raises:
            ValueError: If unable to fetch decimals
        """
        if token_address not in self._decimals_cache:
            # Call decimals() method
            result = self._make_rpc_call("0x313ce567", token_address)
            if result:
                self._decimals_cache[token_address] = int(result, 16)
            else:
                raise ValueError(f"Failed to get decimals for token {token_address}")
        return self._decimals_cache[token_address]

    def check_allowance(self, token_address: str, spender: str) -> int:
        """
        Check single token allowance

        Args:
            token_address: The token contract address
            spender: The address to check allowance for

        Returns:
            The allowance amount as an integer
        """
        # Call allowance(address,address) method
        result = self._make_rpc_call(
            "0xdd62ed3e",
            token_address,
            [self.config.so_diamond, spender]
        )
        return int(result, 16) if result else 0

    def check_all_allowances(self, token_symbol: str) -> Dict[str, int]:
        """
        Check SoDiamond's allowances for a token against all swap protocols

        Args:
            token_symbol: The symbol of the token to check

        Returns:
            Dictionary mapping protocol names to allowance amounts

        Raises:
            ValueError: If token symbol is not found in config
        """
        token_address = self.config.tokens.get(token_symbol)
        if not token_address:
            raise ValueError(f"Unknown token symbol: {token_symbol}")

        results = {}
        for swap_name, swap_address in self.config.swaps.items():
            allowance = self.check_allowance(token_address, swap_address)
            results[swap_name] = allowance

        return results

    def format_amount(self, amount: int, token_symbol: str) -> str:
        """
        Format token amount with proper decimals

        Args:
            amount: The raw token amount
            token_symbol: The token symbol

        Returns:
            Formatted string with amount and symbol
        """
        token_address = self.config.tokens[token_symbol]
        decimals = self._get_token_decimals(token_address)
        return f"{amount / (10 ** decimals):.6f} {token_symbol}"

    def show_allowances(self):
        """
        Check and print allowances for all configured tokens
        """
        print("/" * 50)
        print(f"\nChain ID: {self.config.chain_id}")
        for token in self.config.tokens.keys():
            try:
                print(f"\n{token} Allowances for SoDiamond:")
                print("-" * 50)
                allowances = self.check_all_allowances(token)
                for protocol, amount in allowances.items():
                    formatted_amount = self.format_amount(amount, token)
                    print(f"{protocol:<15}: {formatted_amount}")

            except Exception as e:
                print(f"Error checking {token}: {e}")
        print("/" * 50)



ETH_CONFIG = ChainConfig(
    chain_id=1,
    rpc_url="https://ethereum.publicnode.com",
    tokens={
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDD": "0x0C10bF8FcB7Bf5412187A595ab97a3609160b5c6"
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "Curve": "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "UniswapV3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "UniswapV2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "BalancerV2": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "SushiSwapV2": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

BSC_CONFIG = ChainConfig(
    chain_id=56,
    rpc_url="https://bsc.publicnode.com",
    tokens={
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "WETH": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
        "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "WombatExchange": "0x19609B03C976CCA288fbDae5c21d4290e9a4aDD7",
        "BiSwap": "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
        "THENA": "0xd4ae6eCA985340Dd434D38F470aCCce4DC78D109",
        "PancakeSwapV2": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "PancakeSwapV3": "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

BASE_CONFIG = ChainConfig(
    chain_id=8453,
    rpc_url="https://base.meowrpc.com",
    tokens={
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    },
    so_diamond="0xfDa613cb7366b1812F2d33fC95D1d4DD3896aeb8",
    swaps={
        "SushiswapV3": "0xFB7eF66a7e61224DD6FcD0D7d9C3be5C8B049b9f",
        "BaseswapV2": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",
        "Aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
        "UniswapV3": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "AlienbaseV2": "0x8c1A3cF8f83074169FE5D7aD50B978e1cD6b37c7",
        "SwapBasedV3": "0xD58f563A7D6150a2575C74065CB18f53EC2e9D07",
        "SwapBasedV2": "0xaaa3b1F1bd7BCc97fD1917c18ADE665C5D31F066",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

AVAX_CONFIG = ChainConfig(
    chain_id=43114,
    rpc_url="https://avalanche.public-rpc.com",
    tokens={
        "WETH": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
        "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "USDT": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
        "WETH.e": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
        "USDC.e": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",
        "USDT.e": "0xc7198437980c041c805A1EDcbA50c1Ce5db95118",
        "WAVAX": "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7"
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "BalancerV2": "0xba12222222228d8ba445958a75a0704d566bf2c8",
        "Curve": "0x1da20Ac34187b2d9c74F729B85acB225D3341b25",
        "GMXV1": "0x5F719c2F1095F7B9fc68a68e35B51194f4b6abe8",
        "TraderJoe": "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30",
        "PangolinV2": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
        "TraderJoeV2": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

POL_CONFIG = ChainConfig(
    chain_id=137,
    rpc_url="https://polygon.meowrpc.com",
    tokens={
        "WPOL": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
        "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "Curve": "0x1d8b86e3D88cDb2d34688e87E72F388Cb541B7C8",
        "PearlFi": "0xcC25C0FD84737F44a7d38649b69491BBf0c7f083",
        "UniswapV3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "QuickswapV2": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

ARB_CONFIG = ChainConfig(
    chain_id=42161,
    rpc_url="https://arb1.arbitrum.io/rpc",
    tokens={
        "WBTC": "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",
        "WETH.e": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "USDC.e": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "BalancerV2": "0xba12222222228d8ba445958a75a0704d566bf2c8",
        "TraderJoe": "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30",
        "GMXV1": "0xaBBc5F99639c9B6bCb58544ddf04EFA6802F4064",
        "UniswapV3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "SushiswapV2": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "CamelotV2": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

OP_CONFIG = ChainConfig(
    chain_id=10,
    rpc_url="https://optimism.publicnode.com",
    tokens={
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDT": "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58",
        "USDC.e": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
        "USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
    },
    so_diamond="0x2967e7bb9daa5711ac332caf874bd47ef99b3820",
    swaps={
        "Curve": "0x1337bedc9d22ecbe766df105c9623922a27963ec",
        "UniswapV3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "ZipSwapV2": "0xE6Df0BB08e5A97b40B21950a0A51b94c4DbA0Ff6",
        "Velodrome": "0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OneInch": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

ZKSYNC_CONFIG = ChainConfig(
    chain_id=324,
    rpc_url="https://1rpc.io/zksync2-era",
    tokens={
        "WETH": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
        "USDT": "0x493257fd37edb34451f62edf8d2a0c418852ba4c",
        "USDC": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
    },
    so_diamond="0x2350D92F6Bf51C202395B10D6b8a6ae0B37bB577",
    swaps={
        "SyncSwap": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
        "MuteIO": "0x8B791913eB07C32779a16750e3868aA8495F5964",
        "MaverickProtocol": "0x39E098A153Ad69834a9Dac32f0FCa92066aD03f4",
        "iZiSwap": "0x943ac2310D9BC703d6AB5e5e76876e212100f894",
        "KyberSwap": "0x3F95eF3f2eAca871858dbE20A93c01daF6C2e923",
        "OneInch": "0x6e2B76966cbD9cF4cC2Fa0D76d24d5241E0ABC2F",
        "OpenOcean": "0x36A1aCbbCAfca2468b85011DDD16E7Cb4d673230"
    }
)

ZKEVM_CONFIG = ChainConfig(
    chain_id=1101,
    rpc_url="https://zkevm-rpc.com",
    tokens={
        "WETH": "0x4F9A0e7FD2Bf6067db6994CF12E4495Df938E6e9",
    },
    so_diamond="0x4AF9bE5A3464aFDEFc80700b41fcC4d9713E7449",
    swaps={
        "QuickSwapV3": "0xF6Ad3CcF71Abb3E12beCf6b3D2a74C963859ADCd",
        "PancakeSwapV3": "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        "BalancerV2": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OpenOcean": "0x6dd434082EAB5Cd134B33719ec1FF05fE985B97b"
    }
)

LINEA_CONFIG = ChainConfig(
    chain_id=59144,
    rpc_url="https://linea-rpc.publicnode.com",
    tokens={
        "SGETH": "0x224D8Fd7aB6AD4c6eb4611Ce56EF35Dec2277F03",
    },
    so_diamond="0x6e166933CACB57b40f5C5D1a2D275aD997A7D318",
    swaps={
        "Lynex": "0x610D2f07b7EdC67565160F587F37636194C34E74",
        "KyberSwap": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "OpenOcean": "0x6352a56caadC4F1E25CD6c75970Fa768A3304e64"
    }
)

# bevm-canary, scroll, opbnb

METIS_CONFIG = ChainConfig(
    chain_id=1088,
    rpc_url="https://metis-pokt.nodies.app",
    tokens={
        "METIS": "0xDeadDeAddeAddEAddeadDEaDDEAdDeaDDeAD0000",
        "m.USDT": "0xbB06DCA3AE6887fAbF931640f67cab3e3a16F4dC"
    },
    so_diamond="0x0B77E63db1cd9F4f7cdAfb4a1C39f6ABEB764B66",
    swaps={
        "Netswap": "0x1E876cCe41B7b844FDe09E38Fa1cf00f213bFf56",
        "Wagmi": "0x8Fb7a8cb6c4DCf820762397aDF80A27a777cFedC"
    }
)


MANTLE_CONFIG = ChainConfig(
    chain_id=5000,
    rpc_url="https://mantle-rpc.publicnode.com",
    tokens={
        "WMNT": "0x78c1b0C915c4FAA5FffA6CAbf0219DA63d7f4cb8",
        "WETH": "0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111",
        "METH": "0xcDA86A272531e8640cD7F1a92c01839911B90bb0",
        "USDT": "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
        "USDC": "0x201EBa5CC46D216Ce6DC03F6a759e8E766e956aE"
    },
    so_diamond="0x0B77E63db1cd9F4f7cdAfb4a1C39f6ABEB764B66",
    swaps={
        "MerchantMoe": "0xeaEE7EE68874218c3558b40063c42B82D3E7232a",
        "Agni": "0x319B69888b0d11cEC22caA5034e25FfFBDc88421"
    }
)

CORE_CONFIG = ChainConfig(
    chain_id=1116,
    rpc_url="https://rpc.coredao.org",
    tokens={
        "WBTC": "0x5832f53d147b3d6Cd4578B9CBD62425C7ea9d0Bd",
        "WETH": "0xeAB3aC417c4d6dF6b143346a46fEe1B847B50296",
        "USDT": "0x900101d06A7426441Ae63e9AB3B9b0F63Be145F1",
        "USDC": "0xa4151B2B3e269645181dCcF2D426cE75fcbDeca9",
        "BTC.b": "0x2297aEbD383787A160DD0d9F71508148769342E3",
    },
    so_diamond="0x0B77E63db1cd9F4f7cdAfb4a1C39f6ABEB764B66",
    swaps={
        "GlyphExchange": "0x4ddDD324F205e5989bAF8aD0FFCa41f4E5d9841D",
    }
)

if __name__ == "__main__":
    # SoDiamondAllowanceChecker(ETH_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(BSC_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(BASE_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(AVAX_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(POL_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(ARB_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(OP_CONFIG).show_allowances()
    SoDiamondAllowanceChecker(ZKSYNC_CONFIG).show_allowances()

    # SoDiamondAllowanceChecker(ZKEVM_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(LINEA_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(METIS_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(MANTLE_CONFIG).show_allowances()
    # SoDiamondAllowanceChecker(CORE_CONFIG).show_allowances()

    # Ignore bevm-canary, scroll, opbnb
