// SPDX-License-Identifier: BUSL-1.1

pragma solidity >=0.7.6;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

// this is a MOCK
contract MockToken is ERC20 {
    constructor(
        string memory name_,
        string memory symbol_
    ) ERC20(name_, symbol_) {
        _mint(msg.sender, 1000000000 * 10 ** 18);
    }

    function mint(address _to, uint256 _amount) public {
        _mint(_to, _amount);
    }
}
