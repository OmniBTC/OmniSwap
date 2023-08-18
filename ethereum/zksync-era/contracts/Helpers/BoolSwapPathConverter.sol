// SPDX-License-Identifier: MIT
pragma solidity 0.8.13;

abstract contract BoolSwapPathConverter {
    event PathPairUpdated(
        uint32 indexed consumerChainId,
        uint32 indexed boolChainId
    );

    mapping(uint32 => uint32) private _fromCToB;
    mapping(uint32 => uint32) private _fromBToC;

    function fromConsumerToBool(uint32 consumerChainId)
        external
        view
        returns (uint32 boolChainId)
    {}

    function fromBoolToConsumer(uint32 boolChainId)
        external
        view
        returns (uint32 consumerChainId)
    {}

    /** Permission Required Functions (should override this) */
    function updatePathPair(
        uint32[] calldata consumerChainIds,
        uint32[] calldata boolChainIds
    ) external virtual {
        require(
            consumerChainIds.length == boolChainIds.length,
            "LENGTH_MISSMATCH"
        );
        for (uint256 i = 0; i < consumerChainIds.length; i++) {
            _fromCToB[consumerChainIds[i]] = boolChainIds[i];
            _fromBToC[boolChainIds[i]] = consumerChainIds[i];
        }
    }
}
