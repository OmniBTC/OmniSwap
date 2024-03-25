// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

contract ChainXBridge {
    address public cold;
    uint64 public chainId;
    uint64 public nonce;

    event SwapOut(
        bytes32 swapId,
        uint64 fromChainId,
        uint64 toChainId,
        address sender,
        string receiver,
        uint256 amount,
        uint256 estGas
    );

    // 2023.05.23
    // 最初版本是合约生成swapid,后来改为从链下传入,忘了删掉了
    // 为保持统一,这个就留下了
    modifier autoIncreaseNonce() {
        nonce = nonce + 1;
        _;
    }

    constructor(address _cold, uint64 _chainId) {
        require(_cold != address(0), "InvalidCold");
        require(_chainId != 0, "InvalidChainId");

        cold = _cold;
        chainId = _chainId;
        nonce = 0;
    }

    function swap_out(
        bytes32 swapID,
        uint64 toChainId,
        string calldata receiver,
        uint256 amount,
        uint256 estGas
    ) external payable autoIncreaseNonce {
        require((cold != address(0)), "InvalidCold");
        require(msg.value == amount, "ValueErr");

        uint256 old_balance = cold.balance;
        (bool sent, ) = payable(cold).call{value: amount}("");
        require(sent, "Failed to send Ether");
        uint256 new_balance = cold.balance;

        require(
            new_balance > old_balance && new_balance == old_balance + amount,
            "Unexpect"
        );

        emit SwapOut(
            swapID,
            chainId,
            toChainId,
            msg.sender,
            receiver,
            amount,
            estGas
        );
    }
}
