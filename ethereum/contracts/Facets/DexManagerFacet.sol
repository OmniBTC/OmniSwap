// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Libraries/LibStorage.sol";
import "../Libraries/LibDiamond.sol";
import {InvalidConfig} from "../Errors/GenericErrors.sol";

/// @title Dex Manager Facet
/// @notice Facet contract for managing approved DEXs to be used in swaps.
contract DexManagerFacet {
    /// Events ///

    event DexAdded(address indexed dexAddress);
    event DexRemoved(address indexed dexAddress);
    event FunctionSignatureApprovalChanged(
        bytes32 indexed functionSignature,
        bool indexed approved
    );
    event GatewaySoFeeSelectorsChanged(
        address indexed gatewayAddress,
        address indexed soFeeAddress
    );
    event CorrectSwapRouterSelectorsChanged(address indexed correctSwap);

    /// Storage ///

    LibStorage internal appStorage;

    /// External Methods ///

    /// @notice  Register the soFee address for facet.
    /// @param gateway The address of the gateway facet address.
    /// @param soFee The address of soFee address.
    function addFee(address gateway, address soFee) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => address) storage gatewaySoFeeSelectors = appStorage
            .gatewaySoFeeSelectors;
        gatewaySoFeeSelectors[gateway] = soFee;
        emit GatewaySoFeeSelectorsChanged(gateway, soFee);
    }

    /// @notice Register the correct swap impl address for different swap router
    /// @param correctSwap address that implement the modification of this swap
    function addCorrectSwap(address correctSwap) external {
        LibDiamond.enforceIsContractOwner();
        appStorage.correctSwapRouterSelectors = correctSwap;
        emit CorrectSwapRouterSelectorsChanged(correctSwap);
    }

    /// @notice Register the address of a DEX contract to be approved for swapping.
    /// @param dex The address of the DEX contract to be approved.
    function addDex(address dex) external {
        LibDiamond.enforceIsContractOwner();
        _checkAddress(dex);

        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        if (dexAllowlist[dex]) return;

        dexAllowlist[dex] = true;
        appStorage.dexs.push(dex);
        emit DexAdded(dex);
    }

    /// @notice Batch register the addresss of DEX contracts to be approved for swapping.
    /// @param dexs The addresses of the DEX contracts to be approved.
    function batchAddDex(address[] calldata dexs) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        uint256 length = dexs.length;

        for (uint256 i = 0; i < length; i++) {
            _checkAddress(dexs[i]);
            if (dexAllowlist[dexs[i]]) continue;
            dexAllowlist[dexs[i]] = true;
            appStorage.dexs.push(dexs[i]);
            emit DexAdded(dexs[i]);
        }
    }

    /// @notice Unregister the address of a DEX contract approved for swapping.
    /// @param dex The address of the DEX contract to be unregistered.
    function removeDex(address dex) external {
        LibDiamond.enforceIsContractOwner();
        _checkAddress(dex);

        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        address[] storage storageDexes = appStorage.dexs;

        if (!dexAllowlist[dex]) {
            return;
        }
        dexAllowlist[dex] = false;

        uint256 length = storageDexes.length;
        for (uint256 i = 0; i < length; i++) {
            if (storageDexes[i] == dex) {
                _removeDex(i);
                return;
            }
        }
    }

    /// @notice Batch unregister the addresses of DEX contracts approved for swapping.
    /// @param dexs The addresses of the DEX contracts to be unregistered.
    function batchRemoveDex(address[] calldata dexs) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        address[] storage storageDexes = appStorage.dexs;

        uint256 ilength = dexs.length;
        uint256 jlength = storageDexes.length;
        for (uint256 i = 0; i < ilength; i++) {
            _checkAddress(dexs[i]);
            if (!dexAllowlist[dexs[i]]) {
                continue;
            }
            dexAllowlist[dexs[i]] = false;
            for (uint256 j = 0; j < jlength; j++) {
                if (storageDexes[j] == dexs[i]) {
                    _removeDex(j);
                    jlength = storageDexes.length;
                    break;
                }
            }
        }
    }

    /// @notice Adds/removes a specific function signature to/from the allowlist
    /// @param signature the function signature to allow/disallow
    /// @param approval whether the function signature should be allowed
    function setFunctionApprovalBySignature(bytes32 signature, bool approval)
        external
    {
        LibDiamond.enforceIsContractOwner();
        appStorage.dexFuncSignatureAllowList[signature] = approval;
        emit FunctionSignatureApprovalChanged(signature, approval);
    }

    /// @notice Batch Adds/removes a specific function signature to/from the allowlist
    /// @param signatures the function signatures to allow/disallow
    /// @param approval whether the function signatures should be allowed
    function batchSetFunctionApprovalBySignature(
        bytes32[] calldata signatures,
        bool approval
    ) external {
        LibDiamond.enforceIsContractOwner();
        mapping(bytes32 => bool) storage dexFuncSignatureAllowList = appStorage
            .dexFuncSignatureAllowList;
        uint256 length = signatures.length;
        for (uint256 i = 0; i < length; i++) {
            bytes32 signature = signatures[i];
            dexFuncSignatureAllowList[signature] = approval;
            emit FunctionSignatureApprovalChanged(signature, approval);
        }
    }

    /// @notice Returns whether a function signature is approved
    /// @param signature the function signature to query
    /// @return approved Approved or not
    function isFunctionApproved(bytes32 signature)
        public
        view
        returns (bool approved)
    {
        return appStorage.dexFuncSignatureAllowList[signature];
    }

    /// @notice Returns a list of all approved DEX addresses.
    /// @return addresses List of approved DEX addresses
    function approvedDexs() external view returns (address[] memory addresses) {
        return appStorage.dexs;
    }

    /// Private Methods ///

    /// @dev Contains business logic for removing a DEX address.
    /// @param index index of the dex to remove
    function _removeDex(uint256 index) private {
        address[] storage storageDexes = appStorage.dexs;
        address toRemove = storageDexes[index];
        // Move the last element into the place to delete
        storageDexes[index] = storageDexes[storageDexes.length - 1];
        // Remove the last element
        storageDexes.pop();
        emit DexRemoved(toRemove);
    }

    /// @dev Contains business logic for validating a DEX address.
    /// @param dex address of the dex to check
    function _checkAddress(address dex) private pure {
        if (dex == 0x0000000000000000000000000000000000000000) {
            revert InvalidConfig();
        }
    }
}
