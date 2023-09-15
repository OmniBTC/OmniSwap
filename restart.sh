#!/bin/bash

evm_log=$(pgrep -f relayer_evm.log)
aptos_log=$(pgrep -f relayer_aptos.log)
sui_log=$(pgrep -f relayer_sui.log)

evm=$(pgrep -f scripts/relayer/evm.py)
aptos=$(pgrep -f scripts/relayer/aptos.py)
sui=$(pgrep -f scripts/relayer/sui.py)


if [[ -n "$evm_log" ]];
then
    echo "Restart evm relayer..."
    kill "$evm"
    pkill python3
    cd /OmniSwap/ethereum || echo "Dir not exist"
    nohup /usr/local/bin/brownie run ./scripts/relayer/evm_cctp.py > ../cctp_relayer.log 2>&1 &
    nohup /usr/local/bin/brownie run ./scripts/relayer/evm.py >> ../relayer_evm.log 2>&1 &
    nohup /usr/local/bin/brownie run ./scripts/relayer/stargate_compensate.py > ../stargate_compensate.log 2>&1 &
fi


if [[ -n "$aptos_log" ]];
then
    echo "Restart aptos relayer..."
    kill "$aptos"
    cd /OmniSwap/aptos || echo "Dir not exist"
    nohup /usr/local/bin/brownie run ./scripts/relayer/aptos.py >> ../relayer_aptos.log 2>&1 &
fi

if [[ -n "$sui_log" ]];
then
    echo "Restart sui relayer..."
    kill "$sui"
    cd /OmniSwap/sui || echo "Dir not exist"
    nohup /usr/local/bin/brownie run ./scripts/relayer/sui.py >> ../relayer_sui.log 2>&1 &
fi

