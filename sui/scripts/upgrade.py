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
        digest=[12, 75, 239, 122, 58, 3, 251, 36, 123, 230, 177, 235, 83, 173, 13, 89, 34, 239, 87, 99, 88, 36, 116,
                142, 63, 209, 37, 49, 21, 31, 113, 236],
        gas_budget=500000000,
    )
    print(f"New package id:{omniswap.package_id}")


if __name__ == "__main__":
    main()
