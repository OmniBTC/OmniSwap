// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import { ITransactionManager } from "../Interfaces/ITransactionManager.sol";
import { ISo } from "../Interfaces/ISo.sol";
import { LibAsset, IERC20 } from "../Libraries/LibAsset.sol";
import { LibDiamond } from "../Libraries/LibDiamond.sol";
import { ReentrancyGuard } from "../Helpers/ReentrancyGuard.sol";
import { InvalidAmount, NativeValueWithERC, NoSwapDataProvided, InvalidConfig } from "../Errors/GenericErrors.sol";
import { Swapper, LibSwap } from "../Helpers/Swapper.sol";

/// @title NXTP (Connext) Facet
/// @author LI.FI (https://li.fi)
/// @notice Provides functionality for bridging through NXTP (Connext)
contract NXTPFacet is ISo, Swapper, ReentrancyGuard {
    /// Storage ///

    bytes32 internal constant NAMESPACE = hex"cb4800033539e504944b70f0275e98829f191b99c5226e9a5a072ab49d2a753e"; //keccak256("com.so.facets.nxtp");
    struct Storage {
        ITransactionManager nxtpTxManager;
    }

    /// Events ///

    event NXTPInitialized(ITransactionManager txMgrAddr);

    /// Init ///

    // @notice Initializes local variables for the NXTP facet
    /// @param _txMgrAddr address of the NXTP Transaction Manager contract
    function initNXTP(ITransactionManager _txMgrAddr) external {
        LibDiamond.enforceIsContractOwner();
        if (address(_txMgrAddr) == address(0)) revert InvalidConfig();
        Storage storage s = getStorage();
        s.nxtpTxManager = _txMgrAddr;

        emit NXTPInitialized(_txMgrAddr);
    }

    /// External Methods ///

    /// @notice This function starts a cross-chain transaction using the NXTP protocol
    /// @param _soData data used purely for tracking and analytics
    /// @param _nxtpData data needed to complete an NXTP cross-chain transaction
    function startBridgeTokensViaNXTP(SoData calldata _soData, ITransactionManager.PrepareArgs calldata _nxtpData)
        external
        payable
        nonReentrant
    {
        LibAsset.depositAsset(_nxtpData.invariantData.sendingAssetId, _nxtpData.amount);
        _startBridge(_nxtpData);

        emit SoTransferStarted(
            _soData.transactionId,
            "nxtp",
            "",
            _soData.integrator,
            _soData.referrer,
            _nxtpData.invariantData.sendingAssetId,
            _soData.receivingAssetId,
            _nxtpData.invariantData.receivingAddress,
            _nxtpData.amount,
            _nxtpData.invariantData.receivingChainId,
            false,
            _nxtpData.invariantData.callTo != address(0)
        );
    }

    /// @notice This function performs a swap or multiple swaps and then starts a cross-chain transaction
    ///         using the NXTP protocol.
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapData array of data needed for swaps
    /// @param _nxtpData data needed to complete an NXTP cross-chain transaction
    function swapAndStartBridgeTokensViaNXTP(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapData,
        ITransactionManager.PrepareArgs memory _nxtpData
    ) external payable nonReentrant {
        _nxtpData.amount = _executeAndCheckSwaps(_soData, _swapData);
        _startBridge(_nxtpData);

        emit SoTransferStarted(
            _soData.transactionId,
            "nxtp",
            "",
            _soData.integrator,
            _soData.referrer,
            _swapData[0].sendingAssetId,
            _soData.receivingAssetId,
            _nxtpData.invariantData.receivingAddress,
            _swapData[0].fromAmount,
            _nxtpData.invariantData.receivingChainId,
            true,
            _nxtpData.invariantData.callTo != address(0)
        );
    }

    /// @notice Completes a cross-chain transaction on the receiving chain using the NXTP protocol.
    /// @param _soData data used purely for tracking and analytics
    /// @param assetId token received on the receiving chain
    /// @param receiver address that will receive the tokens
    /// @param amount number of tokens received
    function completeBridgeTokensViaNXTP(
        SoData calldata _soData,
        address assetId,
        address receiver,
        uint256 amount
    ) external payable nonReentrant {
        LibAsset.depositAsset(assetId, amount);
        LibAsset.transferAsset(assetId, payable(receiver), amount);
        emit SoTransferCompleted(_soData.transactionId, assetId, receiver, amount, block.timestamp);
    }

    /// @notice Performs a swap before completing a cross-chain transaction
    ///         on the receiving chain using the NXTP protocol.
    /// @param _soData data used purely for tracking and analytics
    /// @param _swapData array of data needed for swaps
    /// @param finalAssetId token received on the receiving chain
    /// @param receiver address that will receive the tokens
    function swapAndCompleteBridgeTokensViaNXTP(
        SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapData,
        address finalAssetId,
        address receiver
    ) external payable nonReentrant {
        uint256 swapBalance = _executeAndCheckSwaps(_soData, _swapData);
        LibAsset.transferAsset(finalAssetId, payable(receiver), swapBalance);
        emit SoTransferCompleted(_soData.transactionId, finalAssetId, receiver, swapBalance, block.timestamp);
    }

    /// @notice show the NXTP transaction manager contract address
    function getNXTPTransactionManager() external view returns (address) {
        Storage storage s = getStorage();
        return address(s.nxtpTxManager);
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via NXTP
    /// @param _nxtpData data specific to NXTP
    function _startBridge(ITransactionManager.PrepareArgs memory _nxtpData) private returns (bytes32) {
        Storage storage s = getStorage();
        IERC20 sendingAssetId = IERC20(_nxtpData.invariantData.sendingAssetId);
        // Give Connext approval to bridge tokens
        LibAsset.maxApproveERC20(IERC20(sendingAssetId), address(s.nxtpTxManager), _nxtpData.amount);

        uint256 value = LibAsset.isNativeAsset(address(sendingAssetId)) ? _nxtpData.amount : 0;

        // Initiate bridge transaction on sending chain
        ITransactionManager.TransactionData memory result = s.nxtpTxManager.prepare{ value: value }(_nxtpData);
        return result.transactionId;
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
