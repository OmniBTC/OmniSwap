// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.13;

import {ISo} from "../Interfaces/ISo.sol";
import {LibSwap} from "../Libraries/LibSwap.sol";
import {LibBytes} from "../Libraries/LibBytes.sol";

library LibCross {
    using LibBytes for bytes;

    function encodeSoData(ISo.SoData memory soData)
        internal
        pure
        returns (bytes memory)
    {
        ISo.NormalizedSoData memory data;
        data.transactionId = abi.encodePacked(soData.transactionId);
        data.receiver = abi.encodePacked(soData.receiver);
        data.sourceChainId = soData.sourceChainId;
        data.sendingAssetId = abi.encodePacked(soData.sendingAssetId);
        data.destinationChainId = soData.destinationChainId;
        data.receivingAssetId = abi.encodePacked(soData.receivingAssetId);
        data.amount = soData.amount;

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

    function encodeSwapData(LibSwap.SwapData memory swapData)
        internal
        pure
        returns (bytes memory)
    {
        LibSwap.NormalizedSwapData memory data;
        data.callTo = abi.encodePacked(swapData.callTo);
        data.approveTo = abi.encodePacked(swapData.approveTo);
        data.sendingAssetId = abi.encodePacked(swapData.sendingAssetId);
        data.receivingAssetId = abi.encodePacked(swapData.receivingAssetId);
        data.fromAmount = swapData.fromAmount;
        data.callData = abi.encodePacked(swapData.callData);

        return
            abi.encodePacked(
                uint64(data.callTo.length),
                data.callTo,
                uint64(data.approveTo.length),
                data.approveTo,
                uint64(data.sendingAssetId.length),
                data.sendingAssetId,
                uint64(data.receivingAssetId.length),
                data.receivingAssetId,
                data.fromAmount,
                uint64(data.callData.length),
                data.callData
            );
    }

    function decodeSoData(bytes memory soData)
        internal
        pure
        returns (ISo.SoData memory)
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

    function decodeSwapData(bytes memory swapData)
        internal
        pure
        returns (LibSwap.SwapData memory)
    {
        LibSwap.NormalizedSwapData memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(swapData.toUint64(index));
        index += 8;
        data.callTo = swapData.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(swapData.toUint64(index));
        index += 8;
        data.approveTo = swapData.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(swapData.toUint64(index));
        index += 8;
        data.sendingAssetId = swapData.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(swapData.toUint64(index));
        index += 8;
        data.receivingAssetId = swapData.slice(index, nextLen);
        index += nextLen;

        nextLen = 32;
        data.fromAmount = swapData.toUint256(index);
        index += nextLen;

        nextLen = uint256(swapData.toUint64(index));
        index += 8;
        data.callData = swapData.slice(index, nextLen);
        index += nextLen;

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
}
