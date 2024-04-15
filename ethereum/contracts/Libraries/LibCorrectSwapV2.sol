// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import {ICorrectSwap} from "../Interfaces/ICorrectSwap.sol";
import {IUniswapV2Router01} from "../Interfaces/UniswapV2/IUniswapV2Router01.sol";
import {IUniswapV2Router01AVAX} from "../Interfaces/UniswapV2/IUniswapV2Router01AVAX.sol";
import {INetswapRouter01} from "../Interfaces/UniswapV2/INetswapRouter01.sol";
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
import {IMoeRouter} from "../Interfaces/MerchantMoe/IMoeRouter.sol";
import {IGMXV1Router} from "../Interfaces/GMX/IGMXV1Router.sol";
import {IPearlRouter} from "../Interfaces/Pearl/IPearlRouter.sol";
import {IiZiSwap} from "../Interfaces/Iziswap/IiZiSwap.sol";
import {ICamelotRouter} from "../Interfaces/Camelot/ICamelotRouter.sol";
import {IMetaAggregationRouterV2} from "../Interfaces/Kyberswap/IMetaAggregationRouterV2.sol";
import {IOneInchGenericRouter, IOneInchClipperRouter, IOneInchUnoswapRouter, IOneInchUnoswapV3Router} from "../Interfaces/OneInch/IAggregationRouterV5.sol";
import {IOpenOceanExchange, IOpenOceanCaller, IUniswapV2Exchange} from "../Interfaces/OpenOcean/IOpenOceanExchange.sol";
import {ILynexRouter} from "../Interfaces/Lynex/ILynexRouter.sol";

contract LibCorrectSwapV2 is ICorrectSwap {
    address public owner;
    mapping(bytes4 => address) private _correctSwap;

    constructor() {
        // set owner
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(tx.origin == owner, "Not Owner!");
        _;
    }

    //---------------------------------------------------------------------------
    // External Method

    // @dev Set correct swap
    function setCorrectSwap(
        bytes4[] memory _sigs,
        address _correctSwapAddr
    ) external onlyOwner {
        for (uint256 i = 0; i < _sigs.length; i++) {
            _correctSwap[_sigs[i]] = _correctSwapAddr;
        }
    }

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_correctSwap[sig] == address(0)) {
            revert("not support");
        } else {
            try
                ICorrectSwap(_correctSwap[sig]).correctSwap(_data, _amount)
            returns (bytes memory _result) {
                return _result;
            } catch Error(string memory _err) {
                revert(_err);
            } catch {
                revert("correctSwap fail");
            }
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_correctSwap[sig] == address(0)) {
            revert("not support");
        } else {
            try
                ICorrectSwap(_correctSwap[sig]).fixMinAmount(
                    _data,
                    _deltaMinAmount
                )
            returns (uint256 _amountOutMin, bytes memory _result) {
                return (_amountOutMin, _result);
            } catch Error(string memory _err) {
                revert(_err);
            } catch {
                revert("fixMinAmount fail");
            }
        }
    }
}

library LibSwapFuncSigs {
    // UniswapV2
    bytes4 internal constant _FUNC1 =
        IUniswapV2Router01.swapExactETHForTokens.selector;
    bytes4 internal constant _FUNC2 =
        IUniswapV2Router01AVAX.swapExactAVAXForTokens.selector;
    bytes4 internal constant _FUNC3 =
        IUniswapV2Router01.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC4 =
        IUniswapV2Router01AVAX.swapExactTokensForAVAX.selector;
    bytes4 internal constant _FUNC5 =
        IUniswapV2Router01.swapExactTokensForTokens.selector;

    // UniswapV3
    bytes4 internal constant _FUNC6 = ISwapRouter.exactInput.selector;

    // zksync,Syncswap
    bytes4 internal constant _FUNC7 = ISyncSwapRouter.swap.selector;

    // zksync,Muteswap
    bytes4 internal constant _FUNC8 =
        IMuteRouter.swapExactETHForTokens.selector;
    bytes4 internal constant _FUNC9 =
        IMuteRouter.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC10 =
        IMuteRouter.swapExactTokensForTokens.selector;

    // QuickswapV3
    bytes4 internal constant _FUNC11 = IQuickSwapRouter.exactInput.selector;

    // base,Aerodrome
    bytes4 internal constant _FUNC12 =
        IAerodrome.swapExactETHForTokens.selector;
    bytes4 internal constant _FUNC13 =
        IAerodrome.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC14 =
        IAerodrome.swapExactTokensForTokens.selector;

    // UniswapV3
    bytes4 internal constant _FUNC15 = ISwapRouter02.exactInput.selector;

    // BalancerV2
    bytes4 internal constant _FUNC16 = IVault.swap.selector;

    // Curve
    bytes4 internal constant _FUNC17 = ICurveFi.exchange.selector;
    bytes4 internal constant _FUNC18 = ICurveFi.exchange_underlying.selector;

    // bsc,Wombat
    bytes4 internal constant _FUNC19 =
        IWombatRouter.swapExactTokensForTokens.selector;
    bytes4 internal constant _FUNC20 =
        IWombatRouter.swapExactTokensForNative.selector;
    bytes4 internal constant _FUNC21 =
        IWombatRouter.swapExactNativeForTokens.selector;

    // Trader Joe
    bytes4 internal constant _FUNC22 =
        ILBRouter.swapExactTokensForTokens.selector;
    bytes4 internal constant _FUNC23 =
        ILBRouter.swapExactTokensForNATIVE.selector;
    bytes4 internal constant _FUNC24 =
        ILBRouter.swapExactNATIVEForTokens.selector;

    // GMX V1
    bytes4 internal constant _FUNC25 = IGMXV1Router.swap.selector;
    bytes4 internal constant _FUNC26 = IGMXV1Router.swapTokensToETH.selector;
    bytes4 internal constant _FUNC27 = IGMXV1Router.swapETHToTokens.selector;

    // PearlFi
    bytes4 internal constant _FUNC28 =
        IPearlRouter.swapExactTokensForTokens.selector;
    bytes4 internal constant _FUNC29 =
        IPearlRouter.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC30 =
        IPearlRouter.swapExactETHForTokens.selector;

    // iZiSwap
    bytes4 internal constant _FUNC31 = IiZiSwap.swapAmount.selector;

    // Camelot
    bytes4 internal constant _FUNC32 =
        ICamelotRouter
            .swapExactTokensForTokensSupportingFeeOnTransferTokens
            .selector;
    bytes4 internal constant _FUNC33 =
        ICamelotRouter
            .swapExactETHForTokensSupportingFeeOnTransferTokens
            .selector;
    bytes4 internal constant _FUNC34 =
        ICamelotRouter
            .swapExactTokensForETHSupportingFeeOnTransferTokens
            .selector;

    // Kyberswap
    bytes4 internal constant _FUNC35 =
        IMetaAggregationRouterV2.swapGeneric.selector;
    bytes4 internal constant _FUNC36 = IMetaAggregationRouterV2.swap.selector;
    bytes4 internal constant _FUNC37 =
        IMetaAggregationRouterV2.swapSimpleMode.selector;

    // 1inch
    bytes4 internal constant _FUNC38 = IOneInchGenericRouter.swap.selector;
    bytes4 internal constant _FUNC39 =
        IOneInchClipperRouter.clipperSwap.selector;
    bytes4 internal constant _FUNC40 =
        IOneInchClipperRouter.clipperSwapTo.selector;
    bytes4 internal constant _FUNC41 =
        IOneInchClipperRouter.clipperSwapToWithPermit.selector;
    bytes4 internal constant _FUNC42 = IOneInchUnoswapRouter.unoswap.selector;
    bytes4 internal constant _FUNC43 = IOneInchUnoswapRouter.unoswapTo.selector;
    bytes4 internal constant _FUNC44 =
        IOneInchUnoswapRouter.unoswapToWithPermit.selector;
    bytes4 internal constant _FUNC45 =
        IOneInchUnoswapV3Router.uniswapV3Swap.selector;
    bytes4 internal constant _FUNC46 =
        IOneInchUnoswapV3Router.uniswapV3SwapTo.selector;
    bytes4 internal constant _FUNC47 =
        IOneInchUnoswapV3Router.uniswapV3SwapToWithPermit.selector;

    // OpenOcean
    bytes4 internal constant _FUNC48 = IOpenOceanExchange.swap.selector;
    bytes4 internal constant _FUNC49 = IUniswapV2Exchange.callUniswap.selector;
    bytes4 internal constant _FUNC50 =
        IUniswapV2Exchange.callUniswapTo.selector;
    bytes4 internal constant _FUNC51 =
        IUniswapV2Exchange.callUniswapWithPermit.selector;
    bytes4 internal constant _FUNC52 =
        IUniswapV2Exchange.callUniswapToWithPermit.selector;

    // Netswap
    bytes4 internal constant _FUNC53 =
        INetswapRouter01.swapExactMetisForTokens.selector;
    bytes4 internal constant _FUNC54 =
        INetswapRouter01.swapExactTokensForMetis.selector;

    // MerchantMoe
    bytes4 internal constant _FUNC55 =
        IMoeRouter.swapExactNativeForTokens.selector;
    bytes4 internal constant _FUNC56 =
        IMoeRouter.swapExactTokensForNative.selector;

    // Lynex
    bytes4 internal constant _FUNC57 =
        ILynexRouter.swapExactETHForTokens.selector;
    bytes4 internal constant _FUNC58 =
        ILynexRouter.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC59 =
        ILynexRouter.swapExactTokensForTokens.selector;
}

contract CorrectUniswapV2Factory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // UniswapV2
        bytes4[] memory sigs = new bytes4[](9);
        sigs[0] = LibSwapFuncSigs._FUNC1;
        sigs[1] = LibSwapFuncSigs._FUNC2;
        sigs[2] = LibSwapFuncSigs._FUNC3;
        sigs[3] = LibSwapFuncSigs._FUNC4;
        sigs[4] = LibSwapFuncSigs._FUNC5;
        sigs[5] = LibSwapFuncSigs._FUNC53;
        sigs[6] = LibSwapFuncSigs._FUNC54;
        sigs[7] = LibSwapFuncSigs._FUNC55;
        sigs[8] = LibSwapFuncSigs._FUNC56;
        address correctUniswapV2 = address(new CorrectUniswapV2());
        libCorrectSwapV2.setCorrectSwap(sigs, correctUniswapV2);
    }
}

contract CorrectUniswapV2 is ICorrectSwap {
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
    bytes4 private constant _FUNC53 =
        INetswapRouter01.swapExactMetisForTokens.selector;
    bytes4 private constant _FUNC54 =
        INetswapRouter01.swapExactTokensForMetis.selector;
    bytes4 internal constant _FUNC55 =
        IMoeRouter.swapExactNativeForTokens.selector;
    bytes4 internal constant _FUNC56 =
        IMoeRouter.swapExactTokensForNative.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);

        if (
            sig == _FUNC1 || sig == _FUNC2 || sig == _FUNC53 || sig == _FUNC55
        ) {
            return _data;
        } else if (
            sig == _FUNC3 ||
            sig == _FUNC4 ||
            sig == _FUNC5 ||
            sig == _FUNC54 ||
            sig == _FUNC56
        ) {
            return basicCorrectSwap(_data, _amount);
        } else {
            revert("correctUniswapV2 error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (
            sig == _FUNC1 || sig == _FUNC2 || sig == _FUNC53 || sig == _FUNC55
        ) {
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
        } else if (
            sig == _FUNC3 ||
            sig == _FUNC4 ||
            sig == _FUNC5 ||
            sig == _FUNC54 ||
            sig == _FUNC56
        ) {
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
        }

        revert("fix uniswap v2 amount fail!");
    }

    function basicCorrectSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectUniswapV3Factory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // UniswapV3
        bytes4[] memory sigs = new bytes4[](2);
        sigs[0] = LibSwapFuncSigs._FUNC6;
        sigs[1] = LibSwapFuncSigs._FUNC15;
        address correctUniswapV3 = address(new CorrectUniswapV3());
        libCorrectSwapV2.setCorrectSwap(sigs, correctUniswapV3);
    }
}

contract CorrectUniswapV3 is ICorrectSwap {
    // UniswapV3
    bytes4 private constant _FUNC6 = ISwapRouter.exactInput.selector;
    bytes4 private constant _FUNC15 = ISwapRouter02.exactInput.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC6 == sig) {
            return exactInput(_data, _amount);
        } else if (_FUNC15 == sig) {
            return exactInputV2(_data, _amount);
        } else {
            revert("correctUniswapV3 error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC6) {
            ISwapRouter.ExactInputParams memory params = abi.decode(
                _data[4:],
                (ISwapRouter.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        } else if (sig == _FUNC15) {
            ISwapRouter02.ExactInputParams memory params = abi.decode(
                _data[4:],
                (ISwapRouter02.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        }

        revert("fix uniswap v3 amount fail!");
    }

    function exactInput(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        ISwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function exactInputV2(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        ISwapRouter02.ExactInputParams memory params = abi.decode(
            _data[4:],
            (ISwapRouter02.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }
}

contract CorrectSyncswapFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Syncswap
        bytes4[] memory sigs = new bytes4[](1);
        sigs[0] = LibSwapFuncSigs._FUNC7;
        address correctSyncswap = address(new CorrectSyncswap());
        libCorrectSwapV2.setCorrectSwap(sigs, correctSyncswap);
    }
}

contract CorrectSyncswap is ICorrectSwap {
    // zksync,Syncswap
    bytes4 private constant _FUNC7 = ISyncSwapRouter.swap.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC7 == sig) {
            return syncSwap(_data, _amount);
        } else {
            revert("correctSyncswap error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC7) {
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
        }

        revert("fix syncswap amount fail!");
    }

    function syncSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectMuteswapFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Muteswap
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC8;
        sigs[1] = LibSwapFuncSigs._FUNC9;
        sigs[2] = LibSwapFuncSigs._FUNC10;
        address correctMuteswap = address(new CorrectMuteswap());
        libCorrectSwapV2.setCorrectSwap(sigs, correctMuteswap);
    }
}

contract CorrectMuteswap is ICorrectSwap {
    // zksync,Muteswap
    bytes4 private constant _FUNC8 = IMuteRouter.swapExactETHForTokens.selector;
    bytes4 private constant _FUNC9 = IMuteRouter.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC10 =
        IMuteRouter.swapExactTokensForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC8 == sig) {
            return _data;
        } else if (_FUNC9 == sig || _FUNC10 == sig) {
            return muteSwap(_data, _amount);
        } else {
            revert("correctMuteswap error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC8) {
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
        }

        revert("fix muteswap amount fail!");
    }

    function muteSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectQuickswapV3Factory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // QuickswapV3
        bytes4[] memory sigs = new bytes4[](1);
        sigs[0] = LibSwapFuncSigs._FUNC11;
        address correctQuickswapV3 = address(new CorrectQuickswapV3());
        libCorrectSwapV2.setCorrectSwap(sigs, correctQuickswapV3);
    }
}

contract CorrectQuickswapV3 is ICorrectSwap {
    // QuickswapV3
    bytes4 private constant _FUNC11 = IQuickSwapRouter.exactInput.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC11 == sig) {
            return quickExactInput(_data, _amount);
        } else {
            revert("correctQuickswapV3 error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC11) {
            IQuickSwapRouter.ExactInputParams memory params = abi.decode(
                _data[4:],
                (IQuickSwapRouter.ExactInputParams)
            );
            uint256 _amountOutMin = params.amountOutMinimum;
            params.amountOutMinimum = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        }

        revert("fix quickswapv3 amount fail!");
    }

    function quickExactInput(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        IQuickSwapRouter.ExactInputParams memory params = abi.decode(
            _data[4:],
            (IQuickSwapRouter.ExactInputParams)
        );
        params.amountIn = _amount;

        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }
}

contract CorrectAerodromeFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Aerodrome
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC12;
        sigs[1] = LibSwapFuncSigs._FUNC13;
        sigs[2] = LibSwapFuncSigs._FUNC14;
        address correctAerodrome = address(new CorrectAerodrome());
        libCorrectSwapV2.setCorrectSwap(sigs, correctAerodrome);
    }
}

contract CorrectAerodrome is ICorrectSwap {
    // base, Aerodrome
    bytes4 private constant _FUNC12 = IAerodrome.swapExactETHForTokens.selector;
    bytes4 private constant _FUNC13 = IAerodrome.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC14 =
        IAerodrome.swapExactTokensForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC12 == sig) {
            return _data;
        } else if (_FUNC13 == sig || _FUNC14 == sig) {
            return aerodrome(_data, _amount);
        } else {
            revert("correctAerodrome error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC12) {
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
        }

        revert("fix Aerodrome amount fail!");
    }

    function aerodrome(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectBalancerV2Factory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // BalancerV2
        bytes4[] memory sigs = new bytes4[](1);
        sigs[0] = LibSwapFuncSigs._FUNC16;
        address correctBalancerV2 = address(new CorrectBalancerV2());
        libCorrectSwapV2.setCorrectSwap(sigs, correctBalancerV2);
    }
}

contract CorrectBalancerV2 is ICorrectSwap {
    // BalancerV2
    bytes4 private constant _FUNC16 = IVault.swap.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC16 == sig) {
            return balancerV2SingleSwap(_data, _amount);
        } else {
            revert("correctBalancerV2 error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC16) {
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
        }

        revert("fix Aerodrome amount fail!");
    }

    function balancerV2SingleSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectCurveFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Curve
        bytes4[] memory sigs = new bytes4[](2);
        sigs[0] = LibSwapFuncSigs._FUNC17;
        sigs[1] = LibSwapFuncSigs._FUNC18;
        address correctCurve = address(new CorrectCurve());
        libCorrectSwapV2.setCorrectSwap(sigs, correctCurve);
    }
}

contract CorrectCurve is ICorrectSwap {
    // Curve
    bytes4 private constant _FUNC17 = ICurveFi.exchange.selector;
    bytes4 private constant _FUNC18 = ICurveFi.exchange_underlying.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC17 == sig) {
            return curveExchange(_data, _amount);
        } else if (_FUNC18 == sig) {
            return curveExchangeUnderlying(_data, _amount);
        } else {
            revert("correctCurve error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC17) {
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
        }

        revert("fix Curve amount fail!");
    }

    function curveExchange(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }

    function curveExchangeUnderlying(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (int128 i, int128 j, uint256 dx, uint256 min_dy) = abi.decode(
            _data[4:],
            (int128, int128, uint256, uint256)
        );
        dx = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), i, j, dx, min_dy);
    }
}

contract CorrectWombatFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Wombat
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC19;
        sigs[1] = LibSwapFuncSigs._FUNC20;
        sigs[2] = LibSwapFuncSigs._FUNC21;
        address correctWombat = address(new CorrectWombat());
        libCorrectSwapV2.setCorrectSwap(sigs, correctWombat);
    }
}

contract CorrectWombat is ICorrectSwap {
    // bsc, Wombat
    bytes4 private constant _FUNC19 =
        IWombatRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC20 =
        IWombatRouter.swapExactTokensForNative.selector;
    bytes4 private constant _FUNC21 =
        IWombatRouter.swapExactNativeForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC21 == sig) {
            return _data;
        } else if (_FUNC19 == sig || _FUNC20 == sig) {
            return wombatSwap(_data, _amount);
        } else {
            revert("correctWombat error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC19 || sig == _FUNC20) {
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
        }

        revert("fix wombat amount fail!");
    }

    function wombatSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectTraderJoeFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Trader Joe
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC22;
        sigs[1] = LibSwapFuncSigs._FUNC23;
        sigs[2] = LibSwapFuncSigs._FUNC24;
        address correctTraderJoe = address(new CorrectTraderJoe());
        libCorrectSwapV2.setCorrectSwap(sigs, correctTraderJoe);
    }
}

contract CorrectTraderJoe is ICorrectSwap {
    // Trader Joe
    bytes4 private constant _FUNC22 =
        ILBRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC23 =
        ILBRouter.swapExactTokensForNATIVE.selector;
    bytes4 private constant _FUNC24 =
        ILBRouter.swapExactNATIVEForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC24 == sig) {
            return _data;
        } else if (_FUNC22 == sig || _FUNC23 == sig) {
            return traderJoeSwap(_data, _amount);
        } else {
            revert("correctTraderJoe error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC22 || sig == _FUNC23) {
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
        }

        revert("fix TradeJoe amount fail!");
    }

    function traderJoeSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectGMXV1Factory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // GMX V1
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC25;
        sigs[1] = LibSwapFuncSigs._FUNC26;
        sigs[2] = LibSwapFuncSigs._FUNC27;
        address correctGMXV1 = address(new CorrectGMXV1());
        libCorrectSwapV2.setCorrectSwap(sigs, correctGMXV1);
    }
}

contract CorrectGMXV1 is ICorrectSwap {
    // GMX V1
    bytes4 private constant _FUNC25 = IGMXV1Router.swap.selector;
    bytes4 private constant _FUNC26 = IGMXV1Router.swapTokensToETH.selector;
    bytes4 private constant _FUNC27 = IGMXV1Router.swapETHToTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC27 == sig) {
            return _data;
        } else if (_FUNC25 == sig || _FUNC26 == sig) {
            return GMXV1Swap(_data, _amount);
        } else {
            revert("correctGMXV1 error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC25 || sig == _FUNC26) {
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
        }

        revert("fix GMXV1 amount fail!");
    }

    function GMXV1Swap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectPearlFiFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // PearlFi
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC28;
        sigs[1] = LibSwapFuncSigs._FUNC29;
        sigs[2] = LibSwapFuncSigs._FUNC30;
        address correctPearlFi = address(new CorrectPearlFi());
        libCorrectSwapV2.setCorrectSwap(sigs, correctPearlFi);
    }
}

contract CorrectPearlFi is ICorrectSwap {
    // PearlFi
    bytes4 private constant _FUNC28 =
        IPearlRouter.swapExactTokensForTokens.selector;
    bytes4 private constant _FUNC29 =
        IPearlRouter.swapExactTokensForETH.selector;
    bytes4 private constant _FUNC30 =
        IPearlRouter.swapExactETHForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC30 == sig) {
            return _data;
        } else if (_FUNC28 == sig || _FUNC29 == sig) {
            return pearlFiSwap(_data, _amount);
        } else {
            revert("correctPearlFi error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC28 || sig == _FUNC29) {
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
        }

        revert("fix PearlFi amount fail!");
    }

    function pearlFiSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectIZiSwapFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // iZiSwap
        bytes4[] memory sigs = new bytes4[](1);
        sigs[0] = LibSwapFuncSigs._FUNC31;
        address correctiZiSwap = address(new CorrectIZiSwap());
        libCorrectSwapV2.setCorrectSwap(sigs, correctiZiSwap);
    }
}

contract CorrectIZiSwap is ICorrectSwap {
    // iZiSwap
    bytes4 private constant _FUNC31 = IiZiSwap.swapAmount.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC31 == sig) {
            return iZiSwap(_data, _amount);
        } else {
            revert("correctiZiSwap error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC31) {
            IiZiSwap.SwapAmountParams memory params = abi.decode(
                _data[4:],
                (IiZiSwap.SwapAmountParams)
            );
            uint256 _amountOutMin = params.minAcquired;
            params.minAcquired = _amountOutMin + _deltaMinAmount;
            return (_amountOutMin, abi.encodeWithSelector(sig, params));
        }

        revert("fix iZiSwap amount fail!");
    }

    function iZiSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        IiZiSwap.SwapAmountParams memory params = abi.decode(
            _data[4:],
            (IiZiSwap.SwapAmountParams)
        );
        require(_amount <= type(uint128).max, "Value too large for uint128");
        params.amount = uint128(_amount);
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }
}

contract CorrectCamelotFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Camelot
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC32;
        sigs[1] = LibSwapFuncSigs._FUNC33;
        sigs[2] = LibSwapFuncSigs._FUNC34;
        address correctCamelot = address(new CorrectCamelot());
        libCorrectSwapV2.setCorrectSwap(sigs, correctCamelot);
    }
}

contract CorrectCamelot is ICorrectSwap {
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

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC33 == sig) {
            return _data;
        } else if (_FUNC32 == sig || _FUNC34 == sig) {
            return camelot(_data, _amount);
        } else {
            revert("correctCamelot error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC33) {
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
        }

        revert("fix Camelot amount fail!");
    }

    function camelot(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
}

contract CorrectKyberswapFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Kyberswap
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC35;
        sigs[1] = LibSwapFuncSigs._FUNC36;
        sigs[2] = LibSwapFuncSigs._FUNC37;
        address correctKyberswap = address(new CorrectKyberswap());
        libCorrectSwapV2.setCorrectSwap(sigs, correctKyberswap);
    }
}

contract CorrectKyberswap is ICorrectSwap {
    // Camelot
    bytes4 private constant _FUNC35 =
        IMetaAggregationRouterV2.swapGeneric.selector;
    bytes4 private constant _FUNC36 = IMetaAggregationRouterV2.swap.selector;
    bytes4 private constant _FUNC37 =
        IMetaAggregationRouterV2.swapSimpleMode.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC35 == sig || _FUNC36 == sig) {
            return kyberswap(_data, _amount);
        } else if (_FUNC37 == sig) {
            return kyberswapSimple(_data, _amount);
        } else {
            revert("correctKyberswap error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC35 || sig == _FUNC36) {
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

        revert("fix KyberSwap amount fail!");
    }

    function kyberswap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        IMetaAggregationRouterV2.SwapExecutionParams memory params = abi.decode(
            _data[4:],
            (IMetaAggregationRouterV2.SwapExecutionParams)
        );
        params.desc.amount = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), params);
    }

    function kyberswapSimple(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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

contract CorrectOneInchFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // 1inch
        bytes4[] memory sigs = new bytes4[](10);
        sigs[0] = LibSwapFuncSigs._FUNC38;
        sigs[1] = LibSwapFuncSigs._FUNC39;
        sigs[2] = LibSwapFuncSigs._FUNC40;
        sigs[3] = LibSwapFuncSigs._FUNC41;
        sigs[4] = LibSwapFuncSigs._FUNC42;
        sigs[5] = LibSwapFuncSigs._FUNC43;
        sigs[6] = LibSwapFuncSigs._FUNC44;
        sigs[7] = LibSwapFuncSigs._FUNC45;
        sigs[8] = LibSwapFuncSigs._FUNC46;
        sigs[9] = LibSwapFuncSigs._FUNC47;
        address correctOneInch = address(new CorrectOneInch());
        libCorrectSwapV2.setCorrectSwap(sigs, correctOneInch);
    }
}

contract CorrectOneInch is ICorrectSwap {
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

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC38 == sig) {
            return oneInchGenericSwap(_data, _amount);
        } else if (_FUNC39 == sig) {
            return oneInchClipperSwap(_data, _amount);
        } else if (_FUNC40 == sig) {
            return oneInchClipperSwapTo(_data, _amount);
        } else if (_FUNC41 == sig) {
            return oneInchClipperSwapToWithPermit(_data, _amount);
        } else if (_FUNC42 == sig) {
            return oneInchUnoswapSwap(_data, _amount);
        } else if (_FUNC43 == sig) {
            return oneInchUnoswapSwapTo(_data, _amount);
        } else if (_FUNC44 == sig) {
            return oneInchUnoswapSwapToWithPermit(_data, _amount);
        } else if (_FUNC45 == sig) {
            return oneInchUniswapV3Swap(_data, _amount);
        } else if (_FUNC46 == sig) {
            return oneInchUniswapV3SwapTo(_data, _amount);
        } else if (_FUNC47 == sig) {
            return oneInchUniswapV3SwapToWithPermit(_data, _amount);
        } else {
            revert("correctOneInch error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external pure returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC38) {
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

        revert("fix 1inch amount fail!");
    }

    function oneInchGenericSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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

    function oneInchClipperSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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

    function oneInchClipperSwapTo(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
    ) internal pure returns (bytes memory) {
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

    function oneInchUnoswapSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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

    function oneInchUnoswapSwapTo(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
    ) internal pure returns (bytes memory) {
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

    function oneInchUniswapV3Swap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (uint256 amount, uint256 minReturn, uint256[] memory pools) = abi
            .decode(_data[4:], (uint256, uint256, uint256[]));
        amount = _amount;
        return
            abi.encodeWithSelector(bytes4(_data[:4]), amount, minReturn, pools);
    }

    function oneInchUniswapV3SwapTo(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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
    ) internal pure returns (bytes memory) {
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

contract CorrectOpenOceanFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // OpenOcean
        bytes4[] memory sigs = new bytes4[](5);
        sigs[0] = LibSwapFuncSigs._FUNC48;
        sigs[1] = LibSwapFuncSigs._FUNC49;
        sigs[2] = LibSwapFuncSigs._FUNC50;
        sigs[3] = LibSwapFuncSigs._FUNC51;
        sigs[4] = LibSwapFuncSigs._FUNC52;
        address correctOpenOcean = address(new CorrectOpenOcean());
        libCorrectSwapV2.setCorrectSwap(sigs, correctOpenOcean);
    }
}

contract CorrectOpenOcean is ICorrectSwap {
    // OpenOcean
    bytes4 internal constant _FUNC48 = IOpenOceanExchange.swap.selector;
    bytes4 internal constant _FUNC49 = IUniswapV2Exchange.callUniswap.selector;
    bytes4 internal constant _FUNC50 =
        IUniswapV2Exchange.callUniswapTo.selector;
    bytes4 internal constant _FUNC51 =
        IUniswapV2Exchange.callUniswapWithPermit.selector;
    bytes4 internal constant _FUNC52 =
        IUniswapV2Exchange.callUniswapToWithPermit.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC48 == sig) {
            return openOceanSwap(_data, _amount);
        } else if (_FUNC49 == sig) {
            return openOceanCallUniswap(_data, _amount);
        } else if (_FUNC50 == sig) {
            return openOceanCallUniswapTo(_data, _amount);
        } else if (_FUNC51 == sig) {
            return openOceanCallUniswapWithPermit(_data, _amount);
        } else if (_FUNC52 == sig) {
            return openOceanCallUniswapToWithPermit(_data, _amount);
        } else {
            revert("correctOpenOcean error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external pure returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (_FUNC48 == sig) {
            (
                IOpenOceanCaller caller,
                IOpenOceanExchange.SwapDescription memory desc,
                IOpenOceanCaller.CallDescription[] memory calls
            ) = abi.decode(
                    _data[4:],
                    (
                        IOpenOceanCaller,
                        IOpenOceanExchange.SwapDescription,
                        IOpenOceanCaller.CallDescription[]
                    )
                );
            uint256 _amountOutMin = desc.minReturnAmount;
            desc.minReturnAmount = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(sig, caller, desc, calls)
            );
        } else if (_FUNC49 == sig) {
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
        } else if (_FUNC50 == sig) {
            (
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools,
                address payable recipient
            ) = abi.decode(
                    _data[4:],
                    (address, uint256, uint256, uint256[], address)
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    srcToken,
                    amount,
                    minReturn,
                    pools,
                    recipient
                )
            );
        } else if (_FUNC51 == sig) {
            (
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools,
                bytes memory permit
            ) = abi.decode(
                    _data[4:],
                    (address, uint256, uint256, uint256[], bytes)
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    srcToken,
                    amount,
                    minReturn,
                    pools,
                    permit
                )
            );
        } else if (_FUNC52 == sig) {
            (
                address srcToken,
                uint256 amount,
                uint256 minReturn,
                uint256[] memory pools,
                bytes memory permit,
                address payable recipient
            ) = abi.decode(
                    _data[4:],
                    (address, uint256, uint256, uint256[], bytes, address)
                );
            uint256 _amountOutMin = minReturn;
            minReturn = _amountOutMin + _deltaMinAmount;
            return (
                _amountOutMin,
                abi.encodeWithSelector(
                    sig,
                    srcToken,
                    amount,
                    minReturn,
                    pools,
                    permit,
                    recipient
                )
            );
        }

        revert("fix openocean amount fail!");
    }

    function openOceanSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (
            IOpenOceanCaller caller,
            IOpenOceanExchange.SwapDescription memory desc,
            IOpenOceanCaller.CallDescription[] memory calls
        ) = abi.decode(
                _data[4:],
                (
                    IOpenOceanCaller,
                    IOpenOceanExchange.SwapDescription,
                    IOpenOceanCaller.CallDescription[]
                )
            );
        desc.amount = _amount;
        return abi.encodeWithSelector(bytes4(_data[:4]), caller, desc, calls);
    }

    function openOceanCallUniswap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
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

    function openOceanCallUniswapTo(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools,
            address payable recipient
        ) = abi.decode(
                _data[4:],
                (address, uint256, uint256, uint256[], address)
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                srcToken,
                amount,
                minReturn,
                pools,
                recipient
            );
    }

    function openOceanCallUniswapWithPermit(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools,
            bytes memory permit
        ) = abi.decode(
                _data[4:],
                (address, uint256, uint256, uint256[], bytes)
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                srcToken,
                amount,
                minReturn,
                pools,
                permit
            );
    }

    function openOceanCallUniswapToWithPermit(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (
            address srcToken,
            uint256 amount,
            uint256 minReturn,
            uint256[] memory pools,
            bytes memory permit,
            address payable recipient
        ) = abi.decode(
                _data[4:],
                (address, uint256, uint256, uint256[], bytes, address)
            );
        amount = _amount;
        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                srcToken,
                amount,
                minReturn,
                pools,
                permit,
                recipient
            );
    }
}

contract CorrectLynexFactory {
    constructor(LibCorrectSwapV2 libCorrectSwapV2) {
        // Lynex
        bytes4[] memory sigs = new bytes4[](3);
        sigs[0] = LibSwapFuncSigs._FUNC57;
        sigs[1] = LibSwapFuncSigs._FUNC58;
        sigs[2] = LibSwapFuncSigs._FUNC59;
        address correctLynex = address(new CorrectLynex());
        libCorrectSwapV2.setCorrectSwap(sigs, correctLynex);
    }
}

contract CorrectLynex is ICorrectSwap {
    // Lynex
    bytes4 internal constant _FUNC57 =
        ILynexRouter.swapExactETHForTokens.selector;
    bytes4 internal constant _FUNC58 =
        ILynexRouter.swapExactTokensForETH.selector;
    bytes4 internal constant _FUNC59 =
        ILynexRouter.swapExactTokensForTokens.selector;

    // @dev Correct input of destination chain swapData
    function correctSwap(
        bytes calldata _data,
        uint256 _amount
    ) external returns (bytes memory) {
        bytes4 sig = bytes4(_data[:4]);

        if (sig == _FUNC57) {
            return _data;
        } else if (sig == _FUNC58 || sig == _FUNC59) {
            return basicCorrectSwap(_data, _amount);
        } else {
            revert("correctLynex error");
        }
    }

    // @dev Fix min amount
    function fixMinAmount(
        bytes calldata _data,
        uint256 _deltaMinAmount
    ) external view returns (uint256, bytes memory) {
        bytes4 sig = bytes4(_data[:4]);
        if (sig == _FUNC57) {
            (
                uint256 _amountOutMin,
                ILynexRouter.route[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, ILynexRouter.route[], address, uint256)
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
        } else if (sig == _FUNC58 || sig == _FUNC59) {
            (
                uint256 _amount,
                uint256 _amountOutMin,
                ILynexRouter.route[] memory _path,
                address _to,
                uint256 _deadline
            ) = abi.decode(
                    _data[4:],
                    (uint256, uint256, ILynexRouter.route[], address, uint256)
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
        }

        revert("fix lynex swap amount fail!");
    }

    function basicCorrectSwap(
        bytes calldata _data,
        uint256 _amount
    ) internal pure returns (bytes memory) {
        (
            ,
            uint256 _amountOutMin,
            ILynexRouter.route[] memory _path,
            address _to,
            uint256 _deadline
        ) = abi.decode(
                _data[4:],
                (uint256, uint256, ILynexRouter.route[], address, uint256)
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
}
