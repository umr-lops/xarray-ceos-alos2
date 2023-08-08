import datetime as dt

import numpy as np
from tlz.dicttoolz import get_in, itemmap, keyfilter, merge_with, valmap
from tlz.functoolz import apply, compose_left, curry, juxt
from tlz.itertoolz import cons, first, get, identity

from ceos_alos2.dicttoolz import itemsplit
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.utils import remove_nesting_layer, rename


def extract_format_type(header):
    return header["prefix_suffix_data_locators"]["sar_data_format_type_code"]


def extract_shape(header):
    return (
        header["sar_related_data_in_the_record"]["number_of_lines_per_dataset"],
        header["sar_related_data_in_the_record"]["number_of_data_groups_per_line"],
    )


def starcall(func, args, **kwargs):
    return func(*args, **kwargs)


def extract_attrs(header):
    # valid attrs:
    # - pixel range (level 1.5)
    # - burst data per file (level 1.1 specan)
    # - lines per burst (level 1.1 specan)
    # - overlap lines with adjacent bursts (level 1.1 specan)
    known_attrs = {
        "interleaving_id",
        "maximum_data_range_of_pixel",
        "number_of_burst_data",
        "number_of_lines_per_burst",
        "number_of_overlap_lines_with_adjacent_bursts",
    }
    translators = {
        "maximum_data_range_of_pixel": lambda it: ("valid_range", [it[1][1]["start"], it[1][0]])
    }
    filter = compose_left(
        curry(keyfilter, lambda k: k != "preamble"),
        curry(remove_nesting_layer),
        curry(keyfilter, lambda k: k in known_attrs),
        curry(itemmap, lambda it: translators.get(it[0], lambda it: it)(it)),
    )
    return filter(header)


def key_exists(mapping, key):
    if "." in key:
        key = key.split(".")
    else:
        key = [key]

    sentinel = object()

    value = get_in(key, mapping, default=sentinel)

    return value is not sentinel


def to_hierarchical(mapping, dtype_overrides={}):
    def transform_variable(data, dtype=None):
        if isinstance(data[0], tuple):
            values, metadata_ = zip(*data)
            metadata = metadata_[0]
        else:
            values = data
            metadata = {}

        if dtype is not None:
            data_ = np.array(values, dtype=dtype)
        else:
            data_ = np.array(values)
        return Variable(dims="rows", data=data_, attrs=metadata)

    def transform_subgroup(data):
        merged = merge_with(list, data)
        subgroup_data = to_hierarchical(merged)

        return Group(path=None, url=None, data=subgroup_data, attrs={})

    def detect_type(data):
        if not isinstance(data, list):
            raise ValueError("not a list")
        elif len(data) == 0:
            raise ValueError("empty list")

        elem = data[0]
        if isinstance(elem, dict):
            return "group"
        elif isinstance(elem, (int, float, str, dt.datetime, tuple)):
            return "variable"
        else:
            raise ValueError(f"unknown element type: {type(elem)}")

    processors = {
        "group": transform_subgroup,
        "variable": transform_variable,
    }

    transform_entry = compose_left(
        juxt(
            compose_left(first, detect_type, curry(get, seq=processors, default=identity)), identity
        ),
        curry(starcall, cons),
        curry(starcall, apply),
    )

    # TODO: do we need to get this to work with subgroups?
    filtered_overrides = keyfilter(curry(key_exists, mapping), dtype_overrides)
    with_overrides = merge_with(tuple, mapping, filtered_overrides)

    return valmap(transform_entry, with_overrides)


def metadata_to_groups(metadata):
    # process:
    # - drop format metadata
    # - remove categories
    # - merge_with list
    # - split into variables and attributes (TODO: criteria for variable without metadata?)
    format_metadata = {"record_start", "preamble", "data"}
    to_rename = {"sar_image_data_line_number": "rows"}
    ignored_fields = {
        "_io",
        "actual_count_of_left_fill_pixels",
        "actual_count_of_right_fill_pixels",
        "actual_count_of_data_pixels",
        "palsar_auxiliary_data",
    }
    merge = compose_left(
        curry(map, curry(keyfilter, lambda k: k not in format_metadata)),
        curry(map, remove_nesting_layer),
        curry(starcall, curry(merge_with, list)),
        curry(keyfilter, lambda k: k not in ignored_fields and not k.startswith("blanks")),
        curry(rename, translations=to_rename),
    )
    merged = merge(metadata)

    # TODO split using known variable names instead?
    # TODO: what about deduplicating known constant variables?
    known_attrs = {
        "sar_image_data_record_index",
        "sensor_parameters_update_flag",
        "scan_id",
        "sar_channel_code",
        "sar_channel_id",
        "onboard_range_compressed_flag",
        "chirp_type_designator",
        "platform_position_parameters_update_flag",
        "alos2_frame_number",
        "geographic_reference_parameter_update_flag",
        "transmitted_pulse_polarization",
        "received_pulse_polarization",
    }
    raw_data, raw_attrs = itemsplit(lambda it: it[0] not in known_attrs, merged)

    override_dtypes = {
        "sensor_acquisition_date": "datetime64[ns]",
        "sensor_acquisition_date_microseconds": "datetime64[ns]",
    }

    processed = to_hierarchical(raw_data, override_dtypes)

    attrs = valmap(first, raw_attrs)

    return Group(path="", url=None, data=processed, attrs=attrs)


raw_dtypes = {
    "C*8": np.dtype([("real", ">f4"), ("imag", ">f4")]),
    "IU2": np.dtype(">u2"),
}

dtypes = {
    "C*8": np.dtype("complex64"),
    "IU2": np.dtype("uint16"),
}


def transform_metadata(header, metadata):
    byte_ranges = [(m["data"]["start"], m["data"]["stop"]) for m in metadata]
    type_code = extract_format_type(header)

    shape = extract_shape(header)
    dtype = dtypes.get(type_code)
    if dtype is None:
        raise ValueError(f"unknown type code: {type_code}")

    header_attrs = extract_attrs(header)
    group = metadata_to_groups(metadata)
    group.attrs |= header_attrs | {"coordinates": list(group.variables)}

    array_metadata = {
        "type_code": type_code,
        "shape": shape,
        "dtype": str(dtype),
        "byte_ranges": byte_ranges,
    }

    return group, array_metadata
