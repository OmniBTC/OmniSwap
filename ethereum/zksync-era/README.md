# zksync-era

## install
```bash
yarn install
```

## compile
```bash
yarn hardhat compile
```

## deploy
```bash
# testnet
yarn hardhat deploy-zksync

# mainnet
yarn hardhat deploy-zksync --network zkMainnet
```

## verify source codes
```bash
# testnet
python3 scripts/verify.py --deployer 0xcAF084133CBdBE27490d3afB0Da220a40C32E307

# mainnet
python3 scripts/verify.py --deployer 0xcAF084133CBdBE27490d3afB0Da220a40C32E307 --main
```

## initialize

```bash
brownie run scripts/initialize.py
```

## Add network
```bash
brownie networks add ZkSyncEra zksync2-test host="https://testnet.era.zksync.dev" name=zksync2-test chainid=280

brownie networks add ZkSyncEra zksync2-main host="https://mainnet.era.zksync.io" name=zksync2-main chainid=324
```

## Ignore Compile Warnings

- [x] `extcodesize`
    ```txt
    ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Warning: It looks like your code or one of its dependencies uses the 'extcodesize' instruction,  │
    │ which is usually needed in the following cases:                                                  │
    │   1. To detect whether an address belongs to a smart contract.                                   │
    │   2. To detect whether the deploy code execution has finished.                                   │
    │ zkSync era comes with native account abstraction support (so accounts are smart contracts,       │
    │ including private-key controlled EOAs), and you should avoid differentiating between contracts   │
    │ and non-contract addresses.
    └──────────────────────────────────────────────────────────────────────────────────────────────────┘
    ```

    refer to `https://era.zksync.io/docs/dev/building-on-zksync/contracts/differences-with-ethereum.html#selfdestruct`

    Contract bytecode cannot be accessed in our architecture.
    Only its size is accessible with both CODESIZE and EXTCODESIZE.
- [x] `<address payable>.send/transfer(<X>)`

    ```txt
    ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Warning: It looks like you are using '<address payable>.send/transfer(<X>)' without providing    │
    │ the gas amount. Such calls will fail depending on the pubdata costs.                             │
    │ This might be a false positive if you are using some interface (like IERC20) instead of the      │
    │ native Solidity send/transfer                                                                    │
    │ Please use 'payable(<address>).call{value: <X>}("")' instead.                                    │
    └──────────────────────────────────────────────────────────────────────────────────────────────────┘
    ```
    In ICelerBridge,

    function send(address _receiver,address _token,uint256 _amount,uint64 _dstChainId,uint64 _nonce,uint32 _maxSlippage) external;
    
- [x] `block.timestamp`

    ```txt
    ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Warning: It looks like you are checking for 'block.timestamp' in your code, which might lead to  │
    │ unexpected behavior. Due to the nature of the zkEVM, the timestamp of a block actually refers to │
    │ the timestamp of the whole batch that will be sent to L1 (meaning, the timestamp of this batch   │
    │ started being processed).                                                                        │
    │ We will provide a custom method to access the L2 block timestamp from the smart contract code in │
    │ the future.                                                                                      │
    └──────────────────────────────────────────────────────────────────────────────────────────────────┘
    ```
    the timestamp of the whole batch that will be sent to L1 (meaning, the timestamp of this batch started being processed)