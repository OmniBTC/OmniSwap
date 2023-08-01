// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract Claim is ReentrancyGuard, Pausable, Ownable {
    // Start time
    uint256 private start;
    // Claimed token
    IERC20 public token;
    // Claimed amount
    mapping(address => uint256) public claimed;
    // Whether claimed
    mapping(address => bool) public isClaimed;

    constructor(uint256 _start, IERC20 _token) {
        require(_start > block.timestamp, "StartErr");

        start = _start;
        token = _token;
    }

    //Functions

    function claim() public whenNotPaused nonReentrant {
        require(block.timestamp >= start, "NotStart");

        uint256 amount = claimed[_msgSender()];
        require(amount > 0, "AmountZero");
        require(isClaimed[_msgSender()], "HasClaimed");

        SafeERC20.safeTransfer(token, _msgSender(), amount);
        isClaimed[_msgSender()] = true;
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function reFund(IERC20 _token, uint256 _amount) public onlyOwner {
        SafeERC20.safeTransfer(_token, _msgSender(), _amount);
    }

    function batchSetClaim(
        address[] calldata _users,
        uint256[] calldata _amounts
    ) public onlyOwner {
        for (uint256 i = 0; i < _users.length; i++) {
            claimed[_users[i]] = _amounts[i];
        }
    }

    function setClaim(address _user, uint256 _amount) public onlyOwner {
        claimed[_user] = _amount;
        isClaimed[_user] = false;
    }

    //Views
    function getState(address _user) public view returns (string memory) {
        if (claimed[_user] > 0) {
            if (isClaimed[_user]) {
                return "HasClaimed";
            } else {
                return "PendingClaimed";
            }
        } else {
            return "NotClaimed";
        }
    }

    // Callback
    receive() external payable {
        revert("Cannot receive ether");
    }

    fallback() external payable {
        revert("Cannot receive ether");
    }
}
