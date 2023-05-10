# @Time    : 2023/3/7 13:25
# @Author  : WeiDai
# @FileName: __init__.py
from pathlib import Path

import sui_brownie

sui_project = sui_brownie.SuiProject(project_path=Path(__file__).parent.parent, network="sui-mainnet")
sui_project.active_account("Fee")
