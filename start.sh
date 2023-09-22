#!/bin/bash

# start ethereum relayer
cd /OmniSwap/ethereum

# install solidity compiler and compile
brownie networks add Base base-main host=https://rpc.ankr.com/base name=Mainnet chainid=8453

brownie networks modify polygon-main host=https://rpc.ankr.com/polygon

nohup brownie run ./scripts/relayer/evm_cctp.py > ../cctp_relayer.log 2>&1 &

nohup brownie run ./scripts/relayer/evm.py > ../relayer_evm.log 2>&1 &

nohup brownie run ./scripts/relayer/stargate_compensate.py > ../stargate_compensate.log 2>&1 &

cd /OmniSwap


# start aptos relayer
cd /OmniSwap/aptos

nohup brownie run ./scripts/relayer/aptos.py > ../relayer_aptos.log 2>&1 &

cd /OmniSwap

# start sui relayer
cd /OmniSwap/sui

nohup brownie run ./scripts/relayer/sui.py > ../relayer_sui.log 2>&1 &

cd /OmniSwap

touch relayer_evm.log relayer_aptos.log relayer_sui.log cctp_relayer.log stargate_compensate.log

# print relayer logs
tail -f relayer_evm.log -f relayer_aptos.log -f relayer_sui.log -f cctp_relayer.log -f stargate_compensate.log