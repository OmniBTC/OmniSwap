// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../Libraries/LzLib.sol";
import "../Libraries/LibAsset.sol";
import "../Interfaces/ISo.sol";
import "../Interfaces/ICorrectSwap.sol";
import "../Libraries/LibDiamond.sol";
import "../Helpers/ReentrancyGuard.sol";
import "../Errors/GenericErrors.sol";
import "../Helpers/Swapper.sol";
import "../Interfaces/ILibSoFeeV2.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibBytes.sol";
import "../Interfaces/CoreBridge/IOriginalTokenBridge.sol";
import "../Interfaces/CoreBridge/IWrappedTokenBridge.sol";

/// @title CoreBridge Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through CoreBridge
contract CoreBridgeFacet is Swapper, ReentrancyGuard {
    using SafeMath for uint256;
    using LibBytes for bytes;

    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"4269acc1e23b68e65caaa394da4c0dfe5bcd69126c9ede1696d7a946c3d4c467"; //keccak256("com.so.facets.corebridge");

    struct Storage {
        address bridge; // The coredao bridge address
        uint16 srcLzChainId; // The source chain id
        uint16 coreLzChainId; // The core chain id
    }

    struct CoreBridgeData {
        address bridgeToken;
        uint16 remoteChainId;
        address to;
        bool unwrapWeth; // WETH cross-chain back to the source chain is whether it needs to be converted to ETH
    }

    struct CacheBridge {
        address bridgeToken;
        uint256 bridgeAmount;
        uint256 bridgeFee;
        uint16 remoteChainId;
        address to;
        bool unwrapWeth;
        LzLib.CallParams lzTxParams;
        bytes adapterParams;
    }

    /// Events ///

    event CoreBridgeInitialized(
        address bridge,
        uint16 chainId,
        uint16 coreChainId
    );

    /// Init ///

    function initCoreBridge(
        address bridge,
        uint16 chainId,
        uint16 coreChainId
    ) external {
        LibDiamond.enforceIsContractOwner();
        if (bridge == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.bridge = bridge;
        s.srcLzChainId = chainId;
        s.coreLzChainId = coreChainId;
        emit CoreBridgeInitialized(bridge, chainId, coreChainId);
    }

    /// External Methods ///

    /// @notice Bridges tokens via CoreBridge
    /// @param soDataNo Data for tracking cross-chain transactions and a
    ///                portion of the accompanying cross-chain messages
    /// @param swapDataSrcNo Contains a set of data required for Swap
    ///                     transactions on the source chain side
    function soSwapViaCoreBridge(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo,
        CoreBridgeData calldata coreBridgeData
    ) external payable nonReentrant {
        CacheBridge memory cache;

        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
        }

        _capBridgeSoFee();

        cache.bridgeToken = coreBridgeData.bridgeToken;

        if (swapDataSrc.length == 0) {
            transferWrappedAsset(
                soData.sendingAssetId,
                cache.bridgeToken,
                soData.amount
            );
            cache.bridgeAmount = soData.amount;
        } else {
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            cache.bridgeAmount = this.executeAndCheckSwaps(soData, swapDataSrc);
            transferWrappedAsset(
                swapDataSrc[swapDataSrc.length - 1].receivingAssetId,
                cache.bridgeToken,
                cache.bridgeAmount
            );
        }

        cache.remoteChainId = coreBridgeData.remoteChainId;
        cache.to = coreBridgeData.to;
        cache.lzTxParams = LzLib.CallParams({
            refundAddress: payable(coreBridgeData.to),
            zroPaymentAddress: address(0)
        });
        cache.adapterParams = bytes("");
        // core bridge fee
        cache.bridgeFee = getCoreBridgeFee(coreBridgeData.remoteChainId);

        _startBridge(cache);

        emit SoTransferStarted(soData.transactionId);
    }

    /// Public Methods ///

    function estimateBridgeFee(
        uint16 remoteChainId
    ) public view returns (uint256) {
        return getCoreBridgeFee(remoteChainId) + getCoreBridgeBasicFee();
    }

    function getCoreBridgeFee(
        uint16 remoteChainId
    ) public view returns (uint256) {
        Storage storage s = getStorage();

        uint256 fee;
        if (s.coreLzChainId == s.srcLzChainId) {
            (fee, ) = IWrappedTokenBridge(s.bridge).estimateBridgeFee(
                remoteChainId,
                false,
                ""
            );
        } else {
            (fee, ) = IOriginalTokenBridge(s.bridge).estimateBridgeFee(
                false,
                ""
            );
        }

        return fee;
    }

    /// @dev Get basic beneficiary
    function getCoreBridgeBasicBeneficiary() public view returns (address) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.bridge];
        if (soFee == address(0x0)) {
            return address(0x0);
        } else {
            return ILibSoFeeV2(soFee).getBasicBeneficiary();
        }
    }

    /// @dev Get basic fee
    function getCoreBridgeBasicFee() public view returns (uint256) {
        Storage storage s = getStorage();
        address soFee = appStorage.gatewaySoFeeSelectors[s.bridge];
        if (soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFeeV2(soFee).getBasicFee();
        }
    }

    /// Private Methods ///

    function _capBridgeSoFee() private {
        uint256 soBasicFee = getCoreBridgeBasicFee();
        address soBasicBeneficiary = getCoreBridgeBasicBeneficiary();
        if (soBasicBeneficiary == address(0x0)) {
            soBasicFee = 0;
        }

        if (soBasicFee > 0) {
            LibAsset.transferAsset(
                address(0x0),
                payable(soBasicBeneficiary),
                soBasicFee
            );
        }
    }

    /// @dev Conatains the business logic for the bridge via CoreBridge
    function _startBridge(CacheBridge memory cache) private {
        Storage storage s = getStorage();
        address bridge = s.bridge;

        if (cache.bridgeToken == address(0)) {
            cache.bridgeFee = cache.bridgeFee + cache.bridgeAmount;
        }

        if (cache.bridgeToken != address(0)) {
            LibAsset.safeApproveERC20(
                IERC20(cache.bridgeToken),
                bridge,
                cache.bridgeAmount
            );
        }

        if (s.srcLzChainId == s.coreLzChainId) {
            // Bridge from core to others
            IWrappedTokenBridge(bridge).bridge{value: cache.bridgeFee}(
                cache.bridgeToken,
                cache.remoteChainId,
                cache.bridgeAmount,
                cache.to,
                cache.unwrapWeth,
                cache.lzTxParams,
                cache.adapterParams
            );
        } else {
            // Bridge from others to core
            if (cache.bridgeToken == address(0)) {
                // Bridge from others to core
                IOriginalTokenBridge(bridge).bridgeNative{
                    value: cache.bridgeFee
                }(
                    cache.bridgeAmount,
                    cache.to,
                    cache.lzTxParams,
                    cache.adapterParams
                );
            } else {
                IOriginalTokenBridge(bridge).bridge{value: cache.bridgeFee}(
                    cache.bridgeToken,
                    cache.bridgeAmount,
                    cache.to,
                    cache.lzTxParams,
                    cache.adapterParams
                );
            }
        }
    }

    /// @dev fetch local storage
    function getStorage() private pure returns (Storage storage s) {
        bytes32 namespace = NAMESPACE;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            s.slot := namespace
        }
    }
}
