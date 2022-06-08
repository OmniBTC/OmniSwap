// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";

contract StargateFeeLibraryV02 is ILibSoFee, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //---------------------------------------------------------------------------
    // VARIABLES

    uint256 public constant DENOMINATOR = 1e18;
    uint256 public soFee;

    constructor(uint256 _soFee) {
        soFee = _soFee;
    }

    function setFee(uint256 _soFee) external onlyOwner {
        soFee = _soFee;
    }

    function getFees(uint256 _amount)
        external
        view
        override
        returns (uint256 s)
    {
        // calculate the so fee
        s = _amount.mul(soFee).div(DENOMINATOR);
        return s;
    }

    function getVersion() external pure override returns (string memory) {
        return "1.0.0";
    }
}