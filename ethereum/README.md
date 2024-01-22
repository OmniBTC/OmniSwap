

# Overview

Here is OmniSwap's ethereum contract repository.

# Setup 

The deployment and testing of the project uses [Brownie](https://eth-brownie.readthedocs.io/en/stable/index.html).
Brownie is a Python-based development and testing framework for smart contracts targeting the Ethereum Virtual Machine.

## Install dependencies

~~~shell
pip install -r requirements.txt
~~~

## Format 
[Black](https://github.com/psf/black) is the uncompromising Python code formatter.

To get started right away with sensible defaults:
```shell
black {source_file_or_directory}
```

You can run Black as a package if running it as a script doesn't work:
```shell
python -m black {source_file_or_directory}
```

## Environment

You can add your environment variables to a `.env` file. You can use the [.env.exmple](./.env.example) as a template, just fill in the values and rename it to '.env'. 

Here is what your `.env` should look like:
```shell
export WEB3_INFURA_PROJECT_ID=<PROJECT_ID>
export PRIVATE_KEY=<PRIVATE_KEY>
```

# Deployment

## Deploy 

~~~shell
brownie run --network {network} scripts/deploy.py
~~~

After deployment, all deployed contract addresses can be found in `build/deployments/map.json`


## Initialize

~~~shell
brownie run --network {network} scripts/initialize.py
~~~

# Test

## Swap

Note that you need to Deploy and Initialize src-network and dst-network respectively before calling swap.py.

~~~shell
python -m scripts.swap
~~~

## Network

### Modify

~~~shell
brownie networks modify polygon-test host=https://matic-mumbai.chainstacklabs.com chainid=80001
~~~

### Add

~~~shell
brownie networks add Arbitrum arbitrum-test host=https://rinkeby.arbitrum.io/rpc name=Testnet chainid=421611

brownie networks add Polygon zkevm-main host="https://zkevm-rpc.com" name="zkevm-main" chainid=1101
~~~

