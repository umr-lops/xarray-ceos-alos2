import fsspec

from ceos_alos2.array import Array


def create_dummy_array(
    *,
    protocol="memory",
    byte_ranges=None,
    path="/path/to",
    url="file",
    shape=(4, 3),
    dtype="int16",
    records_per_chunk=2,
    type_code="IU2",
):
    if byte_ranges is None:
        byte_ranges = [(x * 10 + 5, (x + 1) * 10) for x in range(shape[0])]

    fs = fsspec.filesystem(protocol)
    dirfs = fsspec.filesystem("dir", fs=fs, path=path)

    return Array(
        fs=dirfs,
        url=url,
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        type_code=type_code,
        records_per_chunk=records_per_chunk,
    )
