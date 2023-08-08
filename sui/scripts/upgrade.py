from sui_brownie import SuiPackage

from scripts import sui_project
from scripts.deploy import load_wormhole, load_token_bridge, load_cetus_clmm, load_move_stl, load_integer_mate
from scripts.struct_sui import omniswap_sui_path


def main():
    package_id = sui_project.network_config["packages"]["OmniSwap"]
    upgrade_capability = sui_project.network_config["objects"]["OmniSwapUpgradeCap"]

    omniswap = SuiPackage(
        package_id=package_id,
        package_path=omniswap_sui_path
    )
    upgrade_policy = 0
    wormhole = load_wormhole()
    token_bridge = load_token_bridge()
    cetus_clmm = load_cetus_clmm()
    move_stl = load_move_stl()
    integer_mate = load_integer_mate()

    omniswap.program_upgrade_package(
        upgrade_capability,
        upgrade_policy,
        replace_address=dict(
            wormhole=sui_project.network_config['packages']['Wormhole']['origin'],
            token_bridge=sui_project.network_config['packages']['TokenBridge']['origin'],
            cetus_clmm=cetus_clmm.package_id,
            move_stl=move_stl.package_id,
            integer_mate=integer_mate.package_id,
        ),
        replace_publish_at=dict(
            wormhole=wormhole.package_id,
            token_bridge=token_bridge.package_id,
        ),
        digest=[80, 186, 56, 220, 2, 16, 189, 62, 205, 202, 225, 130, 183, 158, 250, 80, 224, 66, 11, 88, 166, 51, 157,
                237, 249, 233, 165, 80, 131, 102, 73, 211],
        gas_budget=500000000,
    )
    print(f"New package id:{omniswap.package_id}")


if __name__ == "__main__":
    main()
