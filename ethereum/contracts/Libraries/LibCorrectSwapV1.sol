// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import {IUniswapV2Router01} from "../Interfaces/IUniswapV2Router01.sol";
import {IUniswapV2Router01AVAX} from "../Interfaces/IUniswapV2Router01AVAX.sol";
import {ISwapRouter} from "../Interfaces/ISwapRouter.sol";
import {ISyncSwapRouter} from "../Interfaces/ISyncSwapRouter.sol";
import {IMuteRouter} from "../Interfaces/IMuteRouter.sol";
import {IQuickSwapRouter} from "../Interfaces/IQuickSwapRouter.sol";

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

    //---------------------------------------------------------------------------
    // External Method

    // @dev Correct input of destination chain swapData
    function correctSwap(bytes calldata _data, uint256 _amount)
        external
        view
        returns (bytes memory)
    {
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
        }

        // fuzzy matching
        return tryBasicCorrectSwap(_data, _amount);
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
        }

        revert("fix amount fail!");
    }

    function tryBasicCorrectSwap(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.basicCorrectSwap(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("basicCorrectSwap fail!");
        }
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

    function tryExactInput(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.exactInput(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("exactInput fail!");
        }
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

    function trySyncSwap(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.syncSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("syncSwap fail!");
        }
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

    function tryMuteSwap(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.muteSwap(_data, _amount) returns (bytes memory _result) {
            return _result;
        } catch {
            revert("muteSwap fail!");
        }
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

    function tryQuickExactInput(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.quickExactInput(_data, _amount) returns (
            bytes memory _result
        ) {
            return _result;
        } catch {
            revert("quickExactInput fail!");
        }
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
}
