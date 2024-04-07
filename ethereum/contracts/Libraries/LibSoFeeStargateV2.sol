// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFeeV2} from "../Interfaces/ILibSoFeeV2.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";

// Stargate
contract LibSoFeeStargateV2 is ILibSoFeeV2, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //---------------------------------------------------------------------------
    // VARIABLES

    uint256 public constant DENOMINATOR = 1e18;
    uint256 public soFee;
    uint256 public transferForGas;
    uint256 public soBasicFee;
    address public soBasicBeneficiary;

    constructor(
        uint256 _soFee,
        uint256 _transferForGas,
        uint256 _soBasicFee,
        address _soBasicBeneficiary
    ) {
        soFee = _soFee;
        transferForGas = _transferForGas;
        soBasicFee = _soBasicFee;
        soBasicBeneficiary = _soBasicBeneficiary;
    }

    function setBasicBeneficiary(
        address _soBasicBeneficiary
    ) external onlyOwner {
        soBasicBeneficiary = _soBasicBeneficiary;
    }

    function setBasicFee(uint256 _soBasicFee) external onlyOwner {
        soBasicFee = _soBasicFee;
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

    function getBasicBeneficiary() external view override returns (address) {
        return soBasicBeneficiary;
    }

    function getBasicFee() external view override returns (uint256) {
        return soBasicFee;
    }

    function setTransferForGas(uint256 _transferForGas) external onlyOwner {
        transferForGas = _transferForGas;
    }

    function getTransferForGas() external view override returns (uint256) {
        return transferForGas;
    }

    function getVersion() external pure override returns (string memory) {
        return "StargateV2";
    }
}
