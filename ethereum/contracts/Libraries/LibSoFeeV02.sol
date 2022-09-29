// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";
import {IUniswapV2Router01} from "../Interfaces/IUniswapV2Router01.sol";
import {IQuoter} from "../Interfaces/IQuoter.sol";

// Wormhole
contract LibSoFeeV02 is ILibSoFee, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    bytes4 private constant _FUNC1 = IUniswapV2Router01.getAmountsOut.selector;
    bytes4 private constant _FUNC2 = IQuoter.quoteExactInput.selector;

    //---------------------------------------------------------------------------
    // VARIABLES

    struct PriceConfig {
        address router;
        // function sig
        bytes4 priceFunc;
        uint256 lastUpdateTimestamp;
        uint256 amountIn;
        // update interval
        uint256 interval;
        // Uniswap v2 path
        address[] pathV2;
        // Uniswap v3 path
        bytes pathV3;
    }

    uint256 public constant DENOMINATOR = 1e18;
    uint256 public soFee;
    mapping(address => PriceConfig) priceConfig;

    constructor(uint256 _soFee) {
        soFee = _soFee;
    }

    function setFee(uint256 _soFee) external onlyOwner {
        soFee = _soFee;
    }

    function setPriceConfig(
        address _tokenAddress,
        address _router,
        uint256 _amountIn,
        bytes4 _func,
        uint256 _interval,
        address[] memory _path
    ) external onlyOwner {
        require(_func == _FUNC1, "Func error");
        require(_amountIn > 0, "Amount<=0");
        priceConfig[_tokenAddress].router = _router;
        priceConfig[_tokenAddress].amountIn = _amountIn;
        priceConfig[_tokenAddress].priceFunc = _func;
        priceConfig[_tokenAddress].interval = _interval;
        priceConfig[_tokenAddress].pathV2 = _path;
    }

    function setPriceConfig(
        address _tokenAddress,
        address _router,
        uint256 _amountIn,
        bytes4 _func,
        uint256 _interval,
        bytes memory _path
    ) external onlyOwner {
        require(_func == _FUNC2, "Func error");
        require(_amountIn > 0, "Amount<=0");
        priceConfig[_tokenAddress].router = _router;
        priceConfig[_tokenAddress].amountIn = _amountIn;
        priceConfig[_tokenAddress].priceFunc = _func;
        priceConfig[_tokenAddress].interval = _interval;
        priceConfig[_tokenAddress].pathV3 = _path;
    }

    function setPriceInterval(address _tokenAddress, uint256 _interval)
        external
        onlyOwner
    {
        priceConfig[_tokenAddress].interval = _interval;
    }

    function setPriceAmount(address _tokenAddress, uint256 _amountIn)
        external
        onlyOwner
    {
        require(_amountIn > 0, "Amount<=0");
        priceConfig[_tokenAddress].amountIn = _amountIn;
    }

    function getPrice(address _tokenAddress) external returns (uint256) {
        // todo Add interval
        // todo Add try catch ?
        // todo Add price update
        if (priceConfig[_tokenAddress].priceFunc == _FUNC1) {
            uint256[] memory _data = IUniswapV2Router01(
                priceConfig[_tokenAddress].router
            ).getAmountsOut(
                    priceConfig[_tokenAddress].amountIn,
                    priceConfig[_tokenAddress].pathV2
                );
            return _data[_data.length - 1];
        } else if (priceConfig[_tokenAddress].priceFunc == _FUNC2) {
            return
                IQuoter(priceConfig[_tokenAddress].router).quoteExactInput(
                    priceConfig[_tokenAddress].pathV3,
                    priceConfig[_tokenAddress].amountIn
                );
        } else {
            return 0;
        }
    }

    function getRestoredAmount(uint256 _amountIn)
        external
        view
        override
        returns (uint256 r)
    {
        // calculate the amount to be restored
        r = _amountIn.mul(DENOMINATOR).div((DENOMINATOR - soFee));
        return r;
    }

    function getFees(uint256 _amountIn)
        external
        view
        override
        returns (uint256 s)
    {
        // calculate the so fee
        s = _amountIn.mul(soFee).div(DENOMINATOR);
        return s;
    }

    function getTransferForGas() external view override returns (uint256) {
        return 0;
    }

    function getVersion() external pure override returns (string memory) {
        return "2.0.0";
    }
}
