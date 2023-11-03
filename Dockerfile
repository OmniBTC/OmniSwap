FROM comingweb3/coming-ubuntu:arm64

RUN apt update && apt install -y python3-pip libcurl4-openssl-dev libssl-dev git

# boost local build
ENV http_proxy "http://172.17.0.1:7890"
ENV https_proxy "http://172.17.0.1:7890"

COPY requirements.txt .
RUN pip install -r requirements.txt  \
    && brownie pm install OpenZeppelin/openzeppelin-contracts@4.6.0  \
    && brownie pm install Uniswap/v3-core@1.0.0 \
    && wget https://nodejs.org/dist/v18.16.0/node-v18.16.0-linux-arm64.tar.xz \
    && tar -xvf node-v18.16.0-linux-arm64.tar.xz \
    && mv node-v18.16.0-linux-arm64 /usr/local/node \
    && rm node-v18.16.0-linux-arm64.tar.xz \
    && rm -rf /usr/bin/node \
    && rm -rf /usr/bin/npm \
    && ln -s /usr/local/node-v18.16.0-linux-arm64/bin/node /usr/bin/node \
    && ln -s /usr/local/node-v18.16.0-linux-arm64/bin/npm /usr/bin/npm \
    && npm install -g ts-node \
    && ln -s /usr/local/node-v18.16.0-linux-arm64/bin/ts-node /usr/bin/ts-node

ENV http_proxy ""
ENV https_proxy ""

WORKDIR /OmniSwap

COPY ./ /OmniSwap/

# init relayer run env
RUN mv ./arm64/aptos /usr/bin/aptos  \
    && mv ./arm64/sui /usr/bin/sui  \
    && cd ethereum  \
    && brownie compile  \
    && cd ..