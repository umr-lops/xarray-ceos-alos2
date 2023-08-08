from dataclasses import dataclass, field
from typing import Any

import numpy as np
from tlz.itertoolz import cons, first, get, groupby, partition_all, second

from ceos_alos2.utils import parse_bytes

raw_dtypes = {
    "C*8": np.dtype([("real", ">f4"), ("imag", ">f4")]),
    "IU2": np.dtype(">u2"),
}


def parse_data(content, type_code):
    dtype = raw_dtypes.get(type_code)
    if dtype is None:
        raise ValueError(f"unknown type code: {type_code}")

    raw = np.frombuffer(content, dtype)
    if type_code == "C*8":
        return raw["real"] + 1j * raw["imag"]
    return raw


def normalize_chunksize(chunksize, dim_size):
    if chunksize in (None, -1) or chunksize > dim_size:
        return dim_size

    return chunksize


def determine_nearest_chunksize(sizes, reference_size):
    diff = np.cumsum(sizes) - reference_size
    index = np.argmin(abs(diff))

    return index + 1


def compute_chunk_ranges(byte_ranges, chunks):
    partitioned = partition_all(chunks, byte_ranges)

    return {
        chunk_number: (min(map(first, ranges_)), max(map(second, ranges_)))
        for chunk_number, ranges_ in enumerate(partitioned)
    }


def to_offset_size(ranges):
    return {
        index: {"offset": start, "size": stop - start} for index, (start, stop) in ranges.items()
    }


def compute_chunk_offsets(byte_ranges, chunks):
    ranges = compute_chunk_ranges(byte_ranges, chunks)
    return to_offset_size(ranges)


def compute_selected_ranges(byte_ranges, indexer):
    n_rows = len(byte_ranges)
    if isinstance(indexer, int):
        indexer = [indexer]

    if isinstance(indexer, slice):
        selected_rows = range(n_rows)[indexer]
    else:
        selected_rows = indexer

    return list(get(list(selected_rows), list(enumerate(byte_ranges))))


def groupby_chunks(byte_ranges, chunksize):
    grouped = groupby(lambda it: it[0] // chunksize, byte_ranges)
    return {key: [value for _, value in ranges] for key, ranges in grouped.items()}


def merge_chunk_info(selected, chunk_offsets):
    return [(chunk_offsets[index], ranges) for index, ranges in selected.items()]


def relocate_ranges(chunk_info, ranges):
    offset = chunk_info["offset"]

    return chunk_info, [(min_ - offset, max_ - offset) for min_, max_ in ranges]


def extract_ranges(content, ranges):
    return [content[start:stop] for start, stop in ranges]


def read_chunk(f, offset, size):
    f.seek(offset)

    return f.read(size)


@dataclass(order=False, unsafe_hash=True)
class Array:
    """2d array from chunked data"""

    # TODO: decide whether having a cached file object or fs instance and url are better
    # file location / access
    fs: Any = field(repr=False)
    url: str = field(repr=True)

    # data positions
    byte_ranges: list[tuple[int, int]] = field(repr=False)

    # array information
    shape: tuple[int, int] = field(repr=True)
    dtype: str | np.dtype = field(repr=True)

    # convert raw bytes to data
    type_code: str = field(repr=False)

    # chunk sizes: chunks in (rows, cols)
    records_per_chunk: int | None = field(repr=True, default=None)
    chunk_offsets: list[tuple[int, int]] = field(repr=False, init=False)

    def __post_init__(self):
        sizes = np.array([stop - start for start, stop in self.byte_ranges])
        if self.records_per_chunk is None:
            self.records_per_chunk = 1024
        elif isinstance(self.records_per_chunk, str):
            if self.records_per_chunk == "auto":
                size = 100 * 2**20
            else:
                size = parse_bytes(self.records_per_chunk)

            self.records_per_chunk = determine_nearest_chunksize(sizes, size)
        else:
            self.records_per_chunk = normalize_chunksize(self.records_per_chunk, self.shape[0])
        self.chunk_offsets = compute_chunk_offsets(self.byte_ranges, self.records_per_chunk)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False

        return (
            self.url == other.url
            and self.fs == other.fs
            and self.byte_ranges == other.byte_ranges
            and self.shape == other.shape
            and self.dtype == other.dtype
            and self.records_per_chunk == other.records_per_chunk
            and self.type_code == other.type_code
        )

    def __getitem__(self, indexers):
        selected_ranges = compute_selected_ranges(self.byte_ranges, indexers[0])
        grouped = groupby_chunks(selected_ranges, chunksize=self.records_per_chunk)
        merged = merge_chunk_info(grouped, chunk_offsets=self.chunk_offsets)
        tasks = [relocate_ranges(info, ranges) for info, ranges in merged]

        with self.fs.open(self.url, mode="rb") as f:
            data_ = []
            for chunk_info, ranges in tasks:
                chunk = read_chunk(f, **chunk_info)
                raw_bytes = extract_ranges(chunk, ranges)
                chunk_data = [parse_data(part, type_code=self.type_code) for part in raw_bytes]
                data_.extend(chunk_data)

            data = np.stack(data_, axis=0)

        new_indexers = tuple(cons(slice(None), indexers[1:]))
        return data[new_indexers]

    @property
    def ndim(self):
        return len(self.shape)

    @property
    def chunks(self):
        return (self.records_per_chunk, *self.shape[1:])
