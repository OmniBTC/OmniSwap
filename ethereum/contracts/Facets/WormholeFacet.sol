// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "../Libraries/LibDiamond.sol";
import "../Interfaces/ISo.sol";
import "../Helpers/Swapper.sol";
import "../Interfaces/IWormholeBridge.sol";

/// @title Wormhole Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through Wormhole
contract WormholeFacet is Swapper {
    bytes32 internal constant NAMESPACE =
        hex"5cf8a649899e43a2530442580fb1a9721870a3fa10790c9ef200c611cab819d4"; // keccak256("com.omnibtc.facets.wormhole")

    struct Storage {
        address tokenBridge;
        uint16 wormholeChainId;
        uint32 nonce;
    }

    /// Events ///

    event InitWormholeEvent(address tokenBridge, uint16 wormholeChainId);

    /// Types ///
    struct WormholeData {
        address bridgeToken;
        uint16 recipientChain; // wormhole chain id
        bytes32 recipient;
    }

    /// Init ///

    /// init wormhole token bridge
    function initWormholeTokenBridge(
        address _tokenBridge,
        uint16 _wormholeChainId
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.tokenBridge = _tokenBridge;
        s.wormholeChainId = _wormholeChainId;
        emit InitWormholeEvent(_tokenBridge, _wormholeChainId);
    }

    /// External Methods ///

    /// transfer with payload
    function omniswapViaWormhole(
        ISo.SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        WormholeData calldata _wormholeData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable {
        bool _hasSourceSwap;
        bool _hasDestinationSwap;
        uint256 _bridgeAmount;
        if (!LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            LibAsset.depositAsset(_soData.sendingAssetId, _soData.amount);
        }
        if (_swapDataSrc.length == 0) {
            _bridgeAmount = _soData.amount;
            _hasSourceSwap = false;
        } else {
            require(
                _soData.amount == _swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            _bridgeAmount = this.executeAndCheckSwaps(_soData, _swapDataSrc);
            _hasSourceSwap = true;
        }

        bytes memory _payload;
        if (_swapDataDst.length == 0) {
            _payload = abi.encode(_soData, bytes(""));
            _hasDestinationSwap = false;
        } else {
            _payload = abi.encode(_soData, abi.encode(_swapDataDst));
            _hasDestinationSwap = true;
        }

        /// start bridge
        startBridge(_wormholeData, _bridgeAmount, _payload);

        emit ISo.SoTransferStarted(
            _soData.transactionId,
            "Wormhole",
            _hasSourceSwap,
            _hasDestinationSwap,
            _soData
        );
    }

    function startBridge(
        WormholeData calldata _wormholeData,
        uint256 _amount,
        bytes memory _payload
    ) internal {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;

        LibAsset.maxApproveERC20(
            IERC20(_wormholeData.bridgeToken),
            bridge,
            _amount
        );

        IWormholeBridge(bridge).transferTokensWithPayload{value: msg.value}(
            _wormholeData.bridgeToken,
            _amount,
            _wormholeData.recipientChain,
            _wormholeData.recipient,
            s.nonce,
            _payload
        );
        s.nonce += 1;
    }

    /// complete transfer with payload
    /// called by relayer
    function completeSwap(bytes memory _encodeVm) external {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;
        bytes memory _payload = IWormholeBridge(bridge)
            .completeTransferWithPayload(_encodeVm);

        (SoData memory _soData, bytes memory _swapPayload) = abi.decode(
            _payload,
            (SoData, bytes)
        );

        uint256 amount = LibAsset.getOwnBalance(_soData.receivingAssetId);
        if (_swapPayload.length == 0) {
            LibAsset.transferAsset(
                _soData.receivingAssetId,
                _soData.receiver,
                amount
            );
            emit SoTransferCompleted(
                _soData.transactionId,
                _soData.receivingAssetId,
                _soData.receiver,
                amount,
                block.timestamp,
                _soData
            );
        } else {
            LibSwap.SwapData[] memory _swapDataDst = abi.decode(
                _swapPayload,
                (LibSwap.SwapData[])
            );

            _swapDataDst[0].fromAmount = amount;

            address _correctSwap = appStorage.correctSwapRouterSelectors;

            if (_correctSwap != address(0)) {
                _swapDataDst[0].callData = ICorrectSwap(_correctSwap)
                    .correctSwap(
                        _swapDataDst[0].callData,
                        _swapDataDst[0].fromAmount
                    );
            }

            try this.executeAndCheckSwaps(_soData, _swapDataDst) returns (
                uint256 _amountFinal
            ) {
                LibAsset.transferAsset(
                    _swapDataDst[_swapDataDst.length - 1].receivingAssetId,
                    _soData.receiver,
                    _amountFinal
                );
                emit SoTransferCompleted(
                    _soData.transactionId,
                    _soData.receivingAssetId,
                    _soData.receiver,
                    _amountFinal,
                    block.timestamp,
                    _soData
                );
            } catch Error(string memory revertReason) {
                LibAsset.transferAsset(
                    _soData.receivingAssetId,
                    _soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    _soData.transactionId,
                    revertReason,
                    bytes(""),
                    _soData
                );
            } catch (bytes memory returnData) {
                LibAsset.transferAsset(
                    _soData.receivingAssetId,
                    _soData.receiver,
                    amount
                );
                emit SoTransferFailed(
                    _soData.transactionId,
                    "",
                    returnData,
                    _soData
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
