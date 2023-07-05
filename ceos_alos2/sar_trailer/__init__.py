import itertools

from ceos_alos2.sar_trailer.file_descriptor import file_descriptor_record
from ceos_alos2.sar_trailer.image_data import parse_image_data


def read_sar_trailer(f):
    header = file_descriptor_record.parse(f.read(720))
    data = f.read()

    data_sizes = [record["record_length"] for record in header.low_resolution_image_sizes]
    offsets = list(itertools.accumulate(data_sizes, initial=0))

    ranges = list(zip(offsets, offsets[1:]))
    shapes = [
        (record["number_of_pixels"], record["number_of_lines"])
        for record in header.low_resolution_image_sizes
    ]
    n_bytes = [
        record["number_of_bytes_per_one_sample"] for record in header.low_resolution_image_sizes
    ]

    low_res_images = [
        parse_image_data(data[start:stop], shape, n_bytes_)
        for (start, stop), shape, n_bytes_ in zip(ranges, shapes, n_bytes)
    ]

    return header, low_res_images
