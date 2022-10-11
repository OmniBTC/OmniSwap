// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.13;

import {ISo} from "../Interfaces/ISo.sol";
import {LibSwap} from "../Libraries/LibSwap.sol";
import {LibBytes} from "../Libraries/LibBytes.sol";

library LibCross {
    using LibBytes for bytes;

    function enNormalizedSoData(ISo.SoData memory soData)
        internal
        pure
        returns (ISo.NormalizedSoData memory)
    {
        ISo.NormalizedSoData memory data;
        data.transactionId = abi.encodePacked(soData.transactionId);
        data.receiver = abi.encodePacked(soData.receiver);
        data.sourceChainId = soData.sourceChainId;
        data.sendingAssetId = abi.encodePacked(soData.sendingAssetId);
        data.destinationChainId = soData.destinationChainId;
        data.receivingAssetId = abi.encodePacked(soData.receivingAssetId);
        data.amount = soData.amount;

        return data;
    }

    function deNormalizedSoData(ISo.NormalizedSoData memory data)
        internal
        pure
        returns (ISo.SoData memory)
    {
        return
            ISo.SoData({
                transactionId: data.transactionId.toBytes32(0),
                receiver: payable(data.receiver.toAddress(0)),
                sourceChainId: data.sourceChainId,
                sendingAssetId: data.sendingAssetId.toAddress(0),
                destinationChainId: data.destinationChainId,
                receivingAssetId: data.receivingAssetId.toAddress(0),
                amount: data.amount
            });
    }

    function enNormalizedSwapData(LibSwap.SwapData memory swapData)
        internal
        pure
        returns (LibSwap.NormalizedSwapData memory)
    {
        LibSwap.NormalizedSwapData memory data;
        data.callTo = abi.encodePacked(swapData.callTo);
        data.approveTo = abi.encodePacked(swapData.approveTo);
        data.sendingAssetId = abi.encodePacked(swapData.sendingAssetId);
        data.receivingAssetId = abi.encodePacked(swapData.receivingAssetId);
        data.fromAmount = swapData.fromAmount;
        data.callData = abi.encodePacked(swapData.callData);

        return data;
    }

    function deNormalizedSwapData(LibSwap.NormalizedSwapData memory data)
        internal
        pure
        returns (LibSwap.SwapData memory)
    {
        return
            LibSwap.SwapData({
                callTo: data.callTo.toAddress(0),
                approveTo: data.approveTo.toAddress(0),
                sendingAssetId: data.sendingAssetId.toAddress(0),
                receivingAssetId: data.receivingAssetId.toAddress(0),
                fromAmount: data.fromAmount,
                callData: data.callData
            });
    }

    function encodeNormalizedSoData(ISo.NormalizedSoData memory data)
        internal
        pure
        returns (bytes memory)
    {
        return
            abi.encodePacked(
                uint64(data.transactionId.length),
                data.transactionId,
                uint64(data.receiver.length),
                data.receiver,
                data.sourceChainId,
                uint64(data.sendingAssetId.length),
                data.sendingAssetId,
                data.destinationChainId,
                uint64(data.receivingAssetId.length),
                data.receivingAssetId,
                data.amount
            );
    }

    function decodeNormalizedSoData(bytes memory soData)
        internal
        pure
        returns (ISo.NormalizedSoData memory)
    {
        ISo.NormalizedSoData memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(soData.toUint64(index));
        index += 8;
        data.transactionId = soData.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(soData.toUint64(index));
        index += 8;
        data.receiver = soData.slice(index, nextLen);
        index += nextLen;

        nextLen = 2;
        data.sourceChainId = soData.toUint16(index);
        index += nextLen;

        nextLen = uint256(soData.toUint64(index));
        index += 8;
        data.sendingAssetId = soData.slice(index, nextLen);
        index += nextLen;

        nextLen = 2;
        data.destinationChainId = soData.toUint16(index);
        index += nextLen;

        nextLen = uint256(soData.toUint64(index));
        index += 8;
        data.receivingAssetId = soData.slice(index, nextLen);
        index += nextLen;

        nextLen = 32;
        data.amount = soData.toUint256(index);
        index += nextLen;

        require(index == soData.length, "Length error");

        return data;
    }

    function encodeNormalizedSwapData(LibSwap.NormalizedSwapData[] memory data)
        internal
        pure
        returns (bytes memory)
    {
        bytes memory encodeData = bytes("");

        if (data.length > 0) {
            encodeData = abi.encodePacked(uint64(data.length));
        }

        for (uint256 i = 0; i < data.length; i++) {
            encodeData = encodeData.concat(
                abi.encodePacked(
                    uint64(data[i].callTo.length),
                    data[i].callTo,
                    uint64(data[i].approveTo.length),
                    data[i].approveTo,
                    uint64(data[i].sendingAssetId.length),
                    data[i].sendingAssetId,
                    uint64(data[i].receivingAssetId.length),
                    data[i].receivingAssetId,
                    data[i].fromAmount,
                    uint64(data[i].callData.length),
                    data[i].callData
                )
            );
        }

        return encodeData;
    }

    function decodeNormalizedSwapData(bytes memory swapData)
        internal
        pure
        returns (LibSwap.NormalizedSwapData[] memory)
    {
        uint256 index;
        uint256 nextLen;

        nextLen = 8;
        uint256 swapLen = uint256(swapData.toUint64(index));
        index += nextLen;

        LibSwap.NormalizedSwapData[]
            memory data = new LibSwap.NormalizedSwapData[](swapLen);

        for (uint256 i = 0; i < swapLen; i++) {
            nextLen = uint256(swapData.toUint64(index));
            index += 8;
            data[i].callTo = swapData.slice(index, nextLen);
            index += nextLen;

            nextLen = uint256(swapData.toUint64(index));
            index += 8;
            data[i].approveTo = swapData.slice(index, nextLen);
            index += nextLen;

            nextLen = uint256(swapData.toUint64(index));
            index += 8;
            data[i].sendingAssetId = swapData.slice(index, nextLen);
            index += nextLen;

            nextLen = uint256(swapData.toUint64(index));
            index += 8;
            data[i].receivingAssetId = swapData.slice(index, nextLen);
            index += nextLen;

            nextLen = 32;
            data[i].fromAmount = swapData.toUint256(index);
            index += nextLen;

            nextLen = uint256(swapData.toUint64(index));
            index += 8;
            data[i].callData = swapData.slice(index, nextLen);
            index += nextLen;
        }

        require(index == swapData.length, "Length error");

        return data;
    }
}
