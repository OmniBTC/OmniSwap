// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ISo} from "../Interfaces/ISo.sol";
import {ICorrectSwap} from "../Interfaces/ICorrectSwap.sol";
import {ILibSoFeeV2} from "../Interfaces/ILibSoFeeV2.sol";
import {LibSwap} from "../Libraries/LibSwap.sol";
import {LibAsset} from "../Libraries/LibAsset.sol";
import {LibCross} from "../Libraries/LibCross.sol";
import {LibBytes} from "../Libraries/LibBytes.sol";
import {LibDiamond} from "../Libraries/LibDiamond.sol";
import {Swapper} from "../Helpers/Swapper.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";
import {InvalidConfig} from "../Errors/GenericErrors.sol";

import {IBoolSwapConsumer} from "../Interfaces/Bool/IBoolSwapConsumer.sol";
import {IBoolSwapPool} from "../Interfaces/Bool/IBoolSwapPool.sol";
import {IBoolSwapFactory} from "../Interfaces/Bool/IBoolSwapFactory.sol";
import {IBoolSwapRouter} from "../Interfaces/Bool/IBoolSwapRouter.sol";
import {BoolSwapPathConverter} from "../Helpers/BoolSwapPathConverter.sol";
import {IWETH} from "../Interfaces/IWETH.sol";

/**
 * @title Bool Faucet
 * @author OmniBTC
 * @notice Provides functionality for bridging through Bool Network
 */
contract BoolFacet is
    Swapper,
    ReentrancyGuard,
    BoolSwapPathConverter,
    IBoolSwapConsumer
{
    using LibBytes for bytes;
    using SafeMath for uint256;

    /// Storage ///
    bytes32 internal constant NAMESPACE =
        hex"c4e242f9d0a8f67e3c471e3eb6b3b98c42240aeaaa189f231d6f69834e05da63"; // keccak256("com.so.facets.bool")

    address internal constant NATIVE_ADDRESS_IN_BS =
        0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE;

    struct Storage {
        address boolSwapRouter;
        address boolSwapFactory;
        uint32 srcBoolSwapChainId;
        mapping(address => bool) allowedList;
    }

    // NOTE that chainId defined in BOOL is in uint32
    struct BoolSwapData {
        uint32 srcBoolSwapPoolId; // The bool swap pool id of the source chain
        uint32 dstBoolSwapChainId; // The bool network defined chain id of the destination chain
        bytes32 dstSoDiamond; // destination SoDiamond address (should be Bool swap compatible)
    }

    struct CachePayload {
        ISo.NormalizedSoData soData;
        LibSwap.NormalizedSwapData[] swapDataDst;
    }

    /** Events */
    event BoolSwapInitialized(
        address boolSwapRouter,
        address boolSwapFactory,
        uint32 chainId
    );
    event SetAllowedList(address boolSwapPool, bool isAllowed);

    /** Permission Required Functions */
    function initBoolSwap(address router, uint32 chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (router == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        address factory = IBoolSwapRouter(router).factory();
        s.boolSwapRouter = router;
        s.boolSwapFactory = factory;
        s.srcBoolSwapChainId = chainId;
        s.allowedList[msg.sender] = true;
        emit BoolSwapInitialized(router, factory, chainId);
    }

    function batchSetBoolAllowedAddresses(
        address[] calldata boolSwapPools,
        bool[] calldata isAllowed
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        for (uint256 i; i < boolSwapPools.length; ++i) {
            s.allowedList[boolSwapPools[i]] = isAllowed[i];
            emit SetAllowedList(boolSwapPools[i], isAllowed[i]);
        }
    }

    function updatePathPair(
        uint32[] calldata consumerChainIds,
        uint32[] calldata boolChainIds
    ) external override {
        LibDiamond.enforceIsContractOwner();
        this.updatePathPair(consumerChainIds, boolChainIds);
    }

    /** External Methods */
    function soSwapViaBool(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        BoolSwapData calldata boolSwapData,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) external payable nonReentrant {
        uint256 bridgeAmount;
        // Denormalize source chain data
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }

        bool isThroughNativePool;

        if (swapDataSrc.length == 0) {
            // Check the balance of the native token
            isThroughNativePool = _transferWrappedAssetAdjusted(
                soData.sendingAssetId,
                _getBoolSwapTokenByPoolId(boolSwapData.srcBoolSwapPoolId),
                soData.amount
            );
            bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            isThroughNativePool = _transferWrappedAssetAdjusted(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                _getBoolSwapTokenByPoolId(boolSwapData.srcBoolSwapPoolId),
                bridgeAmount
            );
        }

        bytes memory payload = encodeBoolSwapPayload(soDataNo, swapDataDstNo);

        Storage storage s = getStorage();

        uint256 boolFee = IBoolSwapRouter(s.boolSwapRouter).estimateBNFee(
            boolSwapData.srcBoolSwapPoolId,
            boolSwapData.dstBoolSwapChainId,
            bridgeAmount,
            boolSwapData.dstSoDiamond,
            payload
        );

        uint256 boolSwapValue = isThroughNativePool
            ? boolFee + bridgeAmount
            : boolFee;

        uint256 soBasicFee = getBoolBasicFee();
        address soBasicBeneficiary = getBoolBasicBeneficiary();
        if (soBasicBeneficiary != address(0x0) && soBasicFee > 0) {
            require(msg.value >= boolSwapValue + soBasicFee, "NotEnoughValue");
            LibAsset.transferAsset(
                address(0x0),
                payable(soBasicBeneficiary),
                soBasicFee
            );
        } else {
            require(msg.value >= boolSwapValue, "NotEnoughValue");
        }

        _startBridge(boolSwapData, boolSwapValue, bridgeAmount, payload);

        emit SoTransferStarted(soData.transactionId);
    }

    function receiveFromBoolSwap(
        uint32,
        address bridgeToken,
        uint256 bridgeAmount,
        bytes calldata payload
    ) external payable override {
        Storage storage s = getStorage();
        require(s.allowedList[msg.sender], "No permission");

        address token = bridgeToken == NATIVE_ADDRESS_IN_BS
            ? _convertNativeAddressFromBS()
            : bridgeToken;

        require(LibAsset.getOwnBalance(token) >= bridgeAmount, "AmountErr");

        (
            ISo.NormalizedSoData memory _soDataNo,
            LibSwap.NormalizedSwapData[] memory _swapDataDstNo
        ) = decodeBoolSwapPayload(payload);

        ISo.SoData memory soData = LibCross.denormalizeSoData(_soDataNo);

        LibSwap.SwapData[] memory swapDataDst = LibCross.denormalizeSwapData(
            _swapDataDstNo
        );

        uint256 amount = bridgeAmount;
        try
            this.remoteBoolSoSwap(token, amount, soData, swapDataDst)
        {} catch Error(string memory revertReason) {
            transferUnwrappedAsset(token, token, amount, soData.receiver);
            emit SoTransferFailed(
                soData.transactionId,
                revertReason,
                bytes("")
            );
        } catch (bytes memory returnData) {
            transferUnwrappedAsset(token, token, amount, soData.receiver);
            emit SoTransferFailed(soData.transactionId, "", returnData);
        }
    }

    /// @dev For internal calls only, do not add it to DiamondCut,
    ///      convenient for sgReceive to catch exceptions
    function remoteBoolSoSwap(
        address token,
        uint256 amount,
        ISo.SoData calldata soData,
        LibSwap.SwapData[] memory swapDataDst
    ) external {
        require(msg.sender == address(this), "NotDiamond");
        uint256 soFee = getBoolSoFee(amount);
        if (soFee < amount) {
            amount = amount.sub(soFee);
        }

        if (swapDataDst.length == 0) {
            if (soFee > 0) {
                transferUnwrappedAsset(
                    token,
                    soData.receivingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            transferUnwrappedAsset(
                token,
                soData.receivingAssetId,
                amount,
                soData.receiver
            );
            emit SoTransferCompleted(soData.transactionId, amount);
        } else {
            if (soFee > 0) {
                transferUnwrappedAsset(
                    token,
                    swapDataDst[0].sendingAssetId,
                    soFee,
                    LibDiamond.contractOwner()
                );
            }
            transferUnwrappedAsset(
                token,
                swapDataDst[0].sendingAssetId,
                amount,
                address(this)
            );

            swapDataDst[0].fromAmount = amount;

            address correctSwap = appStorage.correctSwapRouterSelectors;

            if (correctSwap != address(0)) {
                swapDataDst[0].callData = ICorrectSwap(correctSwap).correctSwap(
                    swapDataDst[0].callData,
                    swapDataDst[0].fromAmount
                );
            }

            uint256 amountFinal = this.executeAndCheckSwaps(
                soData,
                swapDataDst
            );
            // may swap to weth
            transferUnwrappedAsset(
                swapDataDst[swapDataDst.length - 1].receivingAssetId,
                soData.receivingAssetId,
                amountFinal,
                soData.receiver
            );
            emit SoTransferCompleted(soData.transactionId, amountFinal);
        }
    }

    /** Private/Internal Functions */
    function _startBridge(
        BoolSwapData calldata boolSwapData,
        uint256 boolSwapValue,
        uint256 bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();
        address router = s.boolSwapRouter;

        // DO BoolSwap stuff
        // Check if the destination chain has been supported by a specific Anchor (if necessary)

        // Give BoolSwap approval if necessary
        address boolSwapToken = _getBoolSwapTokenByPoolId(
            boolSwapData.srcBoolSwapPoolId
        );
        if (boolSwapToken != NATIVE_ADDRESS_IN_BS) {
            LibAsset.maxApproveERC20(
                IERC20(boolSwapToken),
                router,
                bridgeAmount
            );
        }

        // Convert the data type of SoDiamond on the destination chain from address to bytes32

        // crossId: unique cross-chain id from BOOL Network: crossId = uint32 srcChainId + uint32 dstChainId + uint192 nonce
        bytes32 crossId = IBoolSwapRouter(router).swap{value: boolSwapValue}(
            boolSwapData.srcBoolSwapPoolId,
            boolSwapData.dstBoolSwapChainId,
            bridgeAmount,
            boolSwapData.dstSoDiamond,
            payable(msg.sender),
            payload
        );
    }

    function _getBoolSwapPoolByPoolId(
        uint32 poolId
    ) private view returns (address) {
        Storage storage s = getStorage();
        address factory = s.boolSwapFactory;
        return IBoolSwapFactory(factory).fetchPool(poolId);
    }

    function _getBoolSwapTokenByPoolId(
        uint32 poolId
    ) private view returns (address) {
        return IBoolSwapPool(_getBoolSwapPoolByPoolId(poolId)).token();
    }

    function _convertNativeAddressFromOB() private pure returns (address) {
        return NATIVE_ADDRESS_IN_BS;
    }

    function _convertNativeAddressFromBS() private pure returns (address) {
        return address(0);
    }

    function _transferWrappedAssetAdjusted(
        address currentAssetId,
        address expectAssetId,
        uint256 amount
    ) internal returns (bool) {
        if (currentAssetId == expectAssetId) {
            require(
                LibAsset.getOwnBalance(currentAssetId) >= amount,
                "NotEnough"
            );
            return false;
        } else if (!LibAsset.isNativeAsset(currentAssetId)) {
            try IWETH(currentAssetId).withdraw(amount) {} catch {
                revert("WithdrawErr");
            }
            require(expectAssetId == NATIVE_ADDRESS_IN_BS, "WrongConfig");
            return true;
        } else {
            try IWETH(expectAssetId).deposit{value: amount}() {} catch {
                revert("DepositErr");
            }
            return false;
        }
    }

    /** View/Pure Functions */
    function encodeBoolSwapPayload(
        ISo.NormalizedSoData memory soData,
        LibSwap.NormalizedSwapData[] memory swapDataDst
    ) public pure returns (bytes memory) {
        bytes memory encodeData = abi.encodePacked(
            uint8(soData.transactionId.length),
            soData.transactionId,
            uint8(soData.receiver.length),
            soData.receiver,
            uint8(soData.receivingAssetId.length),
            soData.receivingAssetId
        );

        if (swapDataDst.length > 0) {
            bytes memory swapLenBytes = LibCross.serializeU256WithHexStr(
                swapDataDst.length
            );
            encodeData = encodeData.concat(
                abi.encodePacked(uint8(swapLenBytes.length), swapLenBytes)
            );
        }

        for (uint256 i = 0; i < swapDataDst.length; i++) {
            encodeData = encodeData.concat(
                abi.encodePacked(
                    uint8(swapDataDst[i].callTo.length),
                    swapDataDst[i].callTo,
                    uint8(swapDataDst[i].sendingAssetId.length),
                    swapDataDst[i].sendingAssetId,
                    uint8(swapDataDst[i].receivingAssetId.length),
                    swapDataDst[i].receivingAssetId,
                    uint16(swapDataDst[i].callData.length),
                    swapDataDst[i].callData
                )
            );
        }
        return encodeData;
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
    function decodeBoolSwapPayload(
        bytes memory stargatePayload
    )
        public
        pure
        returns (
            ISo.NormalizedSoData memory soData,
            LibSwap.NormalizedSwapData[] memory swapDataDst
        )
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
        require(index == stargatePayload.length, "LenErr");
        return (data.soData, data.swapDataDst);
    }

    function estimateBoolFee(
        ISo.NormalizedSoData calldata soDataNo,
        BoolSwapData calldata boolSwapData,
        uint256 bridgeAmount,
        LibSwap.NormalizedSwapData[] calldata swapDataDstNo
    ) public view returns (uint256) {
        Storage storage s = getStorage();

        bytes memory payload = encodeBoolSwapPayload(soDataNo, swapDataDstNo);
        uint256 boolFee = IBoolSwapRouter(s.boolSwapRouter).estimateBNFee(
            boolSwapData.srcBoolSwapPoolId,
            boolSwapData.dstBoolSwapChainId,
            bridgeAmount,
            boolSwapData.dstSoDiamond,
            payload
        );
        return boolFee;
    }

    /// @dev Get remain gas for transfer
    function getBoolTransferGas() public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.boolSwapRouter];
        if (soFee == address(0x0)) {
            return 30000;
        } else {
            return ILibSoFeeV2(soFee).getTransferForGas();
        }
    }

    /// @dev Get so fee
    function getBoolSoFee(uint256 amount) public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.boolSwapRouter];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getFees(amount);
        }
    }

    /// @dev Get basic beneficiary
    function getBoolBasicBeneficiary() public view returns (address) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.boolSwapRouter];
        if (soFee == address(0x0)) {
            return address(0x0);
        } else {
            return ILibSoFeeV2(soFee).getBasicBeneficiary();
        }
    }

    /// @dev Get basic fee
    function getBoolBasicFee() public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.boolSwapRouter];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getBasicFee();
        }
    }

    /// Private Methods ///

    /// @dev fetch local storage
    function getStorage() private pure returns (Storage storage s) {
        bytes32 namespace = NAMESPACE;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            s.slot := namespace
        }
    }
}
