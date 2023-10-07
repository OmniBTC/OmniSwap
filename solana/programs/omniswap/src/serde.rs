use spl_math::uint::U256;

pub fn serialize_u8(buf: &mut Vec<u8>, v: u8) {
    buf.push(v)
}

pub fn serialize_u16(buf: &mut Vec<u8>, v: u16) {
    let u16_be_bytes = v.to_be_bytes();
    buf.extend_from_slice(&u16_be_bytes)
}

pub fn serialize_u64(buf: &mut Vec<u8>, v: u64) {
    let u64_be_bytes = v.to_be_bytes();
    buf.extend_from_slice(&u64_be_bytes)
}

pub fn serialize_u128(buf: &mut Vec<u8>, v: u128) {
    let u128_be_bytes = v.to_be_bytes();
    buf.extend_from_slice(&u128_be_bytes)
}

pub fn serialize_u256(buf: &mut Vec<u8>, v: U256) {
    let mut u256_be_bytes= vec![0;32];
    v.to_big_endian(u256_be_bytes.as_mut_slice());
    buf.extend_from_slice(&u256_be_bytes)
}

pub fn serialize_u128_with_hex_str(buf: &mut Vec<u8>, v: u128) {
    if v == 0 {
        return buf.push(0)
    }

    let mut u128_be_bytes_compact = v.to_be_bytes()
        .into_iter()
        .skip_while(|&x| x == 0)
        .collect::<Vec<u8>>();

    buf.append(&mut u128_be_bytes_compact)
}

pub fn serialize_u256_with_hex_str(buf: &mut Vec<u8>, v: U256) {
    if v.is_zero() {
        return buf.push(0)
    }

    let mut u256_be_bytes= vec![0;32];
    v.to_big_endian(u256_be_bytes.as_mut_slice());

    let mut u256_be_bytes_compact = u256_be_bytes
        .into_iter()
        .skip_while(|&x| x == 0)
        .collect::<Vec<u8>>();

    buf.append(&mut u256_be_bytes_compact)
}

pub fn serialize_vector(buf: &mut Vec<u8>, v: &[u8]) {
    buf.append(v.to_vec().as_mut());
}

pub fn serialize_vector_with_length(buf: &mut Vec<u8>, v: &[u8]) {
    let len = v.len();

    if len == 0 {
        return
    };

    serialize_u64(buf, len as u64);
    serialize_vector(buf, v);
}

pub fn get_vector_length(buf: &[u8]) -> u64 {
    deserialize_u64(&buf[0..8])
}

pub fn deserialize_vector_with_length(buf: &[u8]) -> Vec<u8> {
    let buf_len = buf.len();
    if buf_len == 0 {
        return Vec::new()
    }

    assert!(buf_len > 8, "EINVALID_LENGTH");
    let data_len = deserialize_u64(&buf[0..8]);
    let total_len = (data_len + 8) as usize;

    assert_eq!(buf_len, total_len, "EINVALID_LENGTH");

    buf[8..total_len].to_vec()
}

pub fn deserialize_u8(buf: &[u8]) -> u8 {
    assert_eq!(buf.len(), 1, "EINVALID_LENGTH");

    buf[0]
}

pub fn deserialize_u16(buf: &[u8]) -> u16 {
    assert_eq!(buf.len(), 2, "EINVALID_LENGTH");

    u16::from_be_bytes(buf.try_into().unwrap())
}

pub fn deserialize_u64(buf: &[u8]) -> u64 {
    assert_eq!(buf.len(), 8, "EINVALID_LENGTH");

    u64::from_be_bytes(buf.try_into().unwrap())
}

pub fn deserialize_u128(buf: &[u8]) -> u128 {
    assert_eq!(buf.len(), 16, "EINVALID_LENGTH");

    u128::from_be_bytes(buf.try_into().unwrap())
}

pub fn deserialize_u256(buf: &[u8]) -> U256 {
    assert_eq!(buf.len(), 32, "EINVALID_LENGTH");

    U256::from_big_endian(buf.try_into().unwrap())
}

pub fn deserialize_u128_with_hex_str(buf: &[u8]) -> u128 {
    const  MAX_LEN: usize = 16usize;

    let buf_len = buf.len();

    if buf_len >= MAX_LEN {
        return u128::from_be_bytes(buf.try_into().unwrap())
    }

    let padding_len = MAX_LEN - buf_len;
    let mut padding_buf = vec![0u8; padding_len];

    padding_buf.extend_from_slice(buf);

    u128::from_be_bytes(padding_buf.try_into().unwrap())
}

pub fn deserialize_u256_with_hex_str(buf: &[u8]) -> U256 {
    const  MAX_LEN: usize = 32usize;

    let buf_len = buf.len();

    if buf_len >= MAX_LEN {
        return U256::from_big_endian(buf.try_into().unwrap())
    }

    let padding_len = MAX_LEN - buf_len;
    let mut padding_buf = vec![0u8; padding_len];

    padding_buf.extend_from_slice(buf);

    U256::from_big_endian(padding_buf.as_slice().try_into().unwrap())
}


#[cfg(test)]
pub mod test {
    use std::ops::{Add, Shl};
    use super::*;

    #[test]
    fn test_serialize() {
        let mut data = Vec::<u8>::new();

        serialize_u8(&mut data, 1);
        assert_eq!(data, vec![1]);

        let mut data = Vec::<u8>::new();
        serialize_u16(&mut data, 258);
        assert_eq!(data, vec![1, 2]);

        let mut data = Vec::<u8>::new();
        serialize_u64(&mut data, 72623859790382856);
        assert_eq!(data, vec![1, 2, 3, 4, 5, 6, 7, 8]);

        let mut data = Vec::<u8>::new();
        serialize_u128(&mut data, 1339673755198158349044581307228491536);
        assert_eq!(data, vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]);

        let mut data = Vec::<u8>::new();
        serialize_u256(&mut data, U256::from(1339673755198158349044581307228491536u128).shl(128).add(22690724228668807036942595891182575392u128));
        assert_eq!(data, vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]);

        let mut data = Vec::<u8>::new();
        serialize_vector_with_length(&mut data, &mut vec![1, 2, 3, 4, 5, 6, 7, 8]);
        assert_eq!(data, vec![0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8]);

        let mut data = Vec::<u8>::new();
        serialize_u256_with_hex_str(&mut data, U256::from(1339673755198158349044581307228491536u128).shl(128).add(22690724228668807036942595891182575392u128));
        assert_eq!(data, vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]);

        let mut data = Vec::<u8>::new();
        serialize_u256_with_hex_str(&mut data, U256::from(1).shl(128));
        assert_eq!(data, vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);

        let mut data = Vec::<u8>::new();
        serialize_u256_with_hex_str(&mut data, U256::from(1).shl(128).add(123));
        assert_eq!(data, vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123]);

        let mut data = Vec::<u8>::new();
        serialize_u256_with_hex_str(&mut data, U256::from(123));
        assert_eq!(data, vec![123]);

        let mut data = Vec::<u8>::new();
        serialize_u128_with_hex_str(&mut data, 123);
        assert_eq!(data, vec![123]);

        let mut data = Vec::<u8>::new();
        serialize_u128_with_hex_str(&mut data, 0);
        assert_eq!(data, vec![0]);
    }

    #[test]
    fn test_deserialize() {
        let data = deserialize_u8(&vec![1]);
        assert_eq!(data, 1);

        let data = deserialize_u16(&vec![1, 2]);
        assert_eq!(data, 258u16);

        let data = deserialize_u64(&vec![1, 2, 3, 4, 5, 6, 7, 8]);
        assert_eq!(data, 72623859790382856u64);

        let data = deserialize_u128(&vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]);
        assert_eq!(data, 1339673755198158349044581307228491536u128);

        let data = deserialize_u256(
            &vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );
        assert_eq!(data, U256::from(1339673755198158349044581307228491536u128).shl(128).add(22690724228668807036942595891182575392u128));

        let data = deserialize_vector_with_length(&vec![0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8]);
        assert_eq!(data, vec![1, 2, 3, 4, 5, 6, 7, 8]);

        let data = deserialize_u256_with_hex_str(
            &vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        );
        assert_eq!(data, U256::from(1339673755198158349044581307228491536u128).shl(128).add(22690724228668807036942595891182575392u128));

        let data = deserialize_u256_with_hex_str(&vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
        assert_eq!(data, U256::from(1).shl(128));

        let data = deserialize_u256_with_hex_str(&vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123]);
        assert_eq!(data, U256::from(1).shl(128).add(123));

        let data = deserialize_u256_with_hex_str(&vec![123]);
        assert_eq!(data, U256::from(123));

        let data = deserialize_u256_with_hex_str(&vec![0]);
        assert_eq!(data, U256::zero());
    }
}