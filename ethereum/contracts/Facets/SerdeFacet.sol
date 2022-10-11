// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Libraries/LibCross.sol";
import "../Interfaces/ISo.sol";
import "../Libraries/LibSwap.sol";


/// @title Serde Facet
/// @notice Provides functionality for encode and decode cross data
contract SerdeFacet{

    function encodeNormalizedSoData(ISo.NormalizedSoData memory data)
        external
        pure
        returns (bytes memory)
    {
        return LibCross.encodeNormalizedSoData(data);
    }

    function decodeNormalizedSoData(bytes memory soData)
        external
        pure
        returns (ISo.NormalizedSoData memory)
    {
        return LibCross.decodeNormalizedSoData(soData);
    }

    function encodeNormalizedSwapData(LibSwap.NormalizedSwapData[] memory data)
        external
        pure
        returns (bytes memory)
    {
        return LibCross.encodeNormalizedSwapData(data);
    }

    function decodeNormalizedSwapData(bytes memory swapData)
        external
        pure
        returns (LibSwap.NormalizedSwapData[] memory)
    {
        return LibCross.decodeNormalizedSwapData(swapData);
    }
}