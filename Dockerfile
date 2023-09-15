FROM comingweb3/coming-ubuntu:arm64

RUN apt update && apt install -y python3-pip libcurl4-openssl-dev libssl-dev git

# boost local build
ENV http_proxy "http://172.17.0.1:7890"
ENV https_proxy "http://172.17.0.1:7890"

COPY requirements.txt .
RUN pip install -r requirements.txt  \
    && brownie pm install OpenZeppelin/openzeppelin-contracts@4.6.0  \
    && brownie pm install Uniswap/v3-core@1.0.0

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