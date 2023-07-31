// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Claim is
    Initializable,
    OwnableUpgradeable,
    PausableUpgradeable,
    ReentrancyGuardUpgradeable
{
    using SafeMathUpgradeable for uint256;

    // Start time
    uint256 private start;
    // Claimed token
    IERC20Upgradeable public token;
    // Claimed amount
    mapping(address => uint256) public claimed;
    // Whether claimed
    mapping(address => bool) public isClaimed;

    function initialize(uint256 _start, IERC20Upgradeable _token)
        public
        initializer
    {
        require(_start > block.timestamp, "StartErr");

        start = _start;
        token = _token;

        __Ownable_init();
        __Pausable_init();
        __ReentrancyGuard_init();
    }

    //Functions

    function claim() public whenNotPaused nonReentrant {
        require(block.timestamp >= start, "NotStart");

        uint256 amount = claimed[_msgSender()];
        require(amount > 0, "AmountZero");
        require(isClaimed[_user], "HasClaimed");

        token.safeTransfer(_msgSender(), amount);
        isClaimed[_user] = false;
    }

    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    function reFund(IERC20Upgradeable _token, uint256 _amount)
        public
        onlyOwner
    {
        _token.safeTransfer(_msgSender(), _amount);
    }

    function batchSetClaim(address[] _users, uint256[] _amounts)
        public
        onlyOwner
    {
        for (uint256 i = 0; i < _users.length; i++) {
            claimed[_users[i]] = _amounts[i];
        }
    }

    function setClaim(address _user, uint256 _amount) public onlyOwner {
        claimed[_user] = _amount;
        isClaimed[_user] = false;
    }

    //Views
    function getState(address _user) public view returns (string) {
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
