# Overview

This is an aptos python tool to quickly implement aptos calls.



# Setup

~~~shell
pip install aptos_brownie
~~~



# Use

~~~python
import aptos_brownie

package = aptos_brownie.AptosPackage(
  project_path=omniswap_aptos_path,
  network=net
)

package["so_fee_wormhole::initialize"](2)
~~~

