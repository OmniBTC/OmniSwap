// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface IStargateReceiver {
    function sgReceive(
        uint16 _chainId,
        bytes memory _srcAddress,
        uint256 _nonce,
        address _token,
        uint256 _amount,
        bytes memory _payload
    ) external;
}
