#!/bin/bash

find ./ethereum/build -type f -name "*.json" -exec sed -i "s|$HOME|/root|g" {} +
