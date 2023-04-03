// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "../Errors/GenericErrors.sol";
import "../Libraries/LibAsset.sol";
import "../Libraries/LibCross.sol";
import "../Libraries/LibDiamond.sol";
import "../Interfaces/IZkSyncDeposit.sol";
import "../Helpers/Swapper.sol";
import "../Helpers/ReentrancyGuard.sol";

/// @title ZkSync Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through zksync bridge
/// ETH(Ethereum) => ETH(ZkSync Era)
contract ZkSyncL1Facet is Swapper, ReentrancyGuard {
    using SafeMath for uint256;

    /// Storage ///

    // keccak256("com.so.facets.zksync.l1")
    bytes32 internal constant NAMESPACE =
        hex"03e874f6bc55cf63253e86f34f708bf2253a89b5ebc53d7170d6178542bfe42e";

    uint256 internal constant RAY = 1e27;
    address internal constant NATIVE_ASSETID= address(0);
    address internal constant SPECIAL_ACCOUNT_ADDRESS = address(0xFFfFfFffFFfffFFfFFfFFFFFffFFFffffFfFFFfF);

    /// Type ///

    struct Storage {
        address zksync; // The zksync address
        uint256 soFee; // The so fee [RAY]
    }

    /// Events ///

    event ZkSync(address _zksync);
    event DepositToZkSync(address from, address zkSyncAddress, uint256 amount);

    /// Init ///

    /// @notice Initializes local variables for the zksync bridge
    /// @param zksync address of the zksync
    function initZkSync(address zksync) external {
        LibDiamond.enforceIsContractOwner();
        if (zksync == address(0)) revert InvalidConfig();

        require(!IZkSyncDeposit(zksync).exodusMode(), "InvalidZkSync");

        Storage storage s = getStorage();
        s.zksync = zksync;
        s.soFee = RAY / 1000; // 0.1 %

        emit ZkSync(zksync);
    }

    /// @notice Update local variables for the zksync bridge
    /// @param zksync address of the zksync
    function updateZkSync(address zksync) external {
        LibDiamond.enforceIsContractOwner();
        if (zksync == address(0)) revert InvalidConfig();

        require(!IZkSyncDeposit(zksync).exodusMode(), "InvalidZkSync");

        Storage storage s = getStorage();
        s.zksync = zksync;

        emit ZkSync(zksync);
    }

    /// @notice Update local variables for the zksync bridge
    /// @param soFee so fee [RAY]
    function setZkSyncSoFee(uint256 soFee) external {
        LibDiamond.enforceIsContractOwner();

        Storage storage s = getStorage();
        s.soFee = soFee;
    }

    /// External ///

    /// @notice Bridge ETH to ZkSync via ZkSync bridge
    /// @param swapDataSrcNo Contains a set of data required for Swap
    /// transactions on the source chain side
    /// Call on source chain by user
    function soSwapViaZkSyncL1(
        ISo.NormalizedSoData calldata soDataNo,
        LibSwap.NormalizedSwapData[] calldata swapDataSrcNo
    ) external payable nonReentrant {
        // decode soDataNo and swapDataSrcNo
        ISo.SoData memory soData = LibCross.denormalizeSoData(soDataNo);
        LibSwap.SwapData[] memory swapDataSrc = LibCross.denormalizeSwapData(
            swapDataSrcNo
        );

        uint256 bridgeAmount = 0;
        address bridgeToken = NATIVE_ASSETID;

        // deposit erc20 tokens to this contract
        if (!LibAsset.isNativeAsset(soData.sendingAssetId)) {
            LibAsset.depositAsset(soData.sendingAssetId, soData.amount);
            bridgeToken = soData.sendingAssetId;
        } else {
            require(msg.value >= soData.amount, "ValueErr");
        }

        // calculate bridgeAmount

        if (swapDataSrc.length == 0) {
            // direct bridge
            bridgeAmount = soData.amount;
        } else {
            // bridge after swap
            require(soData.amount == swapDataSrc[0].fromAmount, "AmountErr");
            try this.executeAndCheckSwaps(soData, swapDataSrc) returns (
                uint256 amount
            ) {
                bridgeToken = swapDataSrc[swapDataSrc.length - 1].receivingAssetId;
                bridgeAmount = amount;
            } catch (bytes memory lowLevelData) {
                // Rethrowing exception
                assembly {
                    let start := add(lowLevelData, 0x20)
                    let end := add(lowLevelData, mload(lowLevelData))
                    revert(start, end)
                }
            }
        }

        // unwrap to eth

        uint256 soFee = getZkSyncSoFee(bridgeAmount);
        if (soFee < bridgeAmount) {
            bridgeAmount = bridgeAmount.sub(soFee);
        }

        if (soFee > 0) {
            transferUnwrappedAsset(
                bridgeToken,
                NATIVE_ASSETID,
                soFee,
                LibDiamond.contractOwner()
            );
        }

        transferUnwrappedAsset(
            bridgeToken,
            NATIVE_ASSETID,
            bridgeAmount,
            address(this)
        );

        // zksync bridge
        startBridge(soData.receiver, bridgeAmount);
    }

    /// Public ///

    // calculate the so fee
    function getZkSyncSoFee(uint256 _amountIn) public view returns (uint256) {
        Storage storage s = getStorage();

        return _amountIn.mul(s.soFee).div(RAY);
    }

    // get zksync bridge config
    function getZkSyncConfig() public view returns (address, uint256) {
        Storage storage s = getStorage();

        return (address(s.zksync),s.soFee);
    }

    /// Private Methods ///

    /// @dev Conatains the business logic for the bridge via zksync
    function startBridge(
        address receiver,
        uint256 bridgeAmount
    ) private {
        Storage storage s = getStorage();

        // Zero-value deposits are forbidden by zkSync rollup logic
        require(bridgeAmount > 0, "ZeroValue");
        // exodus mode activated
        require(!IZkSyncDeposit(s.zksync).exodusMode(), "InActive");
        require(receiver != SPECIAL_ACCOUNT_ADDRESS, "InvalidAddress");

        IZkSyncDeposit(s.zksync).depositETH{value: bridgeAmount}(receiver);

        emit DepositToZkSync(msg.sender, receiver, bridgeAmount);
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