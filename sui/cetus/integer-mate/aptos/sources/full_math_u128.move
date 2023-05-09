module integer_mate::full_math_u128 {
    use integer_mate::u256;
    use integer_mate::math_u128;

    public fun mul_div_floor(num1: u128, num2: u128, denom: u128): u128 {
        let r = full_mul_v2(num1, num2) / (denom as u256);
        (r as u128)
    }

    public fun mul_div_round(num1: u128, num2: u128, denom: u128): u128 {
        let r = (full_mul_v2(num1, num2) + ((denom as u256) >> 1)) / (denom as u256);
        (r as u128)
    }

    public fun mul_div_ceil(num1: u128, num2: u128, denom: u128): u128 {
        let r = (full_mul_v2(num1, num2) + ((denom as u256) - 1)) / (denom as u256);
        (r as u128)
    }

    public fun mul_shr(num1: u128, num2: u128, shift: u8): u128 {
        let product = full_mul_v2(num1, num2) >> shift;
        (product as u128)
    }

    public fun mul_shl(num1: u128, num2: u128, shift: u8): u128 {
        let product = full_mul_v2(num1, num2) << shift;
        (product as u128)
    }

    public fun full_mul(num1: u128, num2: u128): u256::U256 {
        let (lo, hi) = math_u128::full_mul(num1, num2);
        u256::new(
            math_u128::lo(lo),
            math_u128::hi(lo),
            math_u128::lo(hi),
            math_u128::hi(hi),
        )
    }

    public fun full_mul_v2(num1: u128, num2: u128): u256 {
        (num1 as u256) * (num2 as u256)
    }

}
