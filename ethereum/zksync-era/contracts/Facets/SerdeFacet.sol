// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Libraries/LibCross.sol";
import "../Libraries/LibBytes.sol";
import "../Interfaces/ISo.sol";
import "../Libraries/LibSwap.sol";

/// @title Serde Facet
/// @author OmniBTC
/// @notice Provides functionality for encode and decode cross data
contract SerdeFacet {
    using LibBytes for bytes;

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

    function normalizeSoData(ISo.SoData memory soData)
        external
        pure
        returns (ISo.NormalizedSoData memory)
    {
        return LibCross.normalizeSoData(soData);
    }

    function denormalizeSoData(ISo.NormalizedSoData memory data)
        external
        pure
        returns (ISo.SoData memory)
    {
        return LibCross.denormalizeSoData(data);
    }

    function normalizeSwapData(LibSwap.SwapData[] memory swapData)
        external
        pure
        returns (LibSwap.NormalizedSwapData[] memory)
    {
        return LibCross.normalizeSwapData(swapData);
    }

    function denormalizeSwapData(LibSwap.NormalizedSwapData[] memory data)
        external
        pure
        returns (LibSwap.SwapData[] memory)
    {
        return LibCross.denormalizeSwapData(data);
    }

    function normalizeU256(uint256 data) external pure returns (bytes memory) {
        return abi.encodePacked(data);
    }

    function denormalizeU256(bytes memory data)
        external
        pure
        returns (uint256)
    {
        return data.toUint256(0);
    }
}
