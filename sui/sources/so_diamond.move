module omniswap::so_diamond {

    use omniswap::wormhole_facet;

    /// Cross-swap via wormhole
    ///  * so_data Track user data across the chain and record the final destination of tokens
    ///  * swap_data_src Swap data at source chain
    ///  * wormhole_data Data needed to use the wormhole cross-link bridge
    ///  * swap_data_dst Swap data at destination chain
    ///
    /// The parameters passed in are serialized.
    public entry fun so_swap_via_wormhole<X, Y, Z, M>(
        account: &signer,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>
    ) {
        wormhole_facet::so_swap<X, Y, Z, M>(account, so_data, swap_data_src, wormhole_data, swap_data_dst);
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap<X, Y, Z, M>(vaa: vector<u8>) {
        wormhole_facet::complete_so_swap<X, Y, Z, M>(vaa);
    }

    /// To complete a cross-chain transaction, it needs to be called manually by the
    /// user or automatically by Relayer for the tokens to be sent to the user.
    public entry fun complete_so_swap_by_account<X, Y, Z, M>(account: &signer, vaa: vector<u8>) {
        wormhole_facet::complete_so_swap_by_account<X, Y, Z, M>(account, vaa);
    }
}
