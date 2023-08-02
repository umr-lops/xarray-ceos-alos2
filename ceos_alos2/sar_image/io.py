import itertools
import math

import numpy as np
from fsspec.implementations.dirfs import DirFileSystem
from tlz.functoolz import curry
from tlz.itertoolz import concat

from ceos_alos2.array import Array
from ceos_alos2.common import record_preamble
from ceos_alos2.hierarchy import Variable
from ceos_alos2.sar_image import caching
from ceos_alos2.sar_image.caching import CachingError
from ceos_alos2.sar_image.file_descriptor import file_descriptor_record
from ceos_alos2.sar_image.metadata import raw_dtypes, transform_metadata
from ceos_alos2.sar_image.processed_data import processed_data_record
from ceos_alos2.sar_image.signal_data import signal_data_record
from ceos_alos2.utils import to_dict

record_types = {
    10: signal_data_record,
    11: processed_data_record,
}


def filename_to_groupname(path):
    from ceos_alos2.decoders import decode_filename

    info = decode_filename(path)
    scan_number = f"scan{info['scan_number']}" if "scan_number" in info else None
    polarization = info.get("polarization")
    parts = [polarization, scan_number]
    return "_".join([_ for _ in parts if _])


def parse_data(content, type_code):
    dtype = raw_dtypes.get(type_code)
    if dtype is None:
        raise ValueError(f"unknown type code: {type_code}")

    raw = np.frombuffer(content, dtype)
    if type_code == "C*8":
        return raw["real"] + 1j * raw["imag"]
    return raw


def create_array(fs, path, byte_ranges, shape, dtype, type_code, records_per_chunk):
    parser = curry(parse_data, type_code=type_code)

    return Array(
        fs=fs,
        url=path,
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        parse_bytes=parser,
        records_per_chunk=records_per_chunk,
    )


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

    raw_metadata = (
        parse_chunk(f.read(chunksize * record_size), record_size) for chunksize in chunksizes
    )
    adjusted = (
        adjust_offsets(records, offset=offset)
        for records, offset in zip(raw_metadata, chunk_offsets)
    )
    metadata = list(concat(adjusted))

    return to_dict(header), to_dict(metadata)


def open_image(mapper, path, *, use_cache=True, create_cache=False, records_per_chunk=None):
    if use_cache:
        try:
            return caching.read_cache(mapper, path)
        except CachingError:
            pass

    try:
        fs = mapper.dirfs
    except AttributeError:
        fs = DirFileSystem(fs=mapper.fs, path=mapper.root)

    with fs.open(path, mode="rb") as f:
        header, metadata = read_metadata(f, records_per_chunk)

        group, array_metadata = transform_metadata(header, metadata)

    group["data"] = Variable(
        dims=["rows", "columns"],
        data=create_array(fs=fs, path=path, records_per_chunk=records_per_chunk, **array_metadata),
        attrs={},
    )
    group.path = filename_to_groupname(path)

    if create_cache:
        caching.create_cache(mapper, path, group)

    return group
