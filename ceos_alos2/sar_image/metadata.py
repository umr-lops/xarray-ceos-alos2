import numpy as np
from rich.console import Console
from tlz.dicttoolz import keyfilter, keymap, merge_with, valmap
from tlz.functoolz import compose_left, curry
from tlz.itertoolz import first

from ceos_alos2.dicttoolz import itemsplit

console = Console()


def starcall(func, args, **kwargs):
    return func(*args, **kwargs)


def remove_nesting_layer(mapping):
    def _remove(mapping):
        for key, value in mapping.items():
            if not isinstance(value, dict):
                yield key, value
                continue

            yield from value.items()

    return dict(_remove(mapping))


def transform_variable(data):
    if isinstance(data[0], tuple):
        values, metadata_ = zip(*data)
        metadata = metadata_[0]
    else:
        values = data
        metadata = {}
    return ("rows", np.array(values), metadata)


def extract_attrs(header):
    return {}


def transform_metadata(metadata):
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
        curry(keymap, lambda k: to_rename.get(k, k)),
    )
    merged = merge(metadata)

    # TODO split using known variable names instead?
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
    }
    raw_vars, raw_attrs = itemsplit(lambda it: it[0] not in known_attrs, merged)

    variables = valmap(transform_variable, raw_vars)
    attrs = valmap(first, raw_attrs)
    return variables, attrs
