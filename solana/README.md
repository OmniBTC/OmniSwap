## build & test & deploy
```bash
anchor build

cargo test

anchor deploy
```

## generate python sdk
```bash
anchorpy client-gen target/idl/omniswap.json scripts/omniswap --program-id 9YYGvVLZJ9XmKM2A1RNv1Dx3oUnHWgtXWt8V3HU5MtXU
```