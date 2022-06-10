// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import { ISo } from "../Interfaces/ISo.sol";
import { LibSwap } from "../Libraries/LibSwap.sol";
import { LibAsset } from "../Libraries/LibAsset.sol";
import { LibStorage } from "../Libraries/LibStorage.sol";
import { LibAsset } from "../Libraries/LibAsset.sol";
import { InvalidAmount, ContractCallNotAllowed, NoSwapDataProvided } from "../Errors/GenericErrors.sol";

/// @title Swapper
/// @author LI.FI (https://li.fi)
/// @notice Abstract contract to provide swap functionality
contract Swapper is ISo {
    /// Storage ///

    LibStorage internal appStorage;

    /// Modifiers ///

    /// @dev Sends any leftover balances back to the user
    modifier noLeftovers(LibSwap.SwapData[] calldata _swapData) {
        uint256 nSwaps = _swapData.length;
        if (nSwaps != 1) {
            uint256[] memory initialBalances = _fetchBalances(_swapData);
            address finalAsset = _swapData[nSwaps - 1].receivingAssetId;
            uint256 curBalance = 0;

            _;

            for (uint256 i = 0; i < nSwaps - 1; i++) {
                address curAsset = _swapData[i].receivingAssetId;
                if (curAsset == finalAsset) continue; // Handle multi-to-one swaps
                curBalance = LibAsset.getOwnBalance(curAsset) - initialBalances[i];
                if (curBalance > 0) LibAsset.transferAsset(curAsset, payable(msg.sender), curBalance);
            }
        } else _;
    }

    /// External Methods ///

    /// @dev Validates input before executing swaps
    /// @param _soData So tracking data
    /// @param _swapData Array of data used to execute swaps
    function executeAndCheckSwaps(SoData memory _soData, LibSwap.SwapData[] calldata _swapData)
        external
        returns (uint256)
    {
        uint256 nSwaps = _swapData.length;
        if (nSwaps == 0) revert NoSwapDataProvided();
        address finalTokenId = _swapData[_swapData.length - 1].receivingAssetId;
        uint256 swapBalance = LibAsset.getOwnBalance(finalTokenId);
        _executeSwaps(_soData, _swapData);
        swapBalance = LibAsset.getOwnBalance(finalTokenId) - swapBalance;
        if (swapBalance == 0) revert InvalidAmount();
        return swapBalance;
    }

    /// Private Methods ///

    /// @dev Executes swaps and checks that DEXs used are in the allowList
    /// @param _soData So tracking data
    /// @param _swapData Array of data used to execute swaps
    function _executeSwaps(SoData memory _soData, LibSwap.SwapData[] calldata _swapData)
        private
        noLeftovers(_swapData)
    {
        for (uint256 i = 0; i < _swapData.length; i++) {
            LibSwap.SwapData calldata currentSwapData = _swapData[i];
            if (
                !(appStorage.dexAllowlist[currentSwapData.approveTo] &&
                    appStorage.dexAllowlist[currentSwapData.callTo] &&
                    appStorage.dexFuncSignatureAllowList[bytes32(currentSwapData.callData[:8])])
            ) revert ContractCallNotAllowed();
            LibSwap.swap(_soData.transactionId, currentSwapData);
        }
    }

    /// @dev Fetches balances of tokens to be swapped before swapping.
    /// @param _swapData Array of data used to execute swaps
    /// @return uint256[] Array of token balances.
    function _fetchBalances(LibSwap.SwapData[] calldata _swapData) private view returns (uint256[] memory) {
        uint256 length = _swapData.length;
        uint256[] memory balances = new uint256[](length);
        for (uint256 i = 0; i < length; i++) balances[i] = LibAsset.getOwnBalance(_swapData[i].receivingAssetId);
        return balances;
    }
}
