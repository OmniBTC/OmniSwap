// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

interface IConnext {
    // ============= Structs =============

    // Tokens are identified by a TokenId:
    // domain - 4 byte chain ID of the chain from which the token originates
    // id - 32 byte identifier of the token address on the origin chain, in that chain's address format
    struct TokenId {
        uint32 domain;
        bytes32 id;
    }

    /**
     * @notice Enum representing status of destination transfer
     * @dev Status is only assigned on the destination domain, will always be "none" for the
     * origin domains
     * @return uint - Index of value in enum
     */
    enum DestinationTransferStatus {
        None, // 0
        Reconciled, // 1
        Executed, // 2
        Completed // 3 - executed + reconciled
    }

    /**
     * @notice These are the parameters that will remain constant between the
     * two chains. They are supplied on `xcall` and should be asserted on `execute`
     * @property to - The account that receives funds, in the event of a crosschain call,
     * will receive funds if the call fails.
     *
     * @param originDomain - The originating domain (i.e. where `xcall` is called)
     * @param destinationDomain - The final domain (i.e. where `execute` / `reconcile` are called)\
     * @param canonicalDomain - The canonical domain of the asset you are bridging
     * @param to - The address you are sending funds (and potentially data) to
     * @param delegate - An address who can execute txs on behalf of `to`, in addition to allowing relayers
     * @param receiveLocal - If true, will use the local asset on the destination instead of adopted.
     * @param callData - The data to execute on the receiving chain. If no crosschain call is needed, then leave empty.
     * @param slippage - Slippage user is willing to accept from original amount in expressed in BPS (i.e. if
     * a user takes 1% slippage, this is expressed as 1_000)
     * @param originSender - The msg.sender of the xcall
     * @param bridgedAmt - The amount sent over the bridge (after potential AMM on xcall)
     * @param normalizedIn - The amount sent to `xcall`, normalized to 18 decimals
     * @param nonce - The nonce on the origin domain used to ensure the transferIds are unique
     * @param canonicalId - The unique identifier of the canonical token corresponding to bridge assets
     */
    struct TransferInfo {
        uint32 originDomain;
        uint32 destinationDomain;
        uint32 canonicalDomain;
        address to;
        address delegate;
        bool receiveLocal;
        bytes callData;
        uint256 slippage;
        address originSender;
        uint256 bridgedAmt;
        uint256 normalizedIn;
        uint256 nonce;
        bytes32 canonicalId;
    }

    /**
     * @notice
     * @param params - The TransferInfo. These are consistent across sending and receiving chains.
     * @param routers - The routers who you are sending the funds on behalf of.
     * @param routerSignatures - Signatures belonging to the routers indicating permission to use funds
     * for the signed transfer ID.
     * @param sequencer - The sequencer who assigned the router path to this transfer.
     * @param sequencerSignature - Signature produced by the sequencer for path assignment accountability
     * for the path that was signed.
     */
    struct ExecuteArgs {
        TransferInfo params;
        address[] routers;
        bytes[] routerSignatures;
        address sequencer;
        bytes sequencerSignature;
    }

    // ============ BRIDGE ==============

    function xcall(
        uint32 _destination,
        address _to,
        address _asset,
        address _delegate,
        uint256 _amount,
        uint256 _slippage,
        bytes calldata _callData
    ) external payable returns (bytes32);

    function xcall(
        uint32 _destination,
        address _to,
        address _asset,
        address _delegate,
        uint256 _amount,
        uint256 _slippage,
        bytes calldata _callData,
        uint256 _relayerFee
    ) external returns (bytes32);

    function xcallIntoLocal(
        uint32 _destination,
        address _to,
        address _asset,
        address _delegate,
        uint256 _amount,
        uint256 _slippage,
        bytes calldata _callData
    ) external payable returns (bytes32);

    function xcallIntoLocal(
        uint32 _destination,
        address _to,
        address _asset,
        address _delegate,
        uint256 _amount,
        uint256 _slippage,
        bytes calldata _callData,
        uint256 _relayerFee
    ) external returns (bytes32);

    function execute(
        ExecuteArgs calldata _args
    ) external returns (bytes32 transferId);

    function forceUpdateSlippage(
        TransferInfo calldata _params,
        uint256 _slippage
    ) external;

    function forceReceiveLocal(TransferInfo calldata _params) external;

    function bumpTransfer(bytes32 _transferId) external payable;

    function routedTransfers(
        bytes32 _transferId
    ) external view returns (address[] memory);

    function transferStatus(
        bytes32 _transferId
    ) external view returns (DestinationTransferStatus);

    function remote(uint32 _domain) external view returns (address);

    function domain() external view returns (uint256);

    function nonce() external view returns (uint256);

    function approvedSequencers(
        address _sequencer
    ) external view returns (bool);

    function xAppConnectionManager() external view returns (address);

    // ============ ROUTERS ==============

    function LIQUIDITY_FEE_NUMERATOR() external view returns (uint256);

    function LIQUIDITY_FEE_DENOMINATOR() external view returns (uint256);

    function getRouterApproval(address _router) external view returns (bool);

    function getRouterRecipient(
        address _router
    ) external view returns (address);

    function getRouterOwner(address _router) external view returns (address);

    function getProposedRouterOwner(
        address _router
    ) external view returns (address);

    function getProposedRouterOwnerTimestamp(
        address _router
    ) external view returns (uint256);

    function maxRoutersPerTransfer() external view returns (uint256);

    function routerBalances(
        address _router,
        address _asset
    ) external view returns (uint256);

    function getRouterApprovalForPortal(
        address _router
    ) external view returns (bool);

    function initializeRouter(address _owner, address _recipient) external;

    function setRouterRecipient(address _router, address _recipient) external;

    function proposeRouterOwner(address _router, address _proposed) external;

    function acceptProposedRouterOwner(address _router) external;

    function addRouterLiquidityFor(
        uint256 _amount,
        address _local,
        address _router
    ) external payable;

    function addRouterLiquidity(
        uint256 _amount,
        address _local
    ) external payable;

    function removeRouterLiquidityFor(
        TokenId memory _canonical,
        uint256 _amount,
        address payable _to,
        address _router
    ) external;

    function removeRouterLiquidity(
        TokenId memory _canonical,
        uint256 _amount,
        address payable _to
    ) external;

    // ============ TOKEN_FACET ==============
    function adoptedToCanonical(
        address _adopted
    ) external view returns (TokenId memory);

    function approvedAssets(
        TokenId calldata _canonical
    ) external view returns (bool);
}
