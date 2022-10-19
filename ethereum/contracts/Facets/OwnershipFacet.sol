// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Libraries/LibDiamond.sol";
import "../Interfaces/IERC173.sol";

/// @title Ownership Facet
/// @notice Manages ownership of the So Diamond contract for admin purposes
contract OwnershipFacet is IERC173 {
    /// Storage ///

    bytes32 internal constant NAMESPACE =
        hex"cf2fba1a5c9c61959b11f2f1f88658271468c6fcc649cb2a6868473d3cd07f8b"; //keccak256("com.so.facets.ownership");
    struct Storage {
        address newOwner;
    }

    /// Errors ///

    error NoNullOwner();
    error NewOwnerMustNotBeSelf();
    error NoPendingOwnershipTransfer();
    error NotPendingOwner();

    /// Events ///

    event OwnershipTransferRequested(
        address indexed _from,
        address indexed _to
    );

    /// External Methods ///

    /// @notice Intitiates transfer of ownership to a new address
    /// @param newOwner the address to transfer ownership to
    function transferOwnership(address newOwner) external override {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        if (newOwner == address(0)) revert NoNullOwner();

        if (newOwner == LibDiamond.contractOwner())
            revert NewOwnerMustNotBeSelf();

        s.newOwner = newOwner;
        emit OwnershipTransferRequested(msg.sender, s.newOwner);
    }

    /// @notice Cancel transfer of ownership
    function cancelOnwershipTransfer() external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();

        if (s.newOwner == address(0)) revert NoPendingOwnershipTransfer();
        s.newOwner = address(0);
    }

    /// @notice Confirms transfer of ownership to the calling address (msg.sender)
    function confirmOwnershipTransfer() external {
        Storage storage s = getStorage();
        if (msg.sender != s.newOwner) revert NotPendingOwner();
        LibDiamond.setContractOwner(s.newOwner);
        s.newOwner = address(0);
        emit OwnershipTransferred(LibDiamond.contractOwner(), s.newOwner);
    }

    /// @notice Return the current owner address
    /// @return contractOwner The current owner address
    function owner() external view override returns (address contractOwner) {
        contractOwner = LibDiamond.contractOwner();
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
