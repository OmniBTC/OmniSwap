pragma solidity 0.8.13;

contract ContractDeployerFactory {
    event ContractDeployed(bytes32 salt, address addr);

    function deployContract(
        bytes32 salt,
        bytes memory contractBytecode
    ) public {
        address addr;
        assembly {
            addr := create2(
                0,
                add(contractBytecode, 0x20),
                mload(contractBytecode),
                salt
            )
            if iszero(extcodesize(addr)) {
                revert(0, 0)
            }
        }
        emit ContractDeployed(salt, addr);
    }
}
