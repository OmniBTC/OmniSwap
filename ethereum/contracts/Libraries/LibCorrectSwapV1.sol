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

    //---------------------------------------------------------------------------
    // External Method

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external view returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC1) {
            return _data;
        } else if (sig == _FUNC2) {
            return _data;
        } else if (sig == _FUNC3) {
            return tryBasicCorrectSwap(_data, _amount);
        } else if (sig == _FUNC4) {
            return tryBasicCorrectSwap(_data, _amount);
        } else if (sig == _FUNC5) {
            return tryBasicCorrectSwap(_data, _amount);
        } else if (sig == _FUNC6) {
            return tryExactInput(_data, _amount);
        } else if (sig == _FUNC7) {
            return trySyncSwap(_data, _amount);
        } else if (sig == _FUNC8) {
            return _data;
        } else if (sig == _FUNC9) {
            return tryMuteSwap(_data, _amount);
        } else if (sig == _FUNC10) {
            return tryMuteSwap(_data, _amount);
        } else if (sig == _FUNC11) {
            return tryQuickExactInput(_data, _amount);
        } else if (sig == _FUNC12) {
            return _data;
        } else if (sig == _FUNC13) {
            return tryAerodrome(_data, _amount);
        } else if (sig == _FUNC14) {
            return tryAerodrome(_data, _amount);
        } else if (sig == _FUNC15) {
            return tryExactInputV2(_data, _amount);
        } else if (sig == _FUNC16) {
            return tryBalancerV2SingleSwap(_data, _amount);
        } else if (sig == _FUNC17) {
            return tryCurveExchange(_data, _amount);
        } else if (sig == _FUNC18) {
            return tryCurveExchangeUnderlying(_data, _amount);
        } else if (sig == _FUNC19) {
            return tryWombatSwap(_data, _amount);
        } else if (sig == _FUNC20) {
            return tryWombatSwap(_data, _amount);
        } else if (sig == _FUNC21) {
            return _data;
        } else if (sig == _FUNC22 || sig == _FUNC23) {
            return tryTraderJoeSwap(_data, _amount);
        } else if (sig == _FUNC24) {
            return _data;
        } else if (sig == _FUNC25 || sig == _FUNC26) {
            return tryGMXV1Swap(_data, _amount);
        } else if (sig == _FUNC27) {
            return _data;
        } else if (sig == _FUNC28 || sig == _FUNC29) {
            return tryPearlFiSwap(_data, _amount);
        } else if (sig == _FUNC30) {
            return _data;
        } else if (sig == _FUNC31) {
            return tryiZiSwap(_data, _amount);
        } else if (sig == _FUNC32) {
            return tryCamelot(_data, _amount);
        } else if (sig == _FUNC33) {
            return _data;
        } else if (sig == _FUNC34) {
            return tryCamelot(_data, _amount);
        } else if (sig == _FUNC35 || sig == _FUNC36) {
            return tryKyberswap(_data, _amount);
        } else if (sig == _FUNC37) {
            return tryKyberswapSimple(_data, _amount);
        }

        // fuzzy matching
        return tryBasicCorrectSwap(_data, _amount);
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
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
        }

        revert("fix amount fail!");
    }

    function tryBasicCorrectSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.basicCorrectSwap(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("basicCorrectSwap fail!");
        }
    }

    function basicCorrectSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryExactInput(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.exactInput(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("exactInput fail!");
        }
    }

    function exactInput(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        ISwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function trySyncSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.syncSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("syncSwap fail!");
        }
    }

    function syncSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryMuteSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.muteSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("muteSwap fail!");
        }
    }

    function muteSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryQuickExactInput(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.quickExactInput(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("quickExactInput fail!");
        }
    }

    function quickExactInput(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        IQuickSwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (IQuickSwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function tryAerodrome(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.aerodrome(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("aerodrome fail!");
        }
    }

    function aerodrome(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryExactInputV2(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.exactInputV2(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("exactInputV2 fail!");
        }
    }

    function exactInputV2(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        ISwapRouter02.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter02.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function tryBalancerV2SingleSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.balcnerV2SingleSwap(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("balcnerV2SingleSwap fail!");
        }
    }

    function balcnerV2SingleSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryCurveExchange(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.curveExchange(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("curveV2Exchange fail!");
        }
    }

    function curveExchange(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }

    function tryCurveExchangeUnderlying(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.curveExchangeUnderlying(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("curveV2ExchangeUnderlying fail!");
        }
    }

    function curveExchangeUnderlying(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }

    function tryWombatSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.wombatSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("wombat swap fail!");
        }
    }

    function wombatSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryTraderJoeSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.traderJoeSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("trader joe swap fail!");
        }
    }

    function traderJoeSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryGMXV1Swap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.GMXV1Swap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("GMX v1 swap fail!");
        }
    }

    function GMXV1Swap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryPearlFiSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.pearlFiSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("trader joe swap fail!");
        }
    }

    function pearlFiSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryiZiSwap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.iZiSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("trader iziswap fail!");
        }
    }

    function iZiSwap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        IiZiSwap.SwapAmountParams memory params = abi.decode(
            _data[4:],
            (IiZiSwap.SwapAmountParams)
        );
        require(_amount <= type(uint128).max, "Value too large for uint128");
        params.amount = uint128(_amount);
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function tryCamelot(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.camelot(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("camelot fail!");
        }
    }

    function camelot(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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

    function tryKyberswap(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.kyberswap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("kyberswap fail!");
        }
    }

    function kyberswap(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
        IMetaAggregationRouterV2.SwapExecutionParams memory params = abi.decode(
            _data[4:],
            (IMetaAggregationRouterV2.SwapExecutionParams)
        );
        params.desc.amount = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function tryKyberswapSimple(
        bytes calldata _data,
        uint256 _amount
    ) public view returns (bytes memory) {
        try this.kyberswapSimple(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("kyberswap simple fail!");
        }
    }

    function kyberswapSimple(
        bytes calldata _data,
        uint256 _amount
    ) external pure returns (bytes memory) {
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
}
