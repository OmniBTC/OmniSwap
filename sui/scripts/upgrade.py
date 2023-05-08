from sui_brownie import SuiPackage

from scripts import sui_project
from scripts.deploy import load_wormhole, load_token_bridge
from scripts.struct_sui import omniswap_sui_path


def main():
    if sui_project.network == "sui-testnet":
        package_id = "0xe51ed45293a147a795cc6e28e2c0ea2369402c74d17cb84cb8b27b1cd6f766d8"
        upgrade_capability = "0xc5ebb86c58b290b3d3ad50d6f10933bcd99b0396d550ccbb0647ea4dd92f1f33"
    else:
        package_id = "0xe51ed45293a147a795cc6e28e2c0ea2369402c74d17cb84cb8b27b1cd6f766d8"
        upgrade_capability = "0xc5ebb86c58b290b3d3ad50d6f10933bcd99b0396d550ccbb0647ea4dd92f1f33"

    omniswap = SuiPackage(
        package_id=package_id,
        package_path=omniswap_sui_path
    )
    upgrade_policy = 0
    wormhole = load_wormhole()
    token_bridge = load_token_bridge()

    omniswap.program_upgrade_package(
        upgrade_capability,
        upgrade_policy,
        replace_address=dict(
            wormhole=wormhole.package_id,
            token_bridge=token_bridge.package_id
        ),
        gas_budget=2000000000
    )


if __name__ == "__main__":
    main()
