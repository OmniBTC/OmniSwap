## build & test & deploy
```bash
anchor build

cargo test

anchor deploy
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

## extand address-lookup-table
(test_usdc_pool)
```bash
solana address-lookup-table extend  ESxWFjHVo2oes1eAQiwkAUHNTTUT9Xm5zsSrE7QStYX8 \
    --addresses \
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",\
"b3D36rfrihrvLmwfvAzbnX9qF1aJ4hVguZFmjqsxVbV",\
"281LhxeKQ2jaFDx9HAHcdrU9CpedSH7hx5PuRrM7e1FS",\
"4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",\
"3dycP3pym3q6DgUpZRviaavaScwrrCuC6QyLhiLfSXge",\
"969UqMJSqvgxmNuAWZx91PAnLJU825qJRAAcEVQMWASg"
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
