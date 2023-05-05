module cetus_clmm::tick {
    use move_stl::skip_list::SkipList;
    use integer_mate::i32::I32;
    use integer_mate::i128::I128;

    struct TickManager has store {
        tick_spacing: u32,
        ticks: SkipList<Tick>
    }

    struct Tick has copy, drop, store {
        index: I32,
        sqrt_price: u128,
        liquidity_net: I128,
        liquidity_gross: u128,
        fee_growth_outside_a: u128,
        fee_growth_outside_b: u128,
        points_growth_outside: u128,
        rewards_growth_outside: vector<u128>,
    }
}