// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Interfaces/IDiamondCut.sol";
import "../Libraries/LibDiamond.sol";

contract DiamondCutFacet is IDiamondCut {
    /// @notice Add/replace/remove any number of functions and optionally execute
    ///         a function with delegatecall
    /// @param facetCut Contains the facet addresses and function selectors
    /// @param init The address of the contract or facet to execute calldata
    /// @param callData A function call, including function selector and arguments
    ///                  calldata is executed with delegatecall on init
    function diamondCut(
        FacetCut[] calldata facetCut,
        address init,
        bytes calldata callData
    ) external override {
        LibDiamond.enforceIsContractOwner();
        LibDiamond.diamondCut(facetCut, init, callData);
    }
}
