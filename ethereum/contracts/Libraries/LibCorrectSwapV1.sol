// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

import {ISwapRouter} from "../Interfaces/ISwapRouter.sol";
import {ISyncSwapRouter} from "../Interfaces/ISyncSwapRouter.sol";
import {IMuteRouter} from "../Interfaces/IMuteRouter.sol";

contract LibCorrectSwapV1 {
    // Exact search for supported function signatures
    bytes4 private constant _FUNC1 =
        bytes4(
            keccak256(
                "swapExactETHForTokens(uint256,address[],address,uint256)"
            )
        );
    bytes4 private constant _FUNC2 =
        bytes4(
            keccak256(
                "swapExactAVAXForTokens(uint256,address[],address,uint256)"
                "swapExactAVAXForTokens(uint256,address[],address,uint256)"
            )
        );
    bytes4 private constant _FUNC3 =
        bytes4(
            keccak256(
                "swapExactTokensForETH(uint256,uint256,address[],address,uint256)"
            )
        );
    bytes4 private constant _FUNC4 =
        bytes4(
            keccak256(
                "swapExactTokensForAVAX(uint256,uint256,address[],address,uint256)"
            )
        );
    bytes4 private constant _FUNC5 =
        bytes4(
            keccak256(
                "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)"
            )
        );
    bytes4 private constant _FUNC6 = ISwapRouter.exactInput.selector;

    bytes4 private constant _FUNC7 = ISyncSwapRouter.swap.selector;

    bytes4 private constant _FUNC8 = IMuteRouter.swapExactETHForTokens.selector;

    bytes4 private constant _FUNC9 = IMuteRouter.swapExactTokensForETH.selector;

    bytes4 private constant _FUNC10 =
        IMuteRouter.swapExactTokensForTokens.selector;

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
        }

        // fuzzy matching
        return tryBasicCorrectSwap(_data, _amount);
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
            ISyncSwapRouter.SwapPath[] memory paths,
            uint256 amountOutMin,
            uint256 deadline
        ) = abi.decode(
                _data[4:],
                (ISyncSwapRouter.SwapPath[], uint256, uint256)
            );

        uint256 fromAmountSum;
        for (uint256 i = 0; i < paths.length; i++) {
            fromAmountSum = fromAmountSum + paths[i].amountIn;
        }

        for (uint256 i = 0; i < paths.length; i++) {
            paths[i].amountIn =
                (_amount * paths[i].amountIn) /
                fromAmountSum;
        }

        return
            abi.encodeWithSelector(
                bytes4(_data[:4]),
                paths,
                amountOutMin,
                deadline
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
}
