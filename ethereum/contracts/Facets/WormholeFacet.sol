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
        hex"d4ca4302bca26785486b2ceec787497a9cf992c36dcf57c306a00c1f88154623"; // keccak256("com.so.facets.wormhole")

    struct Storage {
        address tokenBridge;
        uint16 srcWormholeChainId;
        uint32 nonce;
    }

    /// Events ///

    event InitWormholeEvent(address tokenBridge, uint16 srcWormholeChainId);

    /// Types ///
    struct WormholeData {
        uint16 dstWormholeChainId;
        address dstSoDiamond;
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
        s.srcWormholeChainId = _wormholeChainId;
        emit InitWormholeEvent(_tokenBridge, _wormholeChainId);
    }

    /// External Methods ///

    /// transfer with payload
    function soSwapViaWormhole(
        ISo.SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        WormholeData calldata _wormholeData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable {
        bool _hasSourceSwap;
        bool _hasDestinationSwap;
        uint256 _bridgeAmount;
        address _bridgeAddress;
        if (!LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            LibAsset.depositAsset(_soData.sendingAssetId, _soData.amount);
        }
        if (_swapDataSrc.length == 0) {
            _bridgeAddress = _soData.sendingAssetId;
            _bridgeAmount = _soData.amount;
            _hasSourceSwap = false;
        } else {
            require(
                _soData.amount == _swapDataSrc[0].fromAmount,
                "soData and swapDataSrc amount not match!"
            );
            _bridgeAmount = this.executeAndCheckSwaps(_soData, _swapDataSrc);
            _bridgeAddress = _swapDataSrc[_swapDataSrc.length - 1]
                .receivingAssetId;
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
        _startBridge(_wormholeData, _bridgeAddress, _bridgeAmount, _payload);

        emit ISo.SoTransferStarted(
            _soData.transactionId,
            "Wormhole",
            _hasSourceSwap,
            _hasDestinationSwap,
            _soData
        );
    }

    function completeTransferAndUnwrapETHWithPayload(bytes memory _encodeVm)
        external
    {
        completeSoSwap(_encodeVm);
    }

    function completeTransferWithPayload(bytes memory _encodeVm) external {
        completeSoSwap(_encodeVm);
    }

    /// complete transfer with payload
    /// called by relayer
    function completeSoSwap(bytes memory _encodeVm) public {
        Storage storage s = getStorage();
        address bridge = s.tokenBridge;

        bytes memory payload = IWormholeBridge(bridge)
            .completeTransferWithPayload(_encodeVm);

        IWormholeBridge.TransferWithPayload
            memory _wormholePayload = IWormholeBridge(bridge)
                .parseTransferWithPayload(payload);

        (SoData memory _soData, bytes memory _swapPayload) = abi.decode(
            _wormholePayload.payload,
            (SoData, bytes)
        );

        address _tokenAddress = address(
            uint160(uint256(_wormholePayload.tokenAddress))
        );

        uint256 amount = LibAsset.getOwnBalance(_tokenAddress);

        IWETH _weth = IWormholeBridge(bridge).WETH();

        if (address(_weth) == _tokenAddress) {
            _weth.withdraw(amount);
        }

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

    /// Internal Methods ///

    function _startBridge(
        WormholeData calldata _wormholeData,
        address _token,
        uint256 _amount,
        bytes memory _payload
    ) internal {
        Storage storage s = getStorage();
        address _bridge = s.tokenBridge;

        if (LibAsset.isNativeAsset(_token)) {
            IWormholeBridge(_bridge).wrapAndTransferETHWithPayload{
                value: msg.value
            }(
                _wormholeData.dstWormholeChainId,
                bytes32(uint256(uint160(_wormholeData.dstSoDiamond))),
                s.nonce,
                _payload
            );
        } else {
            LibAsset.maxApproveERC20(IERC20(_token), _bridge, _amount);
            IWormholeBridge(_bridge).transferTokensWithPayload{
                value: msg.value
            }(
                _token,
                _amount,
                _wormholeData.dstWormholeChainId,
                bytes32(uint256(uint160(_wormholeData.dstSoDiamond))),
                s.nonce,
                _payload
            );
        }

        uint256 _dust = LibAsset.getOwnBalance(_token);
        if (_dust > 0) {
            LibAsset.transferAsset(_token, payable(msg.sender), _dust);
        }

        s.nonce += 1;
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
