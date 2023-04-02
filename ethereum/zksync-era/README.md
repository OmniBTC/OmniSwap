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
yarn hardhat deploy-zksync
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