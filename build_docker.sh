#!/bin/bash

if [ "$1" == "-h" ]; then
  echo "Usage: $0 [version_number]"
  exit 0
else
  tag="comingweb3/omniswap-relayer:arm64_v$1"
  echo "Building docker image with tag: $tag"
  bash ./fix_brownie_path.sh
  python3 fix_server_config.py

  docker buildx build --platform linux/arm64 -t "$tag" . --push
fi

