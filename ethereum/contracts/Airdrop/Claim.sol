// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

contract Claim is ReentrancyGuard, Pausable, Ownable {
    // Start time
    uint256 private start;
    // Claimed token
    IERC20 public token;
    // merkle root
    bytes32 public merkleRoot;
    // Whether claimed
    mapping(uint256 => uint256) private claimedBitMap;

    constructor(uint256 _start, IERC20 _token, bytes32 _merkleRoot) {
        require(_start > block.timestamp, "StartErr");

        start = _start;
        token = _token;
        merkleRoot = _merkleRoot;
    }

    // Functions

    function claim(
        uint256 _index,
        uint256 _amount,
        bytes32[] calldata _proof
    ) public whenNotPaused nonReentrant {
        require(block.timestamp >= start, "NotStart");

        require(
            isValidUser(_index, _msgSender(), _amount, _proof),
            "InvalidUser"
        );
        require(!isClaimed(_index), "HasClaimed");

        SafeERC20.safeTransfer(token, _msgSender(), _amount);
        _setClaimed(_index);
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

    function setRoot(bytes32 _merkleRoot) public onlyOwner {
        merkleRoot = _merkleRoot;
    }

    function setClaimed(uint256 _index) public onlyOwner {
        _setClaimed(_index);
    }

    // Private
    function _setClaimed(uint256 _index) private {
        uint256 claimedWordIndex = _index / 256;
        uint256 claimedBitIndex = _index % 256;
        claimedBitMap[claimedWordIndex] =
            claimedBitMap[claimedWordIndex] |
            (1 << claimedBitIndex);
    }

    // Views
    function isClaimed(uint256 _index) public view returns (bool) {
        uint256 claimedWordIndex = _index / 256;
        uint256 claimedBitIndex = _index % 256;
        uint256 claimedWord = claimedBitMap[claimedWordIndex];
        uint256 mask = (1 << claimedBitIndex);
        return claimedWord & mask == mask;
    }

    function isValidUser(
        uint256 _index,
        address _user,
        uint256 _amount,
        bytes32[] calldata _proof
    ) public view returns (bool) {
        bytes32 node = keccak256(abi.encodePacked(_index, _user, _amount));
        return MerkleProof.verify(_proof, merkleRoot, node);
    }

    function getState(
        uint256 _index,
        address _user,
        uint256 _amount,
        bytes32[] calldata _proof
    ) public view returns (string memory) {
        if (isValidUser(_index, _user, _amount, _proof)) {
            if (isClaimed(_index)) {
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
