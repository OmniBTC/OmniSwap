// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import {LibAsset, IERC20} from "../Libraries/LibAsset.sol";
import {ISo} from "../Interfaces/ISo.sol";
import {IStargate} from "../Interfaces/IStargate.sol";
import {LibDiamond} from "../Libraries/LibDiamond.sol";
import {ReentrancyGuard} from "../Helpers/ReentrancyGuard.sol";
import {InvalidAmount, CannotBridgeToSameNetwork, NativeValueWithERC, InvalidConfig} from "../Errors/GenericErrors.sol";
import {Swapper, LibSwap} from "../Helpers/Swapper.sol";

/// @title Stargate Facet
/// @author SoSwap
/// @notice Provides functionality for bridging through Stargate
contract StargateFacet is ISo, Swapper, ReentrancyGuard {
    /// Storage ///

    bytes32 internal constant NAMESPACE = hex"2bd10e5dcb5694caec513d6d8fa1fd90f6a026e0e9320d7b6e2f8e49b93270d1"; //keccak256("com.so.facets.stargate");
    struct Storage {
        address Stargate;
        uint16 StargateChainId;
    }

    /// Types ///

    struct StargateData {
        uint256 srcPoolId;
        uint16 dstChainId;
        uint256 dstPoolId;
        uint256 amountLD;
        uint256 minAmountLD;
        address payable receiver;
        address token;
    }

    /// Events ///

    event StargateInitialized(address Stargate, uint256 chainId);

    /// Init ///

    /// @notice Initializes local variables for the Stargate facet
    /// @param _Stargate address of the canonical Stargate router contract
    /// @param _chainId chainId of this deployed contract
    function initStargate(address _Stargate, uint16 _chainId) external {
        // LibDiamond.enforceIsContractOwner();
        if (_Stargate == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.Stargate = _Stargate;
        s.StargateChainId = _chainId;
        emit StargateInitialized(_Stargate, _chainId);
    }

    /// External Methods ///

    /// @notice Bridges tokens via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _StargateData data specific to Stargate
    function startBridgeTokensViaStargate(SoData calldata _soData, StargateData calldata _StargateData)
    external
    payable
    nonReentrant
    {
        LibAsset.depositAsset(_StargateData.token, _StargateData.amountLD);
        _startBridge(_StargateData);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            msg.sender,
            _StargateData.amountLD,
            _StargateData.dstChainId,
            false,
            false
        );
    }

    /// @notice Performs a swap before bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapDataSrc an array of swap related data for performing swaps before bridging
    /// @param _StargateData data specific to Stargate
    function startSwapAndBridgeTokensViaStargate(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        StargateData memory _StargateData
    ) external payable nonReentrant {
        _StargateData.amountLD = _executeAndCheckSwaps(_soData, _swapDataSrc);
        _startBridge(_StargateData);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            msg.sender,
            _swapDataSrc[0].fromAmount,
            _StargateData.dstChainId,
            true,
            false
        );
    }

    /// @notice Performs a swap after bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _StargateData data specific to Stargate
    /// @param _swapDataDst an array of swap related data for performing swaps before bridging
    function startBridgeTokensAndSwapViaStargate(
        SoData calldata _soData,
        StargateData memory _StargateData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable nonReentrant {
        // todo! move into sgReceive for _swapDataDst
        _startBridge(_StargateData);

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            msg.sender,
            _StargateData.amountLD,
            _StargateData.dstChainId,
            false,
            true
        );
    }

    /// @notice Performs a swap before and after bridging via Stargate
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapDataSrc an array of swap related data for performing swaps before bridging
    /// @param _StargateData data specific to Stargate
    /// @param _swapDataDst an array of swap related data for performing swaps before bridging
    function startSwapAndSwapViaStargate(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        StargateData memory _StargateData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable nonReentrant {
        _StargateData.amountLD = _executeAndCheckSwaps(_soData, _swapDataSrc);
        _startBridge(_StargateData);
        // todo! move into sgReceive for _swapDataDst

        emit SoTransferStarted(
            _soData.transactionId,
            "Stargate",
            _soData.sendingAssetId,
            _soData.receivingAssetId,
            msg.sender,
            _StargateData.amountLD,
            _StargateData.dstChainId,
            true,
            true
        );
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via Stargate
    /// @param _StargateData data specific to Stargate
    function _startBridge(StargateData memory _StargateData) private {
        Storage storage s = getStorage();
        address bridge = s.Stargate;

        // Do Stargate stuff
        if (s.StargateChainId == _StargateData.dstChainId) revert CannotBridgeToSameNetwork();

        if (LibAsset.isNativeAsset(_StargateData.token)) {
            revert("Stargate: not supported native asset!");
        } else {
            // Give Stargate approval to bridge tokens
            LibAsset.maxApproveERC20(IERC20(_StargateData.token), bridge, _StargateData.amountLD);
            // solhint-disable check-send-result
            IStargate(bridge).swap{value : msg.value}(
                _StargateData.dstChainId,
                _StargateData.srcPoolId,
                _StargateData.dstPoolId,
                _StargateData.receiver,
                _StargateData.amountLD,
                _StargateData.minAmountLD,
                IStargate.lzTxObj(0, 0, "0x"),
                abi.encodePacked(msg.sender),
                bytes("")
            );
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
