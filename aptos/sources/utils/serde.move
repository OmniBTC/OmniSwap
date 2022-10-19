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

    public fun serialize_vector(buf: &mut vector<u8>, v: vector<u8>) {
        vector::append(buf, v);
    }

    public fun serialize_address(buf: &mut vector<u8>, v: address) {
        let data = bcs::to_bytes(&v);
        assert!(vector::length(&data) == 32, error::invalid_argument(EINVALID_LENGTH));
        vector::append(buf, data);
    }

    public fun serialize_type<T>(buf: &mut vector<u8>) {
        serialize_vector(buf,  *string::bytes(&type_info::type_name<T>()));
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

    public fun deserialize_address(buf: &vector<u8>): address {
        assert!(vector::length(buf) == 32, error::invalid_argument(EINVALID_LENGTH));
        util::address_from_bytes(*buf)
    }

    public fun get_vector_length(buf: &vector<u8>): u64{
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
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32], 0);

        let data = vector::empty<u8>();
        serialize_vector_with_length(&mut data, vector<u8>[1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8], 0);
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

        let data = deserialize_u256(&vector<u8>[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]);
        let v0 = u256::shl(u256::from_u128(1339673755198158349044581307228491536), 128);
        let v1 = u256::add(u256::from_u128(22690724228668807036942595891182575392), v0);
        assert!(data == v1, 0);

        let data = deserialize_vector_with_length(&vector<u8>[0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8]);
        assert!(data == vector<u8>[1, 2, 3, 4, 5, 6, 7, 8], 0);
    }
}
