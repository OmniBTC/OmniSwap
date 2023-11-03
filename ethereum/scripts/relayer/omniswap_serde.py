def serialize_u8(buf: bytearray, v: int):
    buf.extend(v.to_bytes(length=1, byteorder="big", signed=False))


def serialize_u16(buf: bytearray, v: int):
    buf.extend(v.to_bytes(length=2, byteorder="big", signed=False))


def serialize_u64(buf: bytearray, v: int):
    buf.extend(v.to_bytes(length=8, byteorder="big", signed=False))


def serialize_u128(buf: bytearray, v: int):
    buf.extend(v.to_bytes(length=16, byteorder="big", signed=False))


def serialize_u256(buf: bytearray, v: int):
    buf.extend(v.to_bytes(length=32, byteorder="big", signed=False))


def serialize_u128_with_hex_str(buf: bytearray, v: int):
    if v == 0:
        buf.append(0)
    else:
        buf.extend(v.to_bytes(length=16, byteorder="big", signed=False).lstrip(b"\x00"))


def serialize_u256_with_hex_str(buf: bytearray, v: int):
    if v == 0:
        buf.append(0)
    else:
        buf.extend(v.to_bytes(length=32, byteorder="big", signed=False).lstrip(b"\x00"))


def serialize_vector(buf: bytearray, v: bytes):
    buf.extend(v)


def serialize_vector_with_length(buf: bytearray, v: bytes):
    length = len(v)
    if length == 0:
        return
    serialize_u64(buf, length)
    serialize_vector(buf, v)


def get_vector_length(buf: bytes):
    assert len(buf) >= 8, "EINVALID_LENGTH"
    return deserialize_u64(buf[0:8])


def deserialize_vector_with_length(buf: bytes):
    assert len(buf) >= 8, "EINVALID_LENGTH"
    data_len = deserialize_u64(buf[0:8])

    if data_len == 0:
        return bytes()
    return buf[8 : 8 + data_len]


def deserialize_u8(buf: bytes):
    assert len(buf) == 1, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u16(buf: bytes):
    assert len(buf) == 2, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u64(buf: bytes):
    assert len(buf) == 8, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u128(buf: bytes):
    assert len(buf) == 16, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u256(buf: bytes):
    assert len(buf) == 32, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u128_with_hex_str(buf: bytes):
    assert len(buf) <= 16, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def deserialize_u256_with_hex_str(buf: bytes):
    assert len(buf) <= 32, "EINVALID_LENGTH"
    return int.from_bytes(bytes=buf, byteorder="big", signed=False)


def test_serialize():
    buf = bytearray()
    serialize_u8(buf, 1)
    assert list(buf) == [1], list(buf)

    buf = bytearray()
    serialize_u16(buf, 258)
    assert list(buf) == [1, 2], list(buf)

    buf = bytearray()
    serialize_u64(buf, 72623859790382856)
    assert list(buf) == [1, 2, 3, 4, 5, 6, 7, 8], list(buf)

    buf = bytearray()
    serialize_u128(buf, 1339673755198158349044581307228491536)
    assert list(buf) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], list(
        buf
    )

    buf = bytearray()
    serialize_u256(
        buf,
        (1339673755198158349044581307228491536 << 128)
        + 22690724228668807036942595891182575392,
    )
    assert list(buf) == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
    ], list(buf)

    buf = bytearray()
    serialize_vector_with_length(buf, bytes([1, 2, 3, 4, 5, 6, 7, 8]))
    assert list(buf) == [0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8], list(buf)

    buf = bytearray()
    serialize_u256_with_hex_str(
        buf,
        (1339673755198158349044581307228491536 << 128)
        + 22690724228668807036942595891182575392,
    )
    assert list(buf) == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
    ], list(buf)

    buf = bytearray()
    serialize_u256_with_hex_str(buf, (1 << 128))
    assert list(buf) == [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], list(buf)

    buf = bytearray()
    serialize_u256_with_hex_str(buf, (1 << 128) + 123)
    assert list(buf) == [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123], list(buf)

    buf = bytearray()
    serialize_u256_with_hex_str(buf, 123)
    assert list(buf) == [123], list(buf)

    buf = bytearray()
    serialize_u128_with_hex_str(buf, 123)
    assert list(buf) == [123], list(buf)

    buf = bytearray()
    serialize_u128_with_hex_str(buf, 0)
    assert list(buf) == [0], list(buf)


def test_deserialize():
    data = deserialize_u8(bytes([1]))
    assert 1 == data, data

    data = deserialize_u16(bytes([1, 2]))
    assert 258 == data, data

    data = deserialize_u64(bytes([1, 2, 3, 4, 5, 6, 7, 8]))
    assert 72623859790382856 == data, data

    data = deserialize_u128(
        bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    )
    assert 1339673755198158349044581307228491536 == data, data

    data = deserialize_u256(
        bytes(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
                32,
            ]
        )
    )
    assert (
        1339673755198158349044581307228491536 << 128
    ) + 22690724228668807036942595891182575392 == data, data

    data = deserialize_vector_with_length(
        bytes([0, 0, 0, 0, 0, 0, 0, 8, 1, 2, 3, 4, 5, 6, 7, 8])
    )
    assert [1, 2, 3, 4, 5, 6, 7, 8] == list(data), list(data)

    data = deserialize_u256_with_hex_str(
        bytes(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
                31,
                32,
            ]
        )
    )
    assert (
        1339673755198158349044581307228491536 << 128
    ) + 22690724228668807036942595891182575392 == data, data

    data = deserialize_u256_with_hex_str(
        bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    )
    assert (1 << 128) == data, data

    data = deserialize_u256_with_hex_str(
        bytes([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 123])
    )
    assert (1 << 128) + 123 == data, data

    data = deserialize_u256_with_hex_str(bytes([123]))
    assert 123 == data, data

    data = deserialize_u256_with_hex_str(bytes([0]))
    assert 0 == data, data


if __name__ == "__main__":
    test_serialize()
    test_deserialize()
