// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import {IUniswapV2Router01} from "../Interfaces/UniswapV2/IUniswapV2Router01.sol";
import {IUniswapV2Router01AVAX} from "../Interfaces/UniswapV2/IUniswapV2Router01AVAX.sol";
import {ISwapRouter} from "../Interfaces/UniswapV3/ISwapRouter.sol";
import {ISyncSwapRouter} from "../Interfaces/Syncswap/ISyncSwapRouter.sol";
import {IMuteRouter} from "../Interfaces/Mute/IMuteRouter.sol";
import {IQuickSwapRouter} from "../Interfaces/Quickswap/IQuickSwapRouter.sol";
import {IAerodrome} from "../Interfaces/Velodrome/IAerodrome.sol";
import {ISwapRouter02} from "../Interfaces/UniswapV3/ISwapRouter02.sol";
import {IVault} from "../Interfaces/Balancer/IVault.sol";
import {ICurveFi} from "../Interfaces/Curve/ICurveFi.sol";
import {IWombatRouter} from "../Interfaces/Wormbat/IWombatRouter.sol";
import {ILBRouter} from "../Interfaces/TraderJoe/ILBRouter.sol";
import {IGMXV1Router} from "../Interfaces/GMX/IGMXV1Router.sol";
import {IPearlRouter} from "../Interfaces/Pearl/IPearlRouter.sol";
import {IiZiSwap} from "../Interfaces/Iziswap/IiZiSwap.sol";
import {ICamelotRouter} from "../Interfaces/Camelot/ICamelotRouter.sol";
import {IMetaAggregationRouterV2} from "../Interfaces/Kyberswap/IMetaAggregationRouterV2.sol";
import {IOneInchGenericRouter} from "../Interfaces/OneInch/IOneInchGenericRouter.sol";
import {IOneInchClipperRouter} from "../Interfaces/OneInch/IOneInchClipperRouter.sol";
import {IOneInchUnoswapRouter} from "../Interfaces/OneInch/IOneInchUnoswapRouter.sol";
import {IOneInchUnoswapV3Router} from "../Interfaces/OneInch/IOneInchUnoswapV3Router.sol";

contract LibCorrectSwapV1 {
    // UniswapV2
    bytes4 private constant _FUNC1 =
        IUniswapV2Router01.swapExactETHForTokens.selector;
    bytes4 private constant _FUNC2 =
        IUniswapV2Router01AVAX.swapExactAVAXForTokens.selector;
    bytes4 private constant _FUNC3 =
        IUniswapV2Router01.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC4 =
        IUniswapV2Router01AVAX.swapExactTokensForAVAX.selector;
    bytes4 private constant _FUNC5 =
        IUniswapV2Router01.swapExactTokensForTokens.selector;

    // UniswapV3
    bytes4 private constant _FUNC6 = ISwapRouter.exactInput.selector;

    // zksync,Syncswap
    bytes4 private constant _FUNC7 = ISyncSwapRouter.swap.selector;

    // zksync,Muteswap
    bytes4 private constant _FUNC8 = IMuteRouter.swapExactETHForTokens.selector;
    bytes4 private constant _FUNC9 = IMuteRouter.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC10 =
        IMuteRouter.swapExactTokensForTokens.selector;

    // QuickswapV3
    bytes4 private constant _FUNC11 = IQuickSwapRouter.exactInput.selector;

    // base,Aerodrome
    bytes4 private constant _FUNC12 = IAerodrome.swapExactETHForTokens.selector;
    bytes4 private constant _FUNC13 = IAerodrome.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC14 =
        IAerodrome.swapExactTokensForTokens.selector;

    // UniswapV3
    bytes4 private constant _FUNC15 = ISwapRouter02.exactInput.selector;

    // BalancerV2
    bytes4 private constant _FUNC16 = IVault.swap.selector;

    // Curve
    bytes4 private constant _FUNC17 = ICurveFi.exchange.selector;
    bytes4 private constant _FUNC18 = ICurveFi.exchange_underlying.selector;

    // bsc,Wombat
    bytes4 private constant _FUNC19 =
        IWombatRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC20 =
        IWombatRouter.swapExactTokensForNative.selector;
    bytes4 private constant _FUNC21 =
        IWombatRouter.swapExactNativeForTokens.selector;

    // Trader Joe
    bytes4 private constant _FUNC22 =
        ILBRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC23 =
        ILBRouter.swapExactTokensForNATIVE.selector;
    bytes4 private constant _FUNC24 =
        ILBRouter.swapExactNATIVEForTokens.selector;

    // GMX V1
    bytes4 private constant _FUNC25 = IGMXV1Router.swap.selector;
    bytes4 private constant _FUNC26 = IGMXV1Router.swapTokensToETH.selector;
    bytes4 private constant _FUNC27 = IGMXV1Router.swapETHToTokens.selector;

    // PearlFi
    bytes4 private constant _FUNC28 =
        IPearlRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC29 =
        IPearlRouter.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC30 =
        IPearlRouter.swapExactETHForTokens.selector;

    // iZiSwap
    bytes4 private constant _FUNC31 = IiZiSwap.swapAmount.selector;

    // Camelot
    bytes4 private constant _FUNC32 =
        ICamelotRouter
            .swapExactTokensForTokensSupportingFeeOnTransferTokens
            .selector;
    bytes4 private constant _FUNC33 =
        ICamelotRouter
            .swapExactETHForTokensSupportingFeeOnTransferTokens
            .selector;
    bytes4 private constant _FUNC34 =
        ICamelotRouter
            .swapExactTokensForETHSupportingFeeOnTransferTokens
            .selector;

    // Kyberswap
    bytes4 private constant _FUNC35 =
        IMetaAggregationRouterV2.swapGeneric.selector;
    bytes4 private constant _FUNC36 = IMetaAggregationRouterV2.swap.selector;
    bytes4 private constant _FUNC37 =
        IMetaAggregationRouterV2.swapSimpleMode.selector;

    // 1inch
    bytes4 private constant _FUNC38 = IOneInchGenericRouter.swap.selector;
    bytes4 private constant _FUNC39 =
        IOneInchClipperRouter.clipperSwap.selector;
    bytes4 private constant _FUNC40 =
        IOneInchClipperRouter.clipperSwapTo.selector;
    bytes4 private constant _FUNC41 =
        IOneInchClipperRouter.clipperSwapToWithPermit.selector;
    bytes4 private constant _FUNC42 = IOneInchUnoswapRouter.unoswap.selector;
    bytes4 private constant _FUNC43 = IOneInchUnoswapRouter.unoswapTo.selector;
    bytes4 private constant _FUNC44 =
        IOneInchUnoswapRouter.unoswapToWithPermit.selector;
    bytes4 private constant _FUNC45 =
        IOneInchUnoswapV3Router.uniswapV3Swap.selector;
    bytes4 private constant _FUNC46 =
        IOneInchUnoswapV3Router.uniswapV3SwapTo.selector;
    bytes4 private constant _FUNC47 =
        IOneInchUnoswapV3Router.uniswapV3SwapToWithPermit.selector;

    mapping(bytes4 => bytes4) private _correctSwapFunc;
    mapping(bytes4 => string) private _swapErrors;

    constructor() {
        _correctSwapFunc[_FUNC3] = this.basicCorrectSwap.selector;
        _swapErrors[_FUNC3] = "basicCorrectSwap fail";
        _correctSwapFunc[_FUNC4] = this.basicCorrectSwap.selector;
        _swapErrors[_FUNC4] = "basicCorrectSwap fail";
        _correctSwapFunc[_FUNC5] = this.basicCorrectSwap.selector;
        _swapErrors[_FUNC5] = "basicCorrectSwap fail";
        _correctSwapFunc[_FUNC6] = this.exactInput.selector;
        _swapErrors[_FUNC6] = "exactInput fail";
        _correctSwapFunc[_FUNC7] = this.syncSwap.selector;
        _swapErrors[_FUNC7] = "syncSwap fail";
        _correctSwapFunc[_FUNC9] = this.muteSwap.selector;
        _swapErrors[_FUNC9] = "muteSwap fail";
        _correctSwapFunc[_FUNC10] = this.muteSwap.selector;
        _swapErrors[_FUNC10] = "muteSwap fail";
        _correctSwapFunc[_FUNC11] = this.quickExactInput.selector;
        _swapErrors[_FUNC11] = "quickExactInput fail";
        _correctSwapFunc[_FUNC13] = this.aerodrome.selector;
        _swapErrors[_FUNC13] = "aerodrome fail";
        _correctSwapFunc[_FUNC14] = this.aerodrome.selector;
        _swapErrors[_FUNC14] = "aerodrome fail";
        _correctSwapFunc[_FUNC15] = this.exactInputV2.selector;
        _swapErrors[_FUNC15] = "exactInputV2 fail";
        _correctSwapFunc[_FUNC16] = this.balancerV2SingleSwap.selector;
        _swapErrors[_FUNC16] = "balancerV2SingleSwap fail";
        _correctSwapFunc[_FUNC17] = this.curveExchange.selector;
        _swapErrors[_FUNC17] = "curveExchange fail";
        _correctSwapFunc[_FUNC18] = this.curveExchangeUnderlying.selector;
        _swapErrors[_FUNC18] = "curveExchangeUnderlying fail";
        _correctSwapFunc[_FUNC19] = this.wombatSwap.selector;
        _swapErrors[_FUNC19] = "wombatSwap fail";
        _correctSwapFunc[_FUNC20] = this.wombatSwap.selector;
        _swapErrors[_FUNC20] = "wombatSwap fail";
        _correctSwapFunc[_FUNC22] = this.traderJoeSwap.selector;
        _swapErrors[_FUNC22] = "traderJoeSwap fail";
        _correctSwapFunc[_FUNC23] = this.traderJoeSwap.selector;
        _swapErrors[_FUNC23] = "traderJoeSwap fail";
        _correctSwapFunc[_FUNC25] = this.GMXV1Swap.selector;
        _swapErrors[_FUNC25] = "GMXV1Swap fail";
        _correctSwapFunc[_FUNC26] = this.GMXV1Swap.selector;
        _swapErrors[_FUNC26] = "GMXV1Swap fail";
        _correctSwapFunc[_FUNC28] = this.pearlFiSwap.selector;
        _swapErrors[_FUNC28] = "pearlFiSwap fail";
        _correctSwapFunc[_FUNC29] = this.pearlFiSwap.selector;
        _swapErrors[_FUNC29] = "pearlFiSwap fail";
        _correctSwapFunc[_FUNC31] = this.iZiSwap.selector;
        _swapErrors[_FUNC31] = "iZiSwap fail";
        _correctSwapFunc[_FUNC32] = this.camelot.selector;
        _swapErrors[_FUNC32] = "camelot fail";
        _correctSwapFunc[_FUNC34] = this.camelot.selector;
        _swapErrors[_FUNC34] = "camelot fail";
        _correctSwapFunc[_FUNC35] = this.kyberswap.selector;
        _swapErrors[_FUNC35] = "kyberswap fail";
        _correctSwapFunc[_FUNC36] = this.kyberswap.selector;
        _swapErrors[_FUNC36] = "kyberswap fail";
        _correctSwapFunc[_FUNC37] = this.kyberswapSimple.selector;
        _swapErrors[_FUNC37] = "kyberswapSimple fail";
        _correctSwapFunc[_FUNC38] = this.oneInchGenericSwap.selector;
        _swapErrors[_FUNC38] = "oneInchGenericSwap fail";
        _correctSwapFunc[_FUNC39] = this.oneInchClipperSwap.selector;
        _swapErrors[_FUNC39] = "oneInchClipperSwap fail";
        _correctSwapFunc[_FUNC40] = this.oneInchClipperSwapTo.selector;
        _swapErrors[_FUNC40] = "oneInchClipperSwapTo fail";
        _correctSwapFunc[_FUNC41] = this
            .oneInchClipperSwapToWithPermit
            .selector;
        _swapErrors[_FUNC41] = "oneInchClipperSwapToWithPermit fail";
        _correctSwapFunc[_FUNC42] = this.oneInchUnoswapSwap.selector;
        _swapErrors[_FUNC42] = "oneInchUnoswapSwap fail";
        _correctSwapFunc[_FUNC43] = this.oneInchUnoswapSwapTo.selector;
        _swapErrors[_FUNC43] = "oneInchUnoswapSwapTo fail";
        _correctSwapFunc[_FUNC44] = this
            .oneInchUnoswapSwapToWithPermit
            .selector;
        _swapErrors[_FUNC44] = "oneInchUnoswapSwapToWithPermit fail";
        _correctSwapFunc[_FUNC45] = this.oneInchUniswapV3Swap.selector;
        _swapErrors[_FUNC45] = "oneInchUniswapV3Swap fail";
        _correctSwapFunc[_FUNC46] = this.oneInchUniswapV3SwapTo.selector;
        _swapErrors[_FUNC46] = "oneInchUniswapV3SwapTo fail";
        _correctSwapFunc[_FUNC47] = this
            .oneInchUniswapV3SwapToWithPermit
            .selector;
        _swapErrors[_FUNC47] = "oneInchUniswapV3SwapToWithPermit fail";
    }

    //---------------------------------------------------------------------------
    // External Method

    // @dev Correct input of destination chain swapData
    function correctSwap(bytes calldata _data, uint256 _amount)
        external
        returns (bytes memory)
    {
        bytes4 sig = bytes4(_data[:4]);
        if (_correctSwapFunc[sig] == bytes4(0)) {
            return _data;
        } else {
            (bool success, bytes memory _result) = address(this).call(
                abi.encodeWithSelector(_correctSwapFunc[sig], _data, _amount)
            );
            if (success) {
                return _result;
            } else {
                revert(_swapErrors[sig]);
            }
        }
    }

    // @dev Fix min amount
    function fixMinAmount(bytes calldata _data, uint256 _deltaMinAmount)
        external
        view
        returns (uint256, bytes memory)
    {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC1 || sig == _FUNC2) {
            (
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(_data[4:], (uint256, address[], address, uint256));
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC3 || sig == _FUNC4 || sig == _FUNC5) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, address[], address, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC6) {
            ISwapRouter.ExactInputParams memory params = abi.decode(
                _data[4:],
                (ISwapRouter.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC7) {
            (
                ISyncSwapRouter.SwapPath[] memory _paths,
                uint256 _amountOutMin,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (ISyncSwapRouter.SwapPath[], uint256, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _paths,
                    _amountOutMin + _deltaMinAmount,
                    _deadline
                )
            );
        } else if (sig == _FUNC8) {
            (
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                uint256 _deadline,
                bool[] memory _stable
            ) = abi.decode(
                    _data[4:],
                    (uint256, address[], address, uint256, bool[])
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline,
                    _stable
                )
            );
        } else if (sig == _FUNC9 || sig == _FUNC10) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                uint256 _deadline,
                bool[] memory _stable
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, address[], address, uint256, bool[])
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline,
                    _stable
                )
            );
        } else if (sig == _FUNC11) {
            IQuickSwapRouter.ExactInputParams memory params = abi.decode(
                _data[4:],
                (IQuickSwapRouter.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC12) {
            (
                uint256 _amountOutMin,
                IAerodrome.Route[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, IAerodrome.Route[], address, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC13 || sig == _FUNC14) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                IAerodrome.Route[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, IAerodrome.Route[], address, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC15) {
            ISwapRouter02.ExactInputParams memory params = abi.decode(
                _data[4:],
                (ISwapRouter02.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC16) {
            (
                IVault.SingleSwap memory singleSwap,
                IVault.FundManagement memory funds,
                uint256 limit,
                uint256 deadline
            ) = abi.decode(
                    _data[4:],
                    (IVault.SingleSwap, IVault.FundManagement, uint256, uint256)
                );
            if (singleSwap.kind == IVault.SwapKind.GIVEN_OUT) {
                revert("not support GIVEN_OUT");
            }
            return (
                limit,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    singleSwap,
                    funds,
                    limit + _deltaMinAmount,
                    deadline
                )
            );
        } else if (sig == _FUNC17) {
            (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
                _data[4:],
                (int128, int128, uint256, uint256)
            );
            return (
                min_dy,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    i,
                    j,
                    dx,
                    min_dy + _deltaMinAmount
                )
            );
        } else if (sig == _FUNC18) {
            (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
                _data[4:],
                (int128, int128, uint256, uint256)
            );
            return (
                min_dy,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    i,
                    j,
                    dx,
                    min_dy + _deltaMinAmount
                )
            );
        } else if (sig == _FUNC19 || sig == _FUNC20) {
            (
                address[] memory _tokenPath,
                address[] memory _poolPath,
                uint256 _amount,
                uint256 _minimumToAmount,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (address[], address[], uint256, uint256, address, uint256)
                );
            return (
                _minimumToAmount,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _tokenPath,
                    _poolPath,
                    _amount,
                    _minimumToAmount + _deltaMinAmount,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC21) {
            (
                address[] memory _tokenPath,
                address[] memory _poolPath,
                uint256 _minimumToAmount,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (address[], address[], uint256, address, uint256)
                );
            return (
                _minimumToAmount,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _tokenPath,
                    _poolPath,
                    _minimumToAmount + _deltaMinAmount,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC22 || sig == _FUNC23) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                ILBRouter.Path memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, ILBRouter.Path, address, uint256)
                );

            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC24) {
            (
                uint256 _amountOutMin,
                ILBRouter.Path memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, ILBRouter.Path, address, uint256)
                );

            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC25 || sig == _FUNC26) {
            (
                address[] memory _path,
                uint256 _amount,
                uint256 _minOut,
                address _receiver
            ) = abi.decode(_data[4:], (address[], uint256, uint256, address));

            return (
                _minOut,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _path,
                    _amount,
                    _minOut + _deltaMinAmount,
                    _receiver
                )
            );
        } else if (sig == _FUNC27) {
            (address[] memory _path, uint256 _minOut, address _receiver) = abi
                .decode(_data[4:], (address[], uint256, address));

            return (
                _minOut,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _path,
                    _minOut + _deltaMinAmount,
                    _receiver
                )
            );
        } else if (sig == _FUNC28 || sig == _FUNC29) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                IPearlRouter.route[] memory _routes,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, IPearlRouter.route[], address, uint256)
                );

            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _routes,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC30) {
            (
                uint256 _amountOutMin,
                IPearlRouter.route[] memory _routes,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, IPearlRouter.route[], address, uint256)
                );

            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    bytes4(_data[:4]),
                    _amountOutMin + _deltaMinAmount,
                    _routes,
                    _to,
                    _deadline
                )
            );
        } else if (sig == _FUNC31) {
            IiZiSwap.SwapAmountParams memory params = abi.decode(
                _data[4:],
                (IiZiSwap.SwapAmountParams)
            );
            uint256 _amountOutMin = params.minAcquired;
            params.minAcquired = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC33) {
            (
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                address _referrer,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, address[], address, address, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _referrer,
                    _deadline
                )
            );
        } else if (sig == _FUNC32 || sig == _FUNC34) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                address[] memory _path,
                address _to,
                address _referrer,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, address[], address, address, uint256)
                );
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    _amount,
                    _amountOutMin + _deltaMinAmount,
                    _path,
                    _to,
                    _referrer,
                    _deadline
                )
            );
        } else if (sig == _FUNC35 || sig == _FUNC36) {
            IMetaAggregationRouterV2.SwapExecutionParams memory params = abi
                .decode(
                    _data[4:],
                    (IMetaAggregationRouterV2.SwapExecutionParams)
                );
            uint256 _amountOutMin = params.desc.minReturnAmount;
            params.desc.minReturnAmount = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC37) {
            (
                address caller,
                IMetaAggregationRouterV2.SwapDescriptionV2 memory desc,
                bytes memory executorData,
                bytes memory clientData
            ) = abi.decode(
                    _data[4:],
                    (
                        address,
                        IMetaAggregationRouterV2.SwapDescriptionV2,
                        bytes,
                        bytes
                    )
                );

            uint256 _amountOutMin = desc.minReturnAmount;
            desc.minReturnAmount = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    caller,
                    desc,
                    executorData,
                    clientData
                )
            );
        } else if (sig == _FUNC38) {
            (
                address executor,
                IOneInchGenericRouter.SwapDescription memory desc,
                bytes memory permit,
                bytes memory data
            ) = abi.decode(
                    _data[4:],
                    (
                        address,
                        IOneInchGenericRouter.SwapDescription,
                        bytes,
                        bytes
                    )
                );
            uint256 _amountOutMin = desc.minReturnAmount;
            desc.minReturnAmount = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(sig, executor, desc, permit, data)
            );
        } else if (sig == _FUNC39) {
            (
                address clipperExchange,
                address srcToken,
                address dstToken,
                uint256 inputAmount,
                uint256 outputAmount,
                uint256 goodUntil,
                bytes32 r,
                bytes32 vs
            ) = abi.decode(
                    _data[4:],
                    (
                        address,
                        address,
                        address,
                        uint256,
                        uint256,
                        uint256,
                        bytes32,
                        bytes32
                    )
                );
            uint256 _amountOutMin = outputAmount;
            outputAmount = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    clipperExchange,
                    srcToken,
                    dstToken,
                    inputAmount,
                    outputAmount,
                    goodUntil,
                    r,
                    vs
                )
            );
        } else if (sig == _FUNC40) {
            (
                address clipperExchange,
                address payable recipient,
                address srcToken,
                address dstToken,
                uint256 inputAmount,
                uint256 outputAmount,
                uint256 goodUntil,
                bytes32 r,
                bytes32 vs
            ) = abi.decode(
                    _data[4:],
                    (
                        address,
                        address,
                        address,
                        address,
                        uint256,
                        uint256,
                        uint256,
                        bytes32,
                        bytes32
                    )
                );
            uint256 _amountOutMin = outputAmount;
            outputAmount = _amountOutMin + _deltaMinAmount;
            return (
                outputAmount,
                abi.encodeWithSelector(
                    sig,
                    clipperExchange,
                    recipient,
                    srcToken,
                    dstToken,
                    inputAmount,
                    outputAmount,
                    goodUntil,
                    r,
                    vs
                )
            );
        } else if (sig == _FUNC41) {
            (
                address clipperExchange,
                address payable recipient,
                address srcToken,
                address dstToken,
                uint256 inputAmount,
                uint256 outputAmount,
                uint256 goodUntil,
                bytes32 r,
                bytes32 vs,
                bytes memory permit
            ) = abi.decode(
                    _data[4:],
                    (
                        address,
                        address,
                        address,
                        address,
                        uint256,
                        uint256,
                        uint256,
                        bytes32,
                        bytes32,
                        bytes
                    )
                );
            uint256 _amountOutMin = outputAmount;
            outputAmount = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    clipperExchange,
                    recipient,
                    srcToken,
                    dstToken,
                    inputAmount,
                    outputAmount,
                    goodUntil,
                    r,
                    vs,
                    permit
                )
            );
        } else if (_FUNC42 == sig) {
            (
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools
            ) = abi.decode(_data[4:], (address, uint256, uint256, uint256[]));
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(sig, srcToken, amount, minReturn, pools)
            );
        } else if (_FUNC43 == sig) {
            (
                address payable recipient,
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools
            ) = abi.decode(
                    _data[4:],
                    (address, address, uint256, uint256, uint256[])
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    recipient,
                    srcToken,
                    amount,
                    minReturn,
                    pools
                )
            );
        } else if (_FUNC44 == sig) {
            (
                address payable recipient,
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools,
                bytes memory permit
            ) = abi.decode(
                    _data[4:],
                    (address, address, uint256, uint256, uint256[], bytes)
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    recipient,
                    srcToken,
                    amount,
                    minReturn,
                    pools,
                    permit
                )
            );
        } else if (_FUNC45 == sig) {
            (uint256 amount, uint256 minReturn, uint256[] memory pools) = abi
                .decode(_data[4:], (uint256, uint256, uint256[]));
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(sig, amount, minReturn, pools)
            );
        } else if (_FUNC46 == sig) {
            (
                address payable recipient,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools
            ) = abi.decode(_data[4:], (address, uint256, uint256, uint256[]));
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(sig, recipient, amount, minReturn, pools)
            );
        } else if (_FUNC47 == sig) {
            (
                address payable recipient,
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools,
                bytes memory permit
            ) = abi.decode(
                    _data[4:],
                    (address, address, uint256, uint256, uint256[], bytes)
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    recipient,
                    srcToken,
                    amount,
                    minReturn,
                    pools,
                    permit
                )
            );
        }

        revert("fix amount fail!");
    }

    function basicCorrectSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            address[] memory _path,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, address[], address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _path,
                _to,
                _deadline
            );
    }

    function exactInput(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        ISwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function syncSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ISyncSwapRouter.SwapPath[] memory _paths,
            uint256 _amountOutMin,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (ISyncSwapRouter.SwapPath[], uint256, uint256)
            );

        uint256 fromAmountSum;
        for (uint256 i = 0; i < _paths.length; i++) {
            fromAmountSum = fromAmountSum + _paths[i].amountIn;
        }

        if (fromAmountSum > 0) {
            for (uint256 i = 0; i < _paths.length; i++) {
                _paths[i].amountIn =
                    (_amount * _paths[i].amountIn) /
                    fromAmountSum;
            }
        }

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _paths,
                _amountOutMin,
                _deadline
            );
    }

    function muteSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            address[] memory _path,
            address _to,
            uint256 _deadline,
            bool[] memory _stable
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, address[], address, uint256, bool[])
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _path,
                _to,
                _deadline,
                _stable
            );
    }

    function quickExactInput(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        IQuickSwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (IQuickSwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function aerodrome(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            IAerodrome.Route[] memory _path,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, IAerodrome.Route[], address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _path,
                _to,
                _deadline
            );
    }

    function exactInputV2(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        ISwapRouter02.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter02.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function balancerV2SingleSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            IVault.SingleSwap memory singleSwap,
            IVault.FundManagement memory funds,
            uint256 limit,
            uint256 deadline
        ) = abi.decode(
                _data[4:],
                (IVault.SingleSwap, IVault.FundManagement, uint256, uint256)
            );
        singleSwap.amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                singleSwap,
                funds,
                limit,
                deadline
            );
    }

    function curveExchange(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }

    function curveExchangeUnderlying(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }

    function wombatSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address[] memory _tokenPath,
            address[] memory _poolPath,
            ,
            uint256 _minimumToAmount,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (address[], address[], uint256, uint256, address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _tokenPath,
                _poolPath,
                _amount,
                _minimumToAmount,
                _to,
                _deadline
            );
    }

    function traderJoeSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            ILBRouter.Path memory _path,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, ILBRouter.Path, address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _path,
                _to,
                _deadline
            );
    }

    function GMXV1Swap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (address[] memory _path, , uint256 _minOut, address _receiver) = abi
            .decode(_data[4:], (address[], uint256, uint256, address));

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _path,
                _amount,
                _minOut,
                _receiver
            );
    }

    function pearlFiSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            IPearlRouter.route[] memory _routes,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, IPearlRouter.route[], address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _routes,
                _to,
                _deadline
            );
    }

    function iZiSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        IiZiSwap.SwapAmountParams memory params = abi.decode(
            _data[4:],
            (IiZiSwap.SwapAmountParams)
        );
        require(_amount <= type(uint128).max, "Value too large for uint128");
        params.amount = uint128(_amount);
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function camelot(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            ,
            uint256 _amountOutMin,
            address[] memory _path,
            address _to,
            address _referrer,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, address[], address, address, uint256)
            );

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                _amount,
                _amountOutMin,
                _path,
                _to,
                _referrer,
                _deadline
            );
    }

    function kyberswap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        IMetaAggregationRouterV2.SwapExecutionParams memory params = abi.decode(
            _data[4:],
            (IMetaAggregationRouterV2.SwapExecutionParams)
        );
        params.desc.amount = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function kyberswapSimple(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address caller,
            IMetaAggregationRouterV2.SwapDescriptionV2 memory desc,
            bytes memory executorData,
            bytes memory clientData
        ) = abi.decode(
                _data[4:],
                (
                    address,
                    IMetaAggregationRouterV2.SwapDescriptionV2,
                    bytes,
                    bytes
                )
            );
        desc.amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                caller,
                desc,
                executorData,
                clientData
            );
    }

    function oneInchGenericSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address executor,
            IOneInchGenericRouter.SwapDescription memory desc,
            bytes memory permit,
            bytes memory data
        ) = abi.decode(
                _data[4:],
                (address, IOneInchGenericRouter.SwapDescription, bytes, bytes)
            );
        desc.amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                executor,
                desc,
                permit,
                data
            );
    }

    function oneInchClipperSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address clipperExchange,
            address srcToken,
            address dstToken,
            uint256 inputAmount,
            uint256 outputAmount,
            uint256 goodUntil,
            bytes32 r,
            bytes32 vs
        ) = abi.decode(
                _data[4:],
                (
                    address,
                    address,
                    address,
                    uint256,
                    uint256,
                    uint256,
                    bytes32,
                    bytes32
                )
            );
        inputAmount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                clipperExchange,
                srcToken,
                dstToken,
                inputAmount,
                outputAmount,
                goodUntil,
                r,
                vs
            );
    }

    function oneInchClipperSwapTo(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address clipperExchange,
            address payable recipient,
            address srcToken,
            address dstToken,
            uint256 inputAmount,
            uint256 outputAmount,
            uint256 goodUntil,
            bytes32 r,
            bytes32 vs
        ) = abi.decode(
                _data[4:],
                (
                    address,
                    address,
                    address,
                    address,
                    uint256,
                    uint256,
                    uint256,
                    bytes32,
                    bytes32
                )
            );
        inputAmount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                clipperExchange,
                recipient,
                srcToken,
                dstToken,
                inputAmount,
                outputAmount,
                goodUntil,
                r,
                vs
            );
    }

    function oneInchClipperSwapToWithPermit(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        (
            address clipperExchange,
            address payable recipient,
            address srcToken,
            address dstToken,
            uint256 inputAmount,
            uint256 outputAmount,
            uint256 goodUntil,
            bytes32 r,
            bytes32 vs,
            bytes memory permit
        ) = abi.decode(
                _data[4:],
                (
                    address,
                    address,
                    address,
                    address,
                    uint256,
                    uint256,
                    uint256,
                    bytes32,
                    bytes32,
                    bytes
                )
            );
        inputAmount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                clipperExchange,
                recipient,
                srcToken,
                dstToken,
                inputAmount,
                outputAmount,
                goodUntil,
                r,
                vs,
                permit
            );
    }

    function oneInchUnoswapSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools
        ) = abi.decode(_data[4:], (address, uint256, uint256, uint256[]));
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                srcToken,
                amount,
                minReturn,
                pools
            );
    }

    function oneInchUnoswapSwapTo(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address payable recipient,
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools
        ) = abi.decode(
                _data[4:],
                (address, address, uint256, uint256, uint256[])
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                recipient,
                srcToken,
                amount,
                minReturn,
                pools
            );
    }

    function oneInchUnoswapSwapToWithPermit(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        (
            address payable recipient,
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools,
            bytes memory permit
        ) = abi.decode(
                _data[4:],
                (address, address, uint256, uint256, uint256[], bytes)
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                recipient,
                srcToken,
                amount,
                minReturn,
                pools,
                permit
            );
    }

    function oneInchUniswapV3Swap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (uint256 amount, uint256 minReturn, uint256[] memory pools) = abi
            .decode(_data[4:], (uint256, uint256, uint256[]));
        amount = _amount;
        return
            abi.encodeWithSelector(bytes4(_data[:4]), amount, minReturn, pools);
    }

    function oneInchUniswapV3SwapTo(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        (
            address payable recipient,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools
        ) = abi.decode(_data[4:], (address, uint256, uint256, uint256[]));
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                recipient,
                amount,
                minReturn,
                pools
            );
    }

    function oneInchUniswapV3SwapToWithPermit(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        (
            address payable recipient,
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools,
            bytes memory permit
        ) = abi.decode(
                _data[4:],
                (address, address, uint256, uint256, uint256[], bytes)
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                recipient,
                srcToken,
                amount,
                minReturn,
                pools,
                permit
            );
    }
}
