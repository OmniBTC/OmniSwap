pragma solidity 0.8.13;

import {LibSwap} from "../Libraries/LibSwap.sol";
import {ISo} from "../Interfaces/ISo.sol";
import "../Libraries/LibCross.sol";

contract StargateHelper {
    using LibBytes for bytes;

    struct CachePayload {
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    function tryFindStargatePayload(bytes memory inputData, address soDiamond)
        external
        view
        returns (uint256, bytes memory)
    {
        if (inputData.length < 41) {
            return (0, bytes(""));
        }
        for (uint256 i; i < inputData.length - 41; ++i) {
            if (soDiamond == inputData.toAddress(i)) {
                if (inputData.toUint8(i + 40) == 32) {
                    try
                        this.findStargatePayload(
                            inputData.slice(i + 40, inputData.length - i - 40)
                        )
                    returns (uint256 index, bytes memory stargatePayload) {
                        return (index, stargatePayload);
                    } catch {}
                }
            }
        }
        return (0, bytes(""));
    }

    /// CrossData
    // 1. length + transactionId(SoData)
    // 2. length + receiver(SoData)
    // 3. length + receivingAssetId(SoData)
    // 4. length + swapDataLength(u8)
    // 5. length + callTo(SwapData)
    // 6. length + sendingAssetId(SwapData)
    // 7. length + receivingAssetId(SwapData)
    // 8. length + callData(SwapData)
    function findStargatePayload(bytes memory stargatePayload)
        external
        view
        returns (uint256, bytes memory)
    {
        CachePayload memory data;
        uint256 index;
        uint256 nextLen;

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.transactionId = stargatePayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.receiver = stargatePayload.slice(index, nextLen);
        index += nextLen;

        nextLen = uint256(stargatePayload.toUint8(index));
        index += 1;
        data.soData.receivingAssetId = stargatePayload.slice(index, nextLen);
        index += nextLen;

        if (index < stargatePayload.length) {
            nextLen = uint256(stargatePayload.toUint8(index));
            index += 1;
            uint256 swap_len = LibCross.deserializeU256WithHexStr(
                stargatePayload.slice(index, nextLen)
            );
            index += nextLen;

            data.swapDataDst = new LibSwap.NormalizedSwapData[](swap_len);
            for (uint256 i = 0; i < swap_len; i++) {
                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].callTo = stargatePayload.slice(
                    index,
                    nextLen
                );
                data.swapDataDst[i].approveTo = data.swapDataDst[i].callTo;
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].sendingAssetId = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint8(index));
                index += 1;
                data.swapDataDst[i].receivingAssetId = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;

                nextLen = uint256(stargatePayload.toUint16(index));
                index += 2;
                data.swapDataDst[i].callData = stargatePayload.slice(
                    index,
                    nextLen
                );
                index += nextLen;
            }
        }
        return (index, stargatePayload.slice(0, index));
    }
}
