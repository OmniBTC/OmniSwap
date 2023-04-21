from scripts.serde_struct import omniswap_aptos_path
import aptos_brownie


def main(net="aptos-testnet"):
    aptos_brownie.AptosPackage(
        project_path=omniswap_aptos_path,
        network=net
    )


if __name__ == '__main__':
    main()
