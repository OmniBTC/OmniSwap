// SPDX-License-Identifier: GPLv3
pragma solidity 0.8.13;

import "../Libraries/LibDiamond.sol";
import "../Interfaces/ISo.sol";
import "../Helpers/Swapper.sol";

/// @title Wormhole Facet
/// @author OmniBTC
/// @notice Provides functionality for bridging through Wormhole
contract WormholeFacet {
    bytes32 internal constant NAMESPACE =
        hex"5cf8a649899e43a2530442580fb1a9721870a3fa10790c9ef200c611cab819d4"; // keccak256("com.omnibtc.facets.wormhole")

    struct Storage {
        address tokenBridge;
        uint16 wormholeChainId;
    }

    /// Events ///

    event InitWormholeEvent(address tokenBridge, uint16 wormholeChainId);

    /// Types ///
    struct WormholeData {
        address token;
        uint256 amount;
        uint16 recipientChain;
        bytes32 recipient;
        uint32 nonce;
        bytes payload;
    }

    /// Init ///

    /// init wormhole token bridge
    function initWormholeTokenBridge(
        address _tokenBridge,
        uint16 _wormholeChainId
    ) external {
        LibDiamond.enforceIsContractOwner();
        Storage storage s = getStorage();
        s.tokenBridge = _tokenBridge;
        s.wormholeChainId = _wormholeChainId;
        emit InitWormholeEvent(_tokenBridge, _wormholeChainId);
    }

    /// External Methods ///

    /// transfer with payload
    function omniswapViaWormhole(
        ISo.SoData calldata _soData,
        LibSwap.SwapData[] calldata _swapDataSrc,
        WormholeData calldata _wormholeData,
        LibSwap.SwapData[] calldata _swapDataDst
    ) external payable {
        // todo
    }

    /// complete transfer with payload
    /// called by relayer
    function completeSwap() external {
        // todo
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
