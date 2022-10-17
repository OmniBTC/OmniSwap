module omniswap::so_diamond {

    use omniswap::wormhole_facet;

    public entry fun so_swap_via_wormhole<X, Y, Z, M>(
        account: &signer,
        so_data: vector<u8>,
        swap_data_src: vector<u8>,
        wormhole_data: vector<u8>,
        swap_data_dst: vector<u8>
    ) {
        wormhole_facet::so_swap<X, Y, Z, M>(account, so_data, swap_data_src, wormhole_data, swap_data_dst);
    }

    public entry fun complete_so_swap<X, Y, Z, M>(vaa: vector<u8>) {
        wormhole_facet::complete_so_swap<X, Y, Z, M>(vaa);
    }
}
