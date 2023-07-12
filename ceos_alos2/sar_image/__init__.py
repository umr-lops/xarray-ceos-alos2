import itertools
import math

import numpy as np
from tlz.functoolz import curry
from tlz.itertoolz import partition_all

from ceos_alos2.common import record_preamble
from ceos_alos2.sar_image.file_descriptor import file_descriptor_record
from ceos_alos2.sar_image.processed_data import processed_data_record
from ceos_alos2.sar_image.signal_data import signal_data_record


def extract_record_type(preamble):
    return (
        preamble.first_record_subtype,
        preamble.record_type,
        preamble.second_record_subtype,
        preamble.third_record_subtype,
    )


record_types = {
    10: signal_data_record,
    11: processed_data_record,
}


def parse_chunk(content, element_size):
    n_elements = len(content) // element_size
    if n_elements * element_size != len(content):
        raise ValueError(
            f"sizes mismatch: chunksize is {n_elements * element_size}"
            f" but got {len(content)} bytes"
        )

    record_type = record_preamble.parse(content[:12]).record_type
    data_record = record_types.get(record_type)
    if data_record is None:
        raise ValueError(f"unknown record type code: {record_type}")

    parser = data_record[n_elements]
    return list(parser.parse(content))


def _adjust_offset(record, offset):
    record.record_start += offset
    record.data.start += offset
    record.data.stop += offset

    return record


def adjust_offsets(records, offset):
    return [_adjust_offset(record, offset) for record in records]


def read_metadata(f, records_per_chunk=1024):
    header = file_descriptor_record.parse(f.read(720))

    n_records = header.number_of_sar_data_records
    record_size = header.sar_data_record_length

    n_chunks = math.ceil(n_records / records_per_chunk)
    chunksizes = [
        records_per_chunk
        if records_per_chunk * (index + 1) <= n_records
        else n_records - records_per_chunk * index
        for index in range(n_chunks)
    ]
    chunk_offsets = [
        offset * record_size + 720 for offset in itertools.accumulate(chunksizes, initial=0)
    ]

    metadata = list(
        itertools.chain.from_iterable(
            adjust_offsets(
                parse_chunk(f.read(chunksize * record_size), record_size), offset=chunk_offset
            )
            for chunksize, chunk_offset in zip(chunksizes, chunk_offsets)
        )
    )

    return header, metadata


def extract_format_type(header):
    return header.prefix_suffix_data_locators.sar_data_format_type_code


def extract_shape(header):
    return (
        header.sar_related_data_in_the_record.number_of_lines_per_dataset,
        header.sar_related_data_in_the_record.number_of_data_groups_per_line,
    )


raw_dtypes = {
    "C*8": np.dtype([("real", ">f4"), ("imag", ">f4")]),
    "IU2": np.dtype(">u2"),
}

dtypes = {
    "C*8": np.dtype("complex64"),
    "IU2": np.dtype("uint16"),
}


def extract_dtype(header):
    type_code = extract_format_type(header)
    dtype = dtypes.get(type_code)
    if dtype is None:
        raise ValueError(f"unknown type code: {type_code}")

    return dtype


def extract_attrs(header):
    return {}


def transform_metadata(metadata):
    return {}, {}


def parse_data(content, type_code):
    dtype = raw_dtypes.get(type_code)
    if dtype is None:
        raise ValueError(f"unknown type code: {type_code}")

    raw = np.frombuffer(content, dtype)
    if type_code == "C*8":
        return raw["real"] + 1j * raw["imag"]
    return raw


def parse_data_chunked(bytes_, ranges, type_code):
    raw = np.stack([parse_data(bytes_[start:stop], type_code) for start, stop in ranges], axis=0)

    return np.where(raw != 0, raw, np.nan)


def compute_chunk_info(metadata, type_code):
    offset = metadata[0].record_start
    chunksize = metadata[0].preamble.record_length * len(metadata)
    return {
        "offset": offset,
        "size": chunksize,
        "type_code": type_code,
        "ranges": [(m.data.start - offset, m.data.stop - offset) for m in metadata],
    }


def read_chunk(f, offset, size, ranges, type_code):
    f.seek(offset)
    chunk = f.read(size)

    return parse_data_chunked(chunk, ranges, type_code)


def read_data_chunked(f, metadata, *, type_code, records_per_chunk=1024):
    partitioned = partition_all(records_per_chunk, metadata)
    chunk_info = list(map(curry(compute_chunk_info, type_code=type_code), partitioned))

    return np.concatenate([read_chunk(f, **info) for info in chunk_info], axis=0)
