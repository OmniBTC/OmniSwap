// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";

// Stargate
contract LibSoFeeBoolV1 is ILibSoFee, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //---------------------------------------------------------------------------
    // VARIABLES

    uint256 public constant RAY = 1e27;
    uint256 public soFee;

    constructor(uint256 _soFee) {
        soFee = _soFee;
    }

    function setFee(uint256 _soFee) external onlyOwner {
        soFee = _soFee;
    }

    function getRestoredAmount(
        uint256 _amountIn
    ) external view override returns (uint256 r) {
        // calculate the amount to be restored
        r = _amountIn.mul(RAY).div((RAY - soFee));
        return r;
    }

    function getFees(
        uint256 _amountIn
    ) external view override returns (uint256 s) {
        // calculate the so fee
        s = _amountIn.mul(soFee).div(RAY);
        return s;
    }

    function getTransferForGas() external view override returns (uint256) {
        return 0;
    }

    function getVersion() external pure override returns (string memory) {
        return "BoolV1";
    }
}
