// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract GenesisBoxStaking {
    using SafeMath for uint256;

    IERC721 public nftContract;

    mapping(uint256 => uint256) public tokenPoints;

    event NFTReceived(address from, uint256 tokenId, uint256 points);

    constructor(address _nftContract) {
        nftContract = IERC721(_nftContract);
    }

    function receiveNFT(uint256 tokenId) public {
        require(nftContract.ownerOf(tokenId) == msg.sender, "NOT OWNER");

        nftContract.transferFrom(msg.sender, address(this), tokenId);

        uint256 points = calculatePoints(tokenId);

        tokenPoints[tokenId] = points;

        emit NFTReceived(msg.sender, tokenId, points);
    }

    function calculatePoints(uint256 tokenId) internal view returns (uint256) {
        uint256 random = uint256(keccak256(abi.encodePacked(address(msg.sender), tokenId)));

        uint256 points = random.mod(1001).add(500);

        return points;
    }

    function getPoints(uint256 tokenId) public view returns (uint256) {
        return tokenPoints[tokenId];
    }
}