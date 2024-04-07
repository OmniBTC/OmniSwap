// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";

// Stargate
contract LibSoFeeStargateV1 is ILibSoFee, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //---------------------------------------------------------------------------
    // VARIABLES

    uint256 public constant DENOMINATOR = 1e18;
    uint256 public soFee;
    uint256 public transferForGas;

    constructor(uint256 _soFee, uint256 _transferForGas) {
        soFee = _soFee;
        transferForGas = _transferForGas;
    }

    function setFee(uint256 _soFee) external onlyOwner {
        soFee = _soFee;
    }

    function getRestoredAmount(
        uint256 _amount
    ) external view override returns (uint256 r) {
        // calculate the amount to be restored
        r = _amount.mul(DENOMINATOR).div((DENOMINATOR - soFee));
        return r;
    }

    function getFees(
        uint256 _amount
    ) external view override returns (uint256 s) {
        // calculate the so fee
        s = _amount.mul(soFee).div(DENOMINATOR);
        return s;
    }

    function setTransferForGas(uint256 _transferForGas) external onlyOwner {
        transferForGas = _transferForGas;
    }

    function getTransferForGas() external view override returns (uint256) {
        return transferForGas;
    }

    function getVersion() external pure override returns (string memory) {
        return "StargateV1";
    }
}
