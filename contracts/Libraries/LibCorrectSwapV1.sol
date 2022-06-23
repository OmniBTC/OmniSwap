// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

contract LibCorrectSwapV1 {
    // Exact search for supported function signatures
    bytes4 private constant _FUNC1 = bytes4(keccak256('swapExactETHForTokens(uint,address[],address,uint)'));
    bytes4 private constant _FUNC2 = bytes4(keccak256('swapExactAVAXForTokens(uint,address[],address,uint)'));
    bytes4 private constant _FUNC3 = bytes4(keccak256('swapExactTokensForETH(uint,uint,address[],address,uint)'));
    bytes4 private constant _FUNC4 = bytes4(keccak256('swapExactTokensForAVAX(uint,uint,address[],address,uint)'));

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
        }
        // fuzzy matching
        return tryBasicCorrectSwap(_data, _amount);
    }

    function tryBasicCorrectSwap(bytes calldata _data, uint256 _amount)
        public
        view
        returns (bytes memory)
    {
        try this.basicCorrectSwap(_data, _amount) returns (bytes memory _result){
            return _result;
        }catch{
            revert("Correctswap fail!");
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
        ) = abi.decode(_data[4 :], (uint256, uint256, address[], address, uint256));

        return abi.encodeWithSelector(
            bytes4(_data[:4]),
            _amount,
            _amountOutMin,
            _path,
            _to,
            _deadline
        );
    }
}
