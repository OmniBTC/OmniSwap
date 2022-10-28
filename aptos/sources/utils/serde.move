module omniswap::serde {
    use std::bcs;
    use std::error;
    use std::string;
    use std::vector;

    use omniswap::u16::{U16, Self};
    use omniswap::u256::{U256, Self};

    use aptos_std::type_info;

    use aptos_framework::util;

    const EINVALID_LENGTH: u64 = 0x00;

    const OVERFLOW: u64 = 0x01;

    const U64_MAX: u64 = 0xFFFFFFFFFFFFFFFF;

    const U128_MAX: u128 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;

    public fun serialize_u8(buf: &mut vector<u8>, v: u8) {
        vector::push_back(buf, v);
    }

    public fun serialize_u16(buf: &mut vector<u8>, v: U16) {
        let v = u16::to_u64(v);
        assert!(v <= 65535, error::invalid_argument(EINVALID_LENGTH));
        serialize_u8(buf, (((v >> 8) & 0xFF) as u8));
        serialize_u8(buf, ((v & 0xFF) as u8));
    }

    public fun serialize_u64(buf: &mut vector<u8>, v: u64) {
        serialize_u8(buf, (((v >> 56) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 48) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 40) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 32) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 24) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 16) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8) & 0xFF) as u8));
        serialize_u8(buf, ((v & 0xFF) as u8));
    }

    public fun serialize_u128(buf: &mut vector<u8>, v: u128) {
        serialize_u8(buf, (((v >> 120) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 112) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 104) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 96) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 88) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 80) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 72) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 64) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 56) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 48) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 40) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 32) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 24) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 16) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8) & 0xFF) as u8));
        serialize_u8(buf, ((v & 0xFF) as u8));
    }

    public fun serialize_u256(buf: &mut vector<u8>, v: U256) {
        let v0 = u256::shr(v, 128);
        serialize_u128(buf, u256::as_u128(v0));
        serialize_u128(buf, u256::as_truncate_u128(v));
    }

    // [0, 9] --> ['0', '9']
    // [10, 15] --> ['a', 'f']
    public fun hex_str_to_ascii(v: u8): u8 {
        if (v >= 0 && v <= 9) {
            v + 48
        }else if (v <= 15) {
            v + 87
        }else {
            abort OVERFLOW
        }
    }

    // ['0', '9'] --> [0, 9]
    // ['a', 'f'] --> [10, 15]
    public fun ascii_to_hex_str(v: u8): u8 {
        if (v >= 48 && v <= 57) {
            v - 48
        }else if (v >= 97 && v <= 102) {
            v - 87
        }else {
            abort OVERFLOW
        }
    }

    public fun serialize_u128_with_hex_str(buf: &mut vector<u8>, v: u128) {
        let data = vector::empty<u8>();
        serialize_u8(&mut data, ((v & 0xFF) as u8));
        let d = (v >> 8);
        while (d != 0) {
            serialize_u8(&mut data, ((d & 0xFF) as u8));
            d = d >> 8;
        };
        vector::reverse(&mut data);
        vector::append(buf, data);
    }

    public fun serialize_u256_with_hex_str(buf: &mut vector<u8>, v: U256) {
        let v0 = u256::shr(v, 128);
        if (v0 != u256::zero()) {
            serialize_u128_with_hex_str(buf, u256::as_u128(v0));
            serialize_u128(buf, u256::as_truncate_u128(v));
        }else {
            serialize_u128_with_hex_str(buf, u256::as_truncate_u128(v));
        }
    }

    public fun serialize_vector(buf: &mut vector<u8>, v: vector<u8>) {
        vector::append(buf, v);
    }

    public fun serialize_address(buf: &mut vector<u8>, v: address) {
        let data = bcs::to_bytes(&v);
        assert!(vector::length(&data) == 32, error::invalid_argument(EINVALID_LENGTH));
        vector::append(buf, data);
    }

    public fun serialize_type<T>(buf: &mut vector<u8>) {
        serialize_vector(buf, *string::bytes(&type_info::type_name<T>()));
    }

    public fun serialize_vector_with_length(buf: &mut vector<u8>, v: vector<u8>) {
        let len = vector::length(&v);
        if (len == 0) {
            return
        };
        serialize_u64(buf, len);
        serialize_vector(buf, v);
    }

    public fun deserialize_u8(buf: &vector<u8>): u8 {
        assert!(vector::length(buf) == 1, error::invalid_argument(EINVALID_LENGTH));
        *vector::borrow(buf, 0)
    }

    public fun deserialize_u16(buf: &vector<u8>): U16 {
        assert!(vector::length(buf) == 2, error::invalid_argument(EINVALID_LENGTH));
        let v = ((*vector::borrow(buf, 0) as u64) << 8) + (*vector::borrow(buf, 1) as u64);
        u16::from_u64(v)
    }

    public fun deserialize_u64(buf: &vector<u8>): u64 {
        assert!(vector::length(buf) == 8, error::invalid_argument(EINVALID_LENGTH));
        ((*vector::borrow(buf, 0) as u64) << 56)
            + ((*vector::borrow(buf, 1) as u64) << 48)
            + ((*vector::borrow(buf, 2) as u64) << 40)
            + ((*vector::borrow(buf, 3) as u64) << 32)
            + ((*vector::borrow(buf, 4) as u64) << 24)
            + ((*vector::borrow(buf, 5) as u64) << 16)
            + ((*vector::borrow(buf, 6) as u64) << 8)
            + (*vector::borrow(buf, 7) as u64)
    }

    public fun deserialize_u128(buf: &vector<u8>): u128 {
        assert!(vector::length(buf) == 16, error::invalid_argument(EINVALID_LENGTH));
        ((*vector::borrow(buf, 0) as u128) << 120)
            + ((*vector::borrow(buf, 1) as u128) << 112)
            + ((*vector::borrow(buf, 2) as u128) << 104)
            + ((*vector::borrow(buf, 3) as u128) << 96)
            + ((*vector::borrow(buf, 4) as u128) << 88)
            + ((*vector::borrow(buf, 5) as u128) << 80)
            + ((*vector::borrow(buf, 6) as u128) << 72)
            + ((*vector::borrow(buf, 7) as u128) << 64)
            + ((*vector::borrow(buf, 8) as u128) << 56)
            + ((*vector::borrow(buf, 9) as u128) << 48)
            + ((*vector::borrow(buf, 10) as u128) << 40)
            + ((*vector::borrow(buf, 11) as u128) << 32)
            + ((*vector::borrow(buf, 12) as u128) << 24)
            + ((*vector::borrow(buf, 13) as u128) << 16)
            + ((*vector::borrow(buf, 14) as u128) << 8)
            + (*vector::borrow(buf, 15) as u128)
    }

    public fun deserialize_u256(buf: &vector<u8>): U256 {
        assert!(vector::length(buf) == 32, error::invalid_argument(EINVALID_LENGTH));
        let v0 = u256::from_u128(deserialize_u128(&vector_slice(buf, 0, 16)));
        let v1 = u256::from_u128(deserialize_u128(&vector_slice(buf, 16, 32)));
        u256::add(u256::shl(v0, 128), v1)
    }

    public fun deserialize_u128_with_hex_str(buf: &vector<u8>): u128 {
        let data: u128 = 0;
        let i = 0;
        while (i < vector::length(buf)) {
            data = (data << 8) + (*vector::borrow(buf, i) as u128);
            i = i + 1;
        };
        data
    }

    public fun deserialize_u256_with_hex_str(buf: &vector<u8>): U256 {
        let len = vector::length(buf);
        assert!(len <= 32, EINVALID_LENGTH);
        if (len > 16) {
            let high_bit = len - 16;
            let high = deserialize_u128_with_hex_str(&mut vector_slice(buf, 0, high_bit));
            let low = deserialize_u128_with_hex_str(&mut vector_slice(buf, high_bit, len));
            u256::add(u256::shl(u256::from_u128(high), 128), u256::from_u128(low))
        }else {
            u256::from_u128(deserialize_u128_with_hex_str(buf))
        }
    }

    public fun deserialize_address(buf: &vector<u8>): address {
        assert!(vector::length(buf) == 32, error::invalid_argument(EINVALID_LENGTH));
        util::address_from_bytes(*buf)
    }

    public fun get_vector_length(buf: &vector<u8>): u64 {
        deserialize_u64(&vector_slice(buf, 0, 8))
    }

    public fun deserialize_vector_with_length(buf: &vector<u8>): vector<u8> {
        let len = vector::length(buf);
        if (len == 0) {
            return vector::empty<u8>()
        };
        assert!(len > 8, error::invalid_argument(EINVALID_LENGTH));
        let data_len = deserialize_u64(&vector_slice(buf, 0, 8));
        assert!(len == data_len + 8, error::invalid_argument(EINVALID_LENGTH));
        vector_slice(buf, 8, data_len + 8)
    }

    public fun vector_slice<T: copy>(vec: &vector<T>, start: u64, end: u64): vector<T> {
        assert!(start < end && end <= vector::length(vec), error::invalid_argument(EINVALID_LENGTH));
        let slice = vector::empty<T>();
        let i = start;
        while (i < end) {
            vector::push_back(&mut slice, *vector::borrow(vec, i));
            i = i + 1;
        };
        slice
    }

    public fun vector_split<T: copy + drop>(vec: &vector<T>, e: T): vector<vector<T>> {
        let split = vector::empty<vector<T>>();
        let start = 0;
        let end = 0;
        while (end < vector::length(vec)) {
            if (*vector::borrow(vec, end) == e) {
                if (start < end) {
                    vector::push_back(&mut split, vector_slice(vec, start, end));
                };
                start = end + 1;
            };
            end = end + 1;
        };
        if (start < end) {
            vector::push_back(&mut split, vector_slice(vec, start, end));
        };
        split
    }

    #[test]
    fun test_serialize() {
        let data = vector::empty<u8>();
        serialize_u8(&mut data, 1);
        assert!(data == vector<u8>[1], 0);

        let data = vector::empty<u8>();
        serialize_u16(&mut data, u16::from_u64(258));
        assert!(data == vector<u8>[1, 2], 0);

        let data = vector::empty<u8>();
        serialize_u64(&mut data, 72623859790382856);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = vector::empty<u8>();
        serialize_u128(&mut data, 1339673755198158349044581307228491536);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 0);

        let data = vector::empty<u8>();
        let v0 = u256::shl(u256::from_u128(1339673755198158349044581307228491536), 128);
        let v1 = u256::add(u256::from_u128(22690724228668807036942595891182575392), v0);
        serialize_u256(&mut data, v1);
        assert!(
            data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            0
        );

        let data = vector::empty<u8>();
        serialize_vector_with_length(&mut data, vector<u8>[1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = vector::empty<u8>();
        let v0 = u256::shl(u256::from_u128(1339673755198158349044581307228491536), 128);
        let v1 = u256::add(u256::from_u128(22690724228668807036942595891182575392), v0);
        serialize_u256_with_hex_str(&mut data, v1);
        assert!(
            data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            0
        );

        let data = vector::empty<u8>();
        let v0 = u256::shl(u256::from_u128(1), 128);
        serialize_u256_with_hex_str(&mut data, v0);
        assert!(data == vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0);

        let data = vector::empty<u8>();
        let v0 = u256::shl(u256::from_u128(1), 128);
        let v1 = u256::add(u256::from_u128(123), v0);
        serialize_u256_with_hex_str(&mut data, v1);
        assert!(data == vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123], 0);

        let data = vector::empty<u8>();
        let v0 = u256::from_u64(123);
        serialize_u256_with_hex_str(&mut data, v0);
        assert!(data == vector<u8>[123], 0);

        let data = vector::empty<u8>();
        serialize_u128_with_hex_str(&mut data, 123);
        assert!(data == vector<u8>[123], 0);

        let data = vector::empty<u8>();
        serialize_u128_with_hex_str(&mut data, 0);
        assert!(data == vector<u8>[0], 0);
    }

    #[test]
    fun test_deserialize() {
        let data = deserialize_u8(&vector<u8>[1]);
        assert!(data == 1, 0);

        let data = deserialize_u16(&vector<u8>[1, 2]);
        assert!(data == u16::from_u64(258), 0);

        let data = deserialize_u64(&vector<u8>[1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == 72623859790382856, 0);

        let data = deserialize_u128(&vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]);
        assert!(data == 1339673755198158349044581307228491536, 0);

        let data = deserialize_u256(
            &vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );
        let v0 = u256::shl(u256::from_u128(1339673755198158349044581307228491536), 128);
        let v1 = u256::add(u256::from_u128(22690724228668807036942595891182575392), v0);
        assert!(data == v1, 0);

        let data = deserialize_vector_with_length(&vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = deserialize_u256_with_hex_str(
            &vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );
        let v0 = u256::shl(u256::from_u128(1339673755198158349044581307228491536), 128);
        let v1 = u256::add(u256::from_u128(22690724228668807036942595891182575392), v0);
        assert!(data == v1, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        let v0 = u256::shl(u256::from_u128(1), 128);
        assert!(data == v0, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123]);
        let v0 = u256::shl(u256::from_u128(1), 128);
        let v1 = u256::add(u256::from_u128(123), v0);
        assert!(data == v1, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[123]);
        let v0 = u256::from_u64(123);
        assert!(data == v0, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[0]);
        let v0 = u256::from_u64(0);
        assert!(data == v0, 0);
    }
}
