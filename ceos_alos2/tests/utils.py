import fsspec

from ceos_alos2.array import Array


def create_dummy_array(shape=(4, 3), dtype="int16", records_per_chunk=2, type_code="IU2"):
    byte_ranges = [(x * 10 + 5, (x + 1) * 10) for x in range(shape[0])]

    fs = fsspec.filesystem("memory")
    dirfs = fsspec.filesystem("dir", fs=fs, path="/path/to")

    return Array(
        fs=dirfs,
        url="file",
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        type_code=type_code,
        records_per_chunk=records_per_chunk,
    )
