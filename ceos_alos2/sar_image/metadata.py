import math

import numpy as np
from tlz.dicttoolz import keyfilter, merge_with, valfilter, valmap
from tlz.functoolz import compose_left, curry, pipe
from tlz.itertoolz import cons, first, second

from ceos_alos2.dicttoolz import apply_to_items, dissoc, keysplit
from ceos_alos2.transformers import as_group, remove_spares, separate_attrs
from ceos_alos2.utils import remove_nesting_layer, rename, starcall


def extract_format_type(header):
    return header["prefix_suffix_data_locators"]["sar_data_format_type_code"]


def extract_shape(header):
    return (
        header["sar_related_data_in_the_record"]["number_of_lines_per_dataset"],
        header["sar_related_data_in_the_record"]["number_of_data_groups_per_line"],
    )


def extract_attrs(header):
    # valid attrs:
    # - pixel range (level 1.5)
    # - burst data per file (level 1.1 specan)
    # - lines per burst (level 1.1 specan)
    # - overlap lines with adjacent bursts (level 1.1 specan)
    ignored = ["preamble"]
    known_attrs = {
        "interleaving_id",
        "maximum_data_range_of_pixel",
        "number_of_burst_data",
        "number_of_lines_per_burst",
        "number_of_overlap_lines_with_adjacent_bursts",
    }
    transformers = {
        "maximum_data_range_of_pixel": lambda v: [0, v] if not math.isnan(v) else [],
        "number_of_burst_data": lambda v: v if v != -1 else [],
        "number_of_lines_per_burst": lambda v: v if v != -1 else [],
        "number_of_overlap_lines_with_adjacent_bursts": lambda v: v if v != -1 else [],
    }
    translations = {
        "maximum_data_range_of_pixel": "valid_range",
    }

    return pipe(
        header,
        curry(dissoc, ignored),
        curry(remove_nesting_layer),
        curry(keyfilter, lambda k: k in known_attrs),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        curry(valfilter, lambda v: not isinstance(v, list) or v),
    )


def apply_overrides(dtype_overrides, mapping):
    def _apply(v, dtype):
        dims, data, attrs = v

        return dims, np.array(data, dtype=dtype), attrs

    return {
        k: v if k not in dtype_overrides else _apply(v, dtype_overrides[k])
        for k, v in mapping.items()
    }


def deduplicate_attrs(known, mapping):
    variables, attrs = keysplit(lambda k: k not in known, mapping)

    return variables | valmap(compose_left(second, first), attrs)


def transform_line_metadata(metadata):
    ignored = [
        "preamble",
        "record_start",
        "actual_count_of_left_fill_pixels",
        "actual_count_of_right_fill_pixels",
        "actual_count_of_data_pixels",
        "alos2_frame_number",
        "palsar_auxiliary_data",
        "data",
    ]
    translations = {
        "sar_image_data_line_number": "rows",
    }
    dtype_overrides = {
        "sensor_acquisition_date": "datetime64[ns]",
        "sensor_acquisition_date_microseconds": "datetime64[ns]",
    }
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
    merged = pipe(
        metadata,
        curry(starcall, curry(merge_with, list)),
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(valmap, compose_left(separate_attrs, curry(cons, "rows"), tuple)),
        curry(deduplicate_attrs, known_attrs),
        curry(apply_overrides, dtype_overrides),
        curry(rename, translations=translations),
        curry(as_group),
    )
    return merged


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
    group = transform_line_metadata(metadata)
    group.attrs |= header_attrs | {"coordinates": list(group.variables)}

    array_metadata = {
        "type_code": type_code,
        "shape": shape,
        "dtype": str(dtype),
        "byte_ranges": byte_ranges,
    }

    return group, array_metadata
