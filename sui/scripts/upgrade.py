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
            cetus_clmm=sui_project.network_config['packages']['CetusClmm']['origin'],
            move_stl=sui_project.network_config['packages']['MoveSTL']['origin'],
            integer_mate=sui_project.network_config['packages']['IntegerMate']['origin'],
        ),
        replace_publish_at=dict(
            wormhole=wormhole.package_id,
            token_bridge=token_bridge.package_id,
            cetus_clmm=cetus_clmm.package_id,
            move_stl=move_stl.package_id,
            integer_mate=integer_mate.package_id,
        ),
        digest=[111, 207, 180, 196, 113, 107, 102, 58, 41, 125, 126, 26, 26, 146, 110, 179, 196, 59, 44, 172, 108, 208,
                234, 76, 129, 251, 253, 8, 181, 3, 7, 159],
        gas_budget=500000000,
    )
    print(f"New package id:{omniswap.package_id}")


if __name__ == "__main__":
    main()
