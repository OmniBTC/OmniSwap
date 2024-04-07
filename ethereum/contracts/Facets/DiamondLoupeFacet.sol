// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

import "../Libraries/LibDiamond.sol";
import "../Interfaces/IDiamondLoupe.sol";
import "../Interfaces/IERC165.sol";

contract DiamondLoupeFacet is IDiamondLoupe, IERC165 {
    /// @notice Gets all facets and their selectors.
    /// @return allFacets Facet
    function facets()
        external
        view
        override
        returns (Facet[] memory allFacets)
    {
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        uint256 numFacets = ds.facetAddresses.length;
        allFacets = new Facet[](numFacets);
        for (uint256 i = 0; i < numFacets; i++) {
            address facetAddress_ = ds.facetAddresses[i];
            allFacets[i].facetAddress = facetAddress_;
            allFacets[i].functionSelectors = ds
                .facetFunctionSelectors[facetAddress_]
                .functionSelectors;
        }
    }

    /// @notice Gets all the function selectors provided by a facet.
    /// @param facet The facet address.
    /// @return facetFunctionSelectors_
    function facetFunctionSelectors(
        address facet
    ) external view override returns (bytes4[] memory facetFunctionSelectors_) {
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        facetFunctionSelectors_ = ds
            .facetFunctionSelectors[facet]
            .functionSelectors;
    }

    /// @notice Get all the facet addresses used by a diamond.
    /// @return addresses
    function facetAddresses()
        external
        view
        override
        returns (address[] memory addresses)
    {
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        addresses = ds.facetAddresses;
    }

    /// @notice Gets the facet that supports the given selector.
    /// @dev If facet is not found return address(0).
    /// @param functionSelector The function selector.
    /// @return addresses The facet address.
    function facetAddress(
        bytes4 functionSelector
    ) external view override returns (address addresses) {
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        addresses = ds
            .selectorToFacetAndPosition[functionSelector]
            .facetAddress;
    }

    // This implements ERC-165.
    function supportsInterface(
        bytes4 interfaceId
    ) external view override returns (bool) {
        LibDiamond.DiamondStorage storage ds = LibDiamond.diamondStorage();
        return ds.supportedInterfaces[interfaceId];
    }
}
