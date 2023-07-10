from dataclasses import dataclass, field
from typing import Any

import numpy as np
from tlz.itertoolz import first, get, groupby, partition_all, second


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
    return [{"offset": start, "size": stop - start} for start, stop in ranges]


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
    parse_bytes: callable = field(repr=False)

    # chunk sizes: chunks in (rows, cols)
    chunks: tuple[int, int] = field(repr=True, default=None)
    chunk_offsets: list[tuple[int, int]] = field(repr=False, init=False)

    def __post_init__(self):
        sizes = np.array([stop - start for start, stop in self.byte_ranges])
        possible_chunksizes = np.cumsum(sizes)
        if self.chunks is None:
            self.chunks = (1, self.shape[1])
        elif self.chunks == "auto":
            reference_size = 100 * 2**20
            rows_per_chunk = determine_nearest_chunksize(possible_chunksizes, reference_size)
            self.chunks = (rows_per_chunk, self.shape[1])
        self.chunk_offsets = compute_chunk_offsets(self.byte_ranges, self.chunks[0])

    def __getitem__(self, indexers):
        rows_per_chunk = self.chunks[0]

        selected_ranges = compute_selected_ranges(self.byte_ranges, indexers[0])
        grouped = groupby_chunks(selected_ranges, chunksize=rows_per_chunk)
        merged = merge_chunk_info(grouped, chunk_offsets=self.chunk_offsets)
        tasks = [relocate_ranges(info, ranges) for info, ranges in merged]

        with self.fs.open(self.url, mode="rb") as f:
            data = []
            for chunk_info, ranges in tasks:
                chunk = read_chunk(f, **chunk_info)
                raw_bytes = extract_ranges(chunk, ranges)
                chunk_data = [self.parse_bytes(part) for part in raw_bytes]
                data.extend(chunk_data)

            return np.stack(data, axis=0)
