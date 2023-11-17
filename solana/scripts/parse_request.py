from solders.pubkey import Pubkey

from cross import WormholeData, SwapData, SoData

def parse_ix_data():
    DISCRIMINATOR = [60, 193, 132, 137, 201, 230, 23, 126]
    data = bytes.fromhex("3cc18489c9e6177e7800000020de38c01b9930178a3a67cef37a77c28b0000000065573e8c035f62f08c4f9c1714830fc068a182f647226cf990c92033e4e646e09a000a200000000000000000000000000000000000000000000000000000000000000000000314000000000000000000000000000000000000000000000000000f42407b0000000120f8f960f43c3b1aeabcc1e5655107583846b22cba9eb80ed93d3b3d406afddcf420069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f000000000012066e5188a1308a1db90b6d31f3fbdca8c3df2678c8112dfdd3d192c5a3cc457a800000000000f42400e576869726c706f6f6c2c323834313300000000040000000173eed8000000000002545323200000000000000000000000002967e7bb9daa5711ac332caf874bd47ef99b3820c40100000000000000000001000000000000001410ed43c718714eb63d5aa57b78b54704e256024e000000000000001410ed43c718714eb63d5aa57b78b54704e256024e00000000000000144db5a66e937a9f4473fa95b1caf1d1e1d62e29ea000000000000001400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000012418cbafe500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000d331a51257b200000000000000000000000000000000000000000000000000000000000000a00000000000000000000000002967e7bb9daa5711ac332caf874bd47ef99b3820000000000000000000000000000000000000000000000000000000006558900d00000000000000000000000000000000000000000000000000000000000000030000000000000000000000004db5a66e937a9f4473fa95b1caf1d1e1d62e29ea0000000000000000000000008ac76a51cc950d9822d68b83fe1ad97b32cd580d000000000000000000000000bb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")
    data_len = len(data)

    index = 0
    next_len = 8
    assert data[index:next_len] == bytes(DISCRIMINATOR)
    index += next_len

    next_len = 4
    so_data_len = int.from_bytes(data[index:index+next_len], "little", signed=False)
    print(f"so_data_len={so_data_len}")
    index += next_len
    so_data = SoData.decode_compact(data[index:index+so_data_len])
    print(f"so_data={so_data}")
    index += so_data_len

    next_len = 4
    swap_data_src_len = int.from_bytes(data[index:index+next_len], "little", signed=False)
    print(f"swap_data_src_len={swap_data_src_len}")
    index += next_len
    swap_data_src = SwapData.decode_compact_src(data[index:index+swap_data_src_len]) if swap_data_src_len > 0 else [None]
    print(f"swap_data_src={swap_data_src[0]}")
    index += swap_data_src_len

    next_len = 4
    wormhole_data_len = int.from_bytes(data[index:index+next_len], "little", signed=False)
    print(f"wormhole_data_len={wormhole_data_len}")
    index += next_len
    wormhole_data = WormholeData.decode_compact(data[index:index+wormhole_data_len])
    print(f"wormhole_data={wormhole_data}")
    index += wormhole_data_len

    next_len = 4
    swap_data_dst_len = int.from_bytes(data[index:index+next_len], "little", signed=False)
    print(f"swap_data_dst_len={swap_data_dst_len}")
    index += next_len
    swap_data_dst = SwapData.decode_normalized(data[index:index+swap_data_dst_len]) if swap_data_dst_len > 0 else [None]
    print(f"swap_data_dst={swap_data_dst}")
    index += swap_data_dst_len

    assert data_len == index, index

if __name__ == '__main__':
    parse_ix_data()

    print(Pubkey.from_bytes(bytes.fromhex("069b8857feab8184fb687f634618c035dac439dc1aeb3b5598a0f00000000001")))
    print(Pubkey.from_bytes(bytes.fromhex("66e5188a1308a1db90b6d31f3fbdca8c3df2678c8112dfdd3d192c5a3cc457a8")))
    print(Pubkey.from_bytes(bytes.fromhex("f8f960f43c3b1aeabcc1e5655107583846b22cba9eb80ed93d3b3d406afddcf4")))

    print(str(bytes.fromhex("576869726c706f6f6c2c32383431")))