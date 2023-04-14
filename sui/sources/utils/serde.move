// Copyright (c) OmniBTC, Inc.
// SPDX-License-Identifier: GPL-3.0

module omniswap::serde {
    use std::ascii;
    use std::bcs;
    use std::type_name;
    use std::vector;

    use sui::address;

    const EINVALID_LENGTH: u64 = 0;

    const OVERFLOW: u64 = 1;

    public fun serialize_u8(buf: &mut vector<u8>, v: u8) {
        vector::push_back(buf, v);
    }

    public fun serialize_u16(buf: &mut vector<u8>, v: u16) {
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

    public fun serialize_u256(buf: &mut vector<u8>, v: u256) {
        serialize_u8(buf, (((v >> 8 * 31) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 30) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 29) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 28) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 27) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 26) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 25) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 24) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 23) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 22) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 21) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 20) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 19) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 18) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 17) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 16) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 15) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 14) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 13) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 12) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 11) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 10) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 9) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 8) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 7) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 6) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 5) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 4) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 3) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 2) & 0xFF) as u8));
        serialize_u8(buf, (((v >> 8 * 1) & 0xFF) as u8));
        serialize_u8(buf, ((v & 0xFF) as u8));
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

    public fun serialize_u256_with_hex_str(buf: &mut vector<u8>, v: u256) {
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

    public fun serialize_vector(buf: &mut vector<u8>, v: vector<u8>) {
        vector::append(buf, v);
    }

    public fun serialize_address(buf: &mut vector<u8>, v: address) {
        let data = bcs::to_bytes(&v);
        assert!(vector::length(&data) == 32, EINVALID_LENGTH);
        vector::append(buf, data);
    }

    public fun serialize_type<T>(buf: &mut vector<u8>) {
        let type_name = type_name::get<T>();
        let name = type_name::into_string(type_name);
        serialize_vector(buf, ascii::into_bytes(name));
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
        assert!(vector::length(buf) == 1, EINVALID_LENGTH);
        *vector::borrow(buf, 0)
    }

    public fun deserialize_u16(buf: &vector<u8>): u16 {
        assert!(vector::length(buf) == 2, EINVALID_LENGTH);
        ((*vector::borrow(buf, 0) as u16) << 8)
            + (*vector::borrow(buf, 1) as u16)
    }

    public fun deserialize_u64(buf: &vector<u8>): u64 {
        assert!(vector::length(buf) == 8, EINVALID_LENGTH);
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
        assert!(vector::length(buf) == 16, EINVALID_LENGTH);
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

    public fun deserialize_u256(buf: &vector<u8>): u256 {
        assert!(vector::length(buf) == 32, EINVALID_LENGTH);
        ((*vector::borrow(buf, 0) as u256) << 8 * 31)
            + ((*vector::borrow(buf, 1) as u256) << 8 * 30)
            + ((*vector::borrow(buf, 2) as u256) << 8 * 29)
            + ((*vector::borrow(buf, 3) as u256) << 8 * 28)
            + ((*vector::borrow(buf, 4) as u256) << 8 * 27)
            + ((*vector::borrow(buf, 5) as u256) << 8 * 26)
            + ((*vector::borrow(buf, 6) as u256) << 8 * 25)
            + ((*vector::borrow(buf, 7) as u256) << 8 * 24)
            + ((*vector::borrow(buf, 8) as u256) << 8 * 23)
            + ((*vector::borrow(buf, 9) as u256) << 8 * 22)
            + ((*vector::borrow(buf, 10) as u256) << 8 * 21)
            + ((*vector::borrow(buf, 11) as u256) << 8 * 20)
            + ((*vector::borrow(buf, 12) as u256) << 8 * 19)
            + ((*vector::borrow(buf, 13) as u256) << 8 * 18)
            + ((*vector::borrow(buf, 14) as u256) << 8 * 17)
            + ((*vector::borrow(buf, 15) as u256) << 8 * 16)
            + ((*vector::borrow(buf, 16) as u256) << 8 * 15)
            + ((*vector::borrow(buf, 17) as u256) << 8 * 14)
            + ((*vector::borrow(buf, 18) as u256) << 8 * 13)
            + ((*vector::borrow(buf, 19) as u256) << 8 * 12)
            + ((*vector::borrow(buf, 20) as u256) << 8 * 11)
            + ((*vector::borrow(buf, 21) as u256) << 8 * 10)
            + ((*vector::borrow(buf, 22) as u256) << 8 * 9)
            + ((*vector::borrow(buf, 23) as u256) << 8 * 8)
            + ((*vector::borrow(buf, 24) as u256) << 8 * 7)
            + ((*vector::borrow(buf, 25) as u256) << 8 * 6)
            + ((*vector::borrow(buf, 26) as u256) << 8 * 5)
            + ((*vector::borrow(buf, 27) as u256) << 8 * 4)
            + ((*vector::borrow(buf, 28) as u256) << 8 * 3)
            + ((*vector::borrow(buf, 29) as u256) << 8 * 2)
            + ((*vector::borrow(buf, 30) as u256) << 8 * 1)
            + (*vector::borrow(buf, 31) as u256)
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

    public fun deserialize_u256_with_hex_str(buf: &vector<u8>): u256 {
        let data: u256 = 0;
        let i = 0;
        while (i < vector::length(buf)) {
            data = (data << 8) + (*vector::borrow(buf, i) as u256);
            i = i + 1;
        };
        data
    }

    public fun deserialize_address(buf: &vector<u8>): address {
        assert!(vector::length(buf) == 32, EINVALID_LENGTH);
        address::from_bytes(*buf)
    }

    public fun get_vector_length(buf: &vector<u8>): u64 {
        deserialize_u64(&vector_slice(buf, 0, 8))
    }

    public fun deserialize_vector_with_length(buf: &vector<u8>): vector<u8> {
        let len = vector::length(buf);
        if (len == 0) {
            return vector::empty<u8>()
        };
        assert!(len > 8, EINVALID_LENGTH);
        let data_len = deserialize_u64(&vector_slice(buf, 0, 8));
        assert!(len == data_len + 8, EINVALID_LENGTH);
        vector_slice(buf, 8, data_len + 8)
    }

    public fun vector_slice<T: copy>(vec: &vector<T>, start: u64, end: u64): vector<T> {
        assert!(start < end && end <= vector::length(vec), EINVALID_LENGTH);
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
        serialize_u16(&mut data, 258);
        assert!(data == vector<u8>[1, 2], 0);

        let data = vector::empty<u8>();
        serialize_u64(&mut data, 72623859790382856);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = vector::empty<u8>();
        serialize_u128(&mut data, 1339673755198158349044581307228491536);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 0);

        let data = vector::empty<u8>();
        serialize_u256(
            &mut data,
            (1339673755198158349044581307228491536 << 128) + 22690724228668807036942595891182575392
        );
        assert!(
            data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            0
        );

        let data = vector::empty<u8>();
        serialize_vector_with_length(&mut data, vector<u8>[1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = vector::empty<u8>();
        serialize_u256_with_hex_str(
            &mut data,
            (1339673755198158349044581307228491536 << 128) + 22690724228668807036942595891182575392
        );
        assert!(
            data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            0
        );

        let data = vector::empty<u8>();
        serialize_u256_with_hex_str(&mut data, 1 << 128);
        assert!(data == vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0);

        let data = vector::empty<u8>();
        serialize_u256_with_hex_str(&mut data, (1 << 128) + 123);
        assert!(data == vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123], 0);

        let data = vector::empty<u8>();
        serialize_u256_with_hex_str(&mut data, 123);
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
        assert!(data == 258, 0);

        let data = deserialize_u64(&vector<u8>[1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == 72623859790382856, 0);

        let data = deserialize_u128(&vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]);
        assert!(data == 1339673755198158349044581307228491536, 0);

        let data = deserialize_u256(
            &vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );

        assert!(data == ((1339673755198158349044581307228491536 << 128) + 22690724228668807036942595891182575392), 0);

        let data = deserialize_vector_with_length(&vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8], 0);

        let data = deserialize_u256_with_hex_str(
            &vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );
        assert!(data == ((1339673755198158349044581307228491536 << 128) + 22690724228668807036942595891182575392), 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        assert!(data == 1 << 128, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123]);
        assert!(data == ((1 << 128) + 123), 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[123]);
        assert!(data == 123, 0);

        let data = deserialize_u256_with_hex_str(&vector<u8>[0]);
        assert!(data == 0, 0);
    }
}
