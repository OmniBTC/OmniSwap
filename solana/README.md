## build & test & deploy
```bash
anchor build

cargo test

anchor deploy

anchor deploy --program-name omniswap --provider.cluster $SOLANA_RPC_URL --program-keypair omniswap-keypair-4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY.json 

```

## generate python sdk
```bash
anchorpy client-gen target/idl/omniswap.json scripts/omniswap --program-id 4edLhT4MAausnqaxvB4ezcVG1adFnGw1QUMTvDMp4JVY
```

## compile get_whirlpool_quote_config.ts
```bash
tsc scripts/test_dex/get_whirlpool_quote_config.ts --esModuleInterop  --skipLibCheck
```

## compile postvaa.ts
```bash
tsc scripts/test_dex/postvaa.ts --esModuleInterop  --skipLibCheck
```

## extend address-lookup-table
(test_usdc_pool)
```bash
solana address-lookup-table extend  8K1NLm2WvUT9inQGsRjF3vrq5wUMtRbPRcWgNpUNNBFC \
    --addresses \
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",\
"worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth",\
"wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb",\
"5BHn4v7pxd44L7eBqJLw39ixLLxP8gs2ds3xXagKCj67",\
"3nJzsfLtAVUaXyMb2NNMw357pFYGpM54qewNE3DiNaX8",\
"A2UVxxSt3AEefNkXANUdrCenvSqeyV6QKzuyxuT2Ai2X",\
"CUCqvvz9TsoeBHwd9Lcv97fu3VM71vcSFTS3TKyuSA79",\
"HjZJTQPJGVQmbDuYwZgmaGeHhF1X9cAxzfmr5CKkqwpd",\
"2Huv2NXqzEpmyooRQp8XY3gPq6FwfYpey9ma8TAKSShU",\
"6WyPZoehvC4EUbwwJ4wfK7HkuD1gHDKDbvHW6LCJNy4q",\
"27uqhhEafgVV3jv2qPavr6uKu1mdbxxxvMXjhLfbBALq",\
"2fCfP7g2QoYu6jaLdaTrWAURUV679SjdTGVf14JXkqpu"
```
(omniswap config)

```bash
solana address-lookup-table extend  ESxWFjHVo2oes1eAQiwkAUHNTTUT9Xm5zsSrE7QStYX8 \
    --addresses \
    "GR7xDWrbWcEYsnz1e5WDfy3iXvPw5tmWjeV8MY1sVHCp",\
"EcZK7hAyxzjeCL1zM9FKWeWcdziF4pFHiUCJ5r2886TP",\
"EofptCXfgVxRk1vxBLNP1Zk6SSPBiPdkYWVPgTLzbzGR",\
"FV2SB6pUGWABHxmnoVUxxdTVctzY7puAQon38sJ8oNm"
```

## install ts-node ubuntu(arm64)
```bash
# Install node/npm
wget https://nodejs.org/dist/v18.16.0/node-v18.16.0-linux-arm64.tar.xz
tar -xvf node-v18.16.0-linux-arm64.tar.xz
mv node-v18.16.0-linux-arm64 /usr/local/
rm -rf /usr/bin/node
rm -rf /usr/bin/npm
ln -s /usr/local/node-v18.16.0-linux-arm64/bin/node /usr/bin/node
ln -s /usr/local/node-v18.16.0-linux-arm64/bin/npm /usr/bin/npm

# Install ts-node
npm install -g ts-node
ln -s /usr/local/node-v18.16.0-linux-arm64/bin/ts-node /usr/bin/ts-node
```

## startup relayer
```bash
nohup ts-node scripts/relayer/solana.ts ./.env ./solana.csv > relayer_solana.log 2>&1 &
```
