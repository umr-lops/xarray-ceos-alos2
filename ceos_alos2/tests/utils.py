import fsspec
from tlz.functoolz import curry

from ceos_alos2.array import Array


def parser(data, type_code):
    return data


def create_dummy_array(shape=(4, 3), dtype="int16"):
    byte_ranges = [(x * 10 + 5, (x + 1) * 10) for x in range(shape[0])]

    fs = fsspec.filesystem("memory")
    dirfs = fsspec.filesystem("dir", fs=fs, path="/path/to")

    return Array(
        fs=dirfs,
        url="file",
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        parse_bytes=curry(parser, type_code="IU2"),
        records_per_chunk=2,
    )
