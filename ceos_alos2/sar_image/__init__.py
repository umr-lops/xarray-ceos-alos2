import math

from ceos_alos2.sar_image.file_descriptor import file_descriptor_record
from ceos_alos2.sar_image.signal_data import signal_data_record


def parse_chunk(content, element_size):
    n_elements = len(content) // element_size
    if n_elements * element_size != len(content):
        raise ValueError(
            f"sizes mismatch: chunksize is {n_elements * element_size}"
            f" but got {len(content)} bytes"
        )

    parser = signal_data_record[n_elements]
    return list(parser.parse(content))


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

    metadata = [parse_chunk(f.read(chunksize), record_size) for chunksize in chunksizes]

    return header, metadata
