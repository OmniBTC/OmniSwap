// SPDX-License-Identifier: BUSL-1.1

pragma solidity 0.8.13;

interface IStargatePool {
    //---------------------------------------------------------------------------
    // STRUCTS
    struct ChainPath {
        bool ready; // indicate if the counter chainPath has been created.
        uint16 dstChainId;
        uint256 dstPoolId;
        uint256 weight;
        uint256 balance;
        uint256 lkb;
        uint256 credits;
        uint256 idealBalance;
    }

    struct SwapObj {
        uint256 amount;
        uint256 eqFee;
        uint256 eqReward;
        uint256 lpFee;
        uint256 protocolFee;
        uint256 lkbRemove;
    }

    //---------------------------------------------------------------------------
    // EVENTS
    event Mint(
        address to,
        uint256 amountLP,
        uint256 amountSD,
        uint256 mintFeeAmountSD
    );
    event Burn(address from, uint256 amountLP, uint256 amountSD);
    event RedeemLocalCallback(
        address _to,
        uint256 _amountSD,
        uint256 _amountToMintSD
    );
    event Swap(
        uint16 chainId,
        uint256 dstPoolId,
        address from,
        uint256 amountSD,
        uint256 eqReward,
        uint256 eqFee,
        uint256 protocolFee,
        uint256 lpFee
    );
    event SendCredits(
        uint16 dstChainId,
        uint256 dstPoolId,
        uint256 credits,
        uint256 idealBalance
    );
    event RedeemRemote(
        uint16 chainId,
        uint256 dstPoolId,
        address from,
        uint256 amountLP,
        uint256 amountSD
    );
    event RedeemLocal(
        address from,
        uint256 amountLP,
        uint256 amountSD,
        uint16 chainId,
        uint256 dstPoolId,
        bytes to
    );
    event InstantRedeemLocal(
        address from,
        uint256 amountLP,
        uint256 amountSD,
        address to
    );
    event CreditChainPath(
        uint16 chainId,
        uint256 srcPoolId,
        uint256 amountSD,
        uint256 idealBalance
    );
    event SwapRemote(
        address to,
        uint256 amountSD,
        uint256 protocolFee,
        uint256 dstFee
    );
    event WithdrawRemote(
        uint16 srcChainId,
        uint256 srcPoolId,
        uint256 swapAmount,
        uint256 mintAmount
    );
    event ChainPathUpdate(uint16 dstChainId, uint256 dstPoolId, uint256 weight);
    event FeesUpdated(uint256 mintFeeBP);
    event FeeLibraryUpdated(address feeLibraryAddr);
    event StopSwapUpdated(bool swapStop);
    event WithdrawProtocolFeeBalance(address to, uint256 amountSD);
    event WithdrawMintFeeBalance(address to, uint256 amountSD);
    event DeltaParamUpdated(
        bool batched,
        uint256 swapDeltaBP,
        uint256 lpDeltaBP,
        bool defaultSwapMode,
        bool defaultLPMode
    );

    function chainPaths(uint256 index) external view returns (ChainPath memory);

    function getChainPathsLength() external view returns (uint256);

    function getChainPath(
        uint16 _dstChainId,
        uint256 _dstPoolId
    ) external view returns (ChainPath memory);

    function convertRate() external view returns (uint256);

    function token() external view returns (address);

    function feeLibrary() external view returns (address);

    function poolId() external view returns (uint256);
}
