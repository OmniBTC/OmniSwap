## build & test & deploy
```bash
anchor build

cargo test

anchor deploy
```

## generate python sdk
```bash
anchorpy client-gen target/idl/omniswap.json scripts/omniswap --program-id FpdkugsrDzCn57xeFPo6fwRmsnH7FUdJiDK717p3dico
```