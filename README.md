# SoOmnichain

The original intention of SoOmnichain is to achieve the purpose of full chain interoperability by aggregating the liquidity of various bridges. With the help of SoOmnichain:
1. Rapid circulation of user assets in different chains
2. Aggregate different bridges, such as stargate, cbridge, anyswap, etc. Users have the best cross-chain withdrawal, mainly including security, speed and handling fees
3. Aggregate the swap of different chains, users can swap different assets of the two chains with one click, such as eth of Ethereum and bnb of bsc

# Install

~~~shell
pip install -r requirements.txt
~~~

# Environment

You can add your environment variables to a `.env` file. You can use the [.env.exmple](./.env.example) as a template, just fill in the values and rename it to '.env'. 

Here is what your `.env` should look like:
```shell
export WEB3_INFURA_PROJECT_ID=<PROJECT_ID>
export PRIVATE_KEY=<PRIVATE_KEY>
```

# Deploy

~~~shell
brownie run --network {network} scripts/deploy.py
~~~

# Initialize

~~~shell
brownie run --network {network} scripts/initialize.py
~~~

# Swap

~~~shell
brownie run scripts/swap.py swap {src-network} {dst-network}
~~~



