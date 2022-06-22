// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

contract LibCorrectUniswapV2 {
    //---------------------------------------------------------------------------
    // External Method

    // @dev Correct input of destination chain swapData
    function correctSwap(bytes calldata _data, uint256 _amount)
        external
        pure
        returns (bytes memory)
    {
        bytes4 sig = bytes4(_data[:4]);
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
                sig,
                _amount,
                _amountOutMin,
                _path,
                _to,
                _deadline
            );
    }
}
