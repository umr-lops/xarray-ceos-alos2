import itertools
import math

import numpy as np
from construct import Float32b, Int16ub, Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import ComplexAdapter
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


parsers = {
    "C*8": ComplexAdapter(Struct("real" / Float32b, "imaginary" / Float32b)),
    "IU2": Int16ub,
}


def parse_data(content, type_code):
    base = parsers.get(type_code)
    if base is None:
        raise ValueError(f"unknown type code: {type_code}")

    element_size = base.sizeof()
    n_elements = len(content) // element_size
    if n_elements * element_size != len(content):
        raise ValueError("type doesn't evenly divide buffer")

    # TODO: try whether using `numpy.frombuffer` would be possible / faster
    parser = base[n_elements]

    return np.array(parser.parse(content))


def read_data_chunk(f, offset, record_size, type_code, records_per_chunk=1024):
    f.seek(offset, whence=0)

    size = records_per_chunk * record_size

    content = f.read(size)

    metadata = parse_chunk(content, record_size)
    byte_ranges = [(m.data.start, m.data.stop) for m in metadata]

    return np.stack(
        [parse_data(content[start:stop], type_code) for start, stop in byte_ranges], axis=0
    )
