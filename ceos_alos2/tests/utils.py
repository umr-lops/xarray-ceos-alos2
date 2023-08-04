from ceos_alos2.array import Array


def create_dummy_array(shape=(4, 3), dtype="int8"):
    byte_ranges = [(x * 10 + 5, (x + 1) * 10) for x in range(shape[0])]

    return Array(
        fs=None,
        url="file:///path/to/file",
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        parse_bytes=lambda x: x,
        records_per_chunk=2,
    )
