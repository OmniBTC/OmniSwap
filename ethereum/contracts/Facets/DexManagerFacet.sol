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
    event CorrectSwapRouterSelectorsChanged(
        address indexed correctSwap
    );

    /// Storage ///

    LibStorage internal appStorage;

    /// External Methods ///

    /// @notice  Register the soFee address for facet.
    /// @param _gateway The address of the gateway facet address.
    /// @param _soFee The address of soFee address.
    function addFee(address _gateway, address _soFee) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => address) storage gatewaySoFeeSelectors = appStorage
            .gatewaySoFeeSelectors;
        gatewaySoFeeSelectors[_gateway] = _soFee;
        emit GatewaySoFeeSelectorsChanged(_gateway, _soFee);
    }

    /// @notice Register the correct swap impl address for different swap router
    /// @param _correctSwap address that implement the modification of this swap
    function addCorrectSwap(address _correctSwap)
        external
    {
        LibDiamond.enforceIsContractOwner();
        appStorage.correctSwapRouterSelectors = _correctSwap;
        emit CorrectSwapRouterSelectorsChanged(_correctSwap);
    }

    /// @notice Register the address of a DEX contract to be approved for swapping.
    /// @param _dex The address of the DEX contract to be approved.
    function addDex(address _dex) external {
        LibDiamond.enforceIsContractOwner();
        _checkAddress(_dex);

        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        if (dexAllowlist[_dex]) return;

        dexAllowlist[_dex] = true;
        appStorage.dexs.push(_dex);
        emit DexAdded(_dex);
    }

    /// @notice Batch register the addresss of DEX contracts to be approved for swapping.
    /// @param _dexs The addresses of the DEX contracts to be approved.
    function batchAddDex(address[] calldata _dexs) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        uint256 length = _dexs.length;

        for (uint256 i = 0; i < length; i++) {
            _checkAddress(_dexs[i]);
            if (dexAllowlist[_dexs[i]]) continue;
            dexAllowlist[_dexs[i]] = true;
            appStorage.dexs.push(_dexs[i]);
            emit DexAdded(_dexs[i]);
        }
    }

    /// @notice Unregister the address of a DEX contract approved for swapping.
    /// @param _dex The address of the DEX contract to be unregistered.
    function removeDex(address _dex) external {
        LibDiamond.enforceIsContractOwner();
        _checkAddress(_dex);

        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        address[] storage storageDexes = appStorage.dexs;

        if (!dexAllowlist[_dex]) {
            return;
        }
        dexAllowlist[_dex] = false;

        uint256 length = storageDexes.length;
        for (uint256 i = 0; i < length; i++) {
            if (storageDexes[i] == _dex) {
                _removeDex(i);
                return;
            }
        }
    }

    /// @notice Batch unregister the addresses of DEX contracts approved for swapping.
    /// @param _dexs The addresses of the DEX contracts to be unregistered.
    function batchRemoveDex(address[] calldata _dexs) external {
        LibDiamond.enforceIsContractOwner();
        mapping(address => bool) storage dexAllowlist = appStorage.dexAllowlist;
        address[] storage storageDexes = appStorage.dexs;

        uint256 ilength = _dexs.length;
        uint256 jlength = storageDexes.length;
        for (uint256 i = 0; i < ilength; i++) {
            _checkAddress(_dexs[i]);
            if (!dexAllowlist[_dexs[i]]) {
                continue;
            }
            dexAllowlist[_dexs[i]] = false;
            for (uint256 j = 0; j < jlength; j++) {
                if (storageDexes[j] == _dexs[i]) {
                    _removeDex(j);
                    jlength = storageDexes.length;
                    break;
                }
            }
        }
    }

    /// @notice Adds/removes a specific function signature to/from the allowlist
    /// @param _signature the function signature to allow/disallow
    /// @param _approval whether the function signature should be allowed
    function setFunctionApprovalBySignature(bytes32 _signature, bool _approval)
        external
    {
        LibDiamond.enforceIsContractOwner();
        appStorage.dexFuncSignatureAllowList[_signature] = _approval;
        emit FunctionSignatureApprovalChanged(_signature, _approval);
    }

    /// @notice Batch Adds/removes a specific function signature to/from the allowlist
    /// @param _signatures the function signatures to allow/disallow
    /// @param _approval whether the function signatures should be allowed
    function batchSetFunctionApprovalBySignature(
        bytes32[] calldata _signatures,
        bool _approval
    ) external {
        LibDiamond.enforceIsContractOwner();
        mapping(bytes32 => bool) storage dexFuncSignatureAllowList = appStorage
            .dexFuncSignatureAllowList;
        uint256 length = _signatures.length;
        for (uint256 i = 0; i < length; i++) {
            bytes32 _signature = _signatures[i];
            dexFuncSignatureAllowList[_signature] = _approval;
            emit FunctionSignatureApprovalChanged(_signature, _approval);
        }
    }

    /// @notice Returns whether a function signature is approved
    /// @param _signature the function signature to query
    /// @return approved Approved or not
    function isFunctionApproved(bytes32 _signature)
        public
        view
        returns (bool approved)
    {
        return appStorage.dexFuncSignatureAllowList[_signature];
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
    /// @param _dex address of the dex to check
    function _checkAddress(address _dex) private pure {
        if (_dex == 0x0000000000000000000000000000000000000000) {
            revert InvalidConfig();
        }
    }
}
