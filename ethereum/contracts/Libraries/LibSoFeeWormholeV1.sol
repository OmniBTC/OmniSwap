// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";
import {ILibPrice} from "../Interfaces/ILibPrice.sol";
import {IAggregatorV3Interface} from "../Interfaces/Chainlink/IAggregatorV3Interface.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";

contract LibSoFeeWormholeV1 is ILibSoFee, ILibPrice, Ownable, ReentrancyGuard {
    using SafeMath for uint256;

    //---------------------------------------------------------------------------
    // VARIABLES

    struct ChainlinkConfig {
        address router;
        // Countdown flag
        bool flag;
    }

    struct PriceConfig {
        ChainlinkConfig[] chainlink;
        // Update time interval
        uint256 interval;
    }

    struct PriceData {
        // The currnet price ratio of native coins
        uint256 currentPriceRatio;
        // Last update timestamp
        uint256 lastUpdateTimestamp;
    }

    uint256 public constant RAY = 1e27;

    uint256 public soFee;

    // Destination wormhole chain id => Oracle config
    mapping(uint16 => PriceConfig) priceConfig;
    mapping(uint16 => PriceData) priceData;

    //---------------------------------------------------------------------------
    // EVENT
    event UpdatePriceConfig(
        uint16 chainId,
        ChainlinkConfig[] chainlink,
        uint256 interval
    );
    event UpdatePriceInterval(uint16 chainId, uint256 interval);
    event UpdatePriceRatio(address sender, uint256 currentRatio);

    constructor(uint256 _soFee) {
        soFee = _soFee;
    }

    function setFee(uint256 _soFee) external onlyOwner {
        soFee = _soFee;
    }

    function setPriceConfig(
        uint16 _chainId,
        ChainlinkConfig[] memory _chainlink,
        uint256 _interval
    ) external onlyOwner {
        delete priceConfig[_chainId].chainlink;
        for (uint256 i = 0; i < _chainlink.length; i++) {
            priceConfig[_chainId].chainlink.push(
                ChainlinkConfig(_chainlink[i].router, _chainlink[i].flag)
            );
        }
        priceConfig[_chainId].interval = _interval;
        emit UpdatePriceConfig(_chainId, _chainlink, _interval);
    }

    function setPriceInterval(
        uint16 _chainId,
        uint256 _interval
    ) external onlyOwner {
        priceConfig[_chainId].interval = _interval;
        emit UpdatePriceInterval(_chainId, _interval);
    }

    function getPriceRatioByChainlink(
        uint16 _chainId,
        PriceConfig memory _config
    ) external view returns (uint256) {
        uint256 _ratio = RAY;
        for (uint256 i = 0; i < _config.chainlink.length; i++) {
            IAggregatorV3Interface _aggregator = IAggregatorV3Interface(
                _config.chainlink[i].router
            );
            (, int256 _price, , , ) = _aggregator.latestRoundData();
            uint8 _decimals = _aggregator.decimals();
            if (_price <= 0) {
                return priceData[_chainId].currentPriceRatio;
            }
            if (_config.chainlink[i].flag) {
                _ratio = _ratio.mul(10 ** _decimals).div(uint256(_price));
            } else {
                _ratio = _ratio.mul(uint256(_price)).div(10 ** _decimals);
            }
        }
        return _ratio;
    }

    function getPriceRatio(
        uint16 _chainId
    ) public view returns (uint256, bool) {
        PriceConfig memory _config = priceConfig[_chainId];
        if (_config.chainlink.length == 0) {
            return (priceData[_chainId].currentPriceRatio, false);
        }
        if (
            priceData[_chainId].lastUpdateTimestamp.add(_config.interval) >=
            block.timestamp
        ) {
            return (priceData[_chainId].currentPriceRatio, false);
        }
        try this.getPriceRatioByChainlink(_chainId, _config) returns (
            uint256 _result
        ) {
            return (_result, true);
        } catch {
            return (priceData[_chainId].currentPriceRatio, false);
        }
    }

    function updatePriceRatio(uint16 _chainId) external returns (uint256) {
        (uint256 _ratio, bool _flag) = getPriceRatio(_chainId);
        if (_flag) {
            priceData[_chainId].currentPriceRatio = _ratio;
            priceData[_chainId].lastUpdateTimestamp = block.timestamp;
            emit UpdatePriceRatio(msg.sender, _ratio);
        }
        return _ratio;
    }

    function setPriceRatio(uint16 _chainId, uint256 _ratio) external onlyOwner {
        priceData[_chainId].currentPriceRatio = _ratio;
        priceData[_chainId].lastUpdateTimestamp = block.timestamp;
        emit UpdatePriceRatio(msg.sender, _ratio);
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
        return "WormholeV1";
    }
}
