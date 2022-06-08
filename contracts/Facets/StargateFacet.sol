// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import {LibAsset, IERC20} from "../Libraries/LibAsset.sol";
import {ISo} from "../Interfaces/ISo.sol";
import {IStargate} from "../Interfaces/IStargate.sol";
import {IStargateReceiver} from "../Interfaces/IStargateReceiver.sol";
import {LibDiamond} from "../Libraries/LibDiamond.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";
import {InvalidAmount, CannotBridgeToSameNetwork, NativeValueWithERC, InvalidConfig} from "../Errors/GenericErrors.sol";
import {Swapper, LibSwap} from "../Helpers/Swapper.sol";
import {ILibSoFee} from "../Interfaces/ILibSoFee.sol";

/// @title Stargate Facet
/// @author SoSwap
/// @notice Provides functionality for bridging through Stargate
contract StargateFacet is ISo, Swapper, ReentrancyGuard, IStargateReceiver {
    /// Storage ///

    bytes32 internal constant NAMESPACE =
    hex"2bd10e5dcb5694caec513d6d8fa1fd90f6a026e0e9320d7b6e2f8e49b93270d1"; //keccak256("com.so.facets.stargate");

    struct Storage {
        address Stargate;
        uint16 StargateChainId;
    }

    /// Types ///

    struct StargateData {
        uint256 srcStargatePoolId;  // The stargate pool id of the source chain
        address srcStargateToken;  // The stargate pool id of the source chain
        uint16 dstStargateChainId; // The stargate chain id of the destination chain
        uint256 dstStargatePoolId; // The stargate pool id of the destination chain
        uint256 minAmount; // The stargate min amount
        IStargate.lzTxObj lzTxParams; // destination gas for sgReceive
        address payable dstSoDiamond; // destination SoDiamond address
    }

    /// Events ///

    event StargateInitialized(address Stargate, uint256 chainId);

    //---------------------------------------------------------------------------
    // MODIFIERS
    modifier onlyStargate() {
        Storage storage s = getStorage();
        require(msg.sender == s.Stargate, "Caller must be Stargate.");
        _;
    }

    /// Init ///

    /// @notice Initializes local variables for the Stargate facet
    /// @param _Stargate address of the canonical Stargate router contract
    /// @param _chainId chainId of this deployed contract
    function initStargate(address _Stargate, uint16 _chainId) external {
        LibDiamond.enforceIsContractOwner();
        if (_Stargate == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.Stargate = _Stargate;
        s.StargateChainId = _chainId;
        emit StargateInitialized(_Stargate, _chainId);
    }

    /// External Methods ///

    /// @notice Bridges tokens via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _stargateData data specific to Stargate
    function startBridgeTokensViaStargate(
        SoData calldata _soData,
        StargateData calldata _stargateData
    ) external payable nonReentrant {
        LibAsset.depositAsset(_stargateData.srcStargateToken, _soData.amount);

        bytes memory payload = abi.encode(_soData, bytes(""));
        uint256 _stargateValue = _getStargateValue(_soData);
        _startBridge(_stargateData, _stargateValue, _soData.amount, payload);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            false,
            false,
            _soData
        );
    }

    /// @notice Performs a swap before bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapDataSrc an array of swap related data for performing swaps before bridging
    /// @param _stargateData data specific to Stargate
    function startSwapAndBridgeTokensViaStargate(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        StargateData calldata _stargateData
    ) external payable nonReentrant {
        uint256 _bridgeAmount = this.executeAndCheckSwaps(
            _soData,
            _swapDataSrc
        );
        bytes memory payload = abi.encode(_soData, bytes(""));
        uint256 _stargateValue = _getStargateValue(_soData);
        _startBridge(_stargateData, _stargateValue, _bridgeAmount, payload);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            true,
            false,
            _soData
        );
    }

    /// @notice Performs a swap after bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _stargateData data specific to Stargate
    /// @param _swapDataDst an array of swap related data for performing swaps before bridging
    function startBridgeTokensAndSwapViaStargate(
        SoData calldata _soData,
        StargateData calldata _stargateData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable nonReentrant {
        LibAsset.depositAsset(_stargateData.srcStargateToken, _soData.amount);

        bytes memory payload = abi.encode(
            _soData,
            abi.encode(_swapDataDst)
        );
        uint256 _stargateValue = _getStargateValue(_soData);
        _startBridge(_stargateData, _stargateValue, _soData.amount, payload);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            false,
            true,
            _soData
        );
    }

    /// @notice Performs a swap before and after bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapDataSrc an array of swap related data for performing swaps before bridging
    /// @param _stargateData data specific to Stargate
    /// @param _swapDataDst an array of swap related data for performing swaps before bridging
    function startSwapAndSwapViaStargate(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        StargateData calldata _stargateData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable nonReentrant {
        uint256 _bridgeAmount = this.executeAndCheckSwaps(
            _soData,
            _swapDataSrc
        );
        bytes memory payload = abi.encode(
            _soData,
            abi.encode(_swapDataDst)
        );
        uint256 _stargateValue = _getStargateValue(_soData);
        _startBridge(_stargateData, _stargateValue, _bridgeAmount, payload);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            true,
            true,
            _soData
        );
    }

    function sgReceive(
        uint16 _chainId,
        bytes memory _srcAddress,
        uint256 _nonce,
        address _token,
        uint256 amountLD,
        bytes memory payload
    ) external onlyStargate {
        (SoData memory _soData, bytes memory swapPayload) = abi.decode(
            payload,
            (SoData, bytes)
        );
        if (swapPayload.length == 0) {
            LibAsset.transferAsset(_token, _soData.receiver, amountLD);
            emit SoTransferCompleted(
                _soData.transactionId,
                _soData.receivingAssetId,
                _soData.receiver,
                amountLD,
                block.timestamp,
                _soData
            );
        } else {
            (
            LibSwap.SwapData[] memory _swapDataDst
            ) = abi.decode(swapPayload, (LibSwap.SwapData[]));
            uint256 _soFee = _getSoFee(amountLD);
            if (_soFee < amountLD) {
                _swapDataDst[0].fromAmount = amountLD - _soFee;
            } else {
                _swapDataDst[0].fromAmount = amountLD;
            }
            _swapDataDst[0].callData = this.correctSwap(
                _swapDataDst[0].callData,
                _swapDataDst[0].fromAmount
            );

            try this.executeAndCheckSwaps(_soData, _swapDataDst) returns (
                uint256 amountFinal
            ) {
                LibAsset.transferAsset(
                    _swapDataDst[_swapDataDst.length - 1].receivingAssetId,
                    _soData.receiver,
                    amountFinal
                );
                emit SoTransferCompleted(
                    _soData.transactionId,
                    _soData.receivingAssetId,
                    _soData.receiver,
                    amountFinal,
                    block.timestamp,
                    _soData
                );
            } catch (bytes memory reason) {
                LibAsset.transferAsset(_token, _soData.receiver, amountLD);
                emit SoTransferFailed(_soData.transactionId, reason, _soData);
            }
        }
    }

    function correctSwap(
        bytes calldata data,
        uint256 amount
    ) external view returns (bytes memory){
        bytes4 sig = bytes4(data[: 4]);
        (
        uint256 amountIn,
        uint256 amountOutMin,
        address[] memory path,
        address to,
        uint256 deadline
        ) = abi.decode(
            data[4 :],
            (uint256, uint256, address[], address, uint256)
        );
        return
        abi.encodeWithSelector(
            sig,
            amount,
            amountOutMin,
            path,
            to,
            deadline
        );
    }

    function _getSoFee(uint256 _amountLD) private returns (uint256) {
        address _soFee = appStorage.gatewaySoFeeSelectors[address(this)];
        if (_soFee == address(0x0)) {
            return 0;
        } else {
            return ILibSoFee(_soFee).getFees(_amountLD);
        }
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via Stargate
    /// @param _StargateData data specific to Stargate
    function _startBridge(
        StargateData calldata _StargateData,
        uint256 _stargateValue,
        uint256 _bridgeAmount,
        bytes memory payload
    ) private {
        Storage storage s = getStorage();
        address bridge = s.Stargate;

        // Do Stargate stuff
        if (s.StargateChainId == _StargateData.dstStargateChainId)
            revert CannotBridgeToSameNetwork();

        if (LibAsset.isNativeAsset(_StargateData.srcStargateToken)) {
            revert("Stargate: not supported native asset!");
        } else {
            // Give Stargate approval to bridge tokens
            LibAsset.maxApproveERC20(
                IERC20(_StargateData.srcStargateToken),
                bridge,
                _bridgeAmount
            );
            //            uint256 _stargateValue = _getStargateValue(_soData);
            IStargate(bridge).swap{value : _stargateValue}(
                _StargateData.dstStargateChainId,
                _StargateData.srcStargatePoolId,
                _StargateData.dstStargatePoolId,
                payable(msg.sender),
                _bridgeAmount,
                _StargateData.minAmount,
                _StargateData.lzTxParams,
                abi.encodePacked(_StargateData.dstSoDiamond),
                payload
            );
        }
    }

    function _getStargateValue(SoData calldata _soData) private returns (uint256){
        if (LibAsset.isNativeAsset(_soData.sendingAssetId)) {
            require(msg.value > _soData.amount, "Stargate value is not enough!");
            return msg.value - _soData.amount;
        } else {
            return msg.value;
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
