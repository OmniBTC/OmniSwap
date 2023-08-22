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
        digest=[225, 169, 137, 76, 220, 104, 31, 61, 171, 199, 26, 252, 236, 239, 126, 224, 4, 110, 72, 148, 75, 157,
                238, 75, 122, 106, 236, 236, 224, 216, 84, 74],
        gas_budget=500000000,
    )
    print(f"New package id:{omniswap.package_id}")


if __name__ == "__main__":
    main()
