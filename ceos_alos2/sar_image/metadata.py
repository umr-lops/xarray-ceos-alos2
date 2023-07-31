import numpy as np
from rich.console import Console
from tlz.dicttoolz import itemmap, keyfilter, keymap, merge_with, valmap
from tlz.functoolz import compose_left, curry, juxt
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


def data_astype(var, dtype):
    dims, data, *attrs = var

    return dims, data.astype(dtype), *attrs


def transform_variable(data):
    if isinstance(data[0], tuple):
        values, metadata_ = zip(*data)
        metadata = metadata_[0]
    else:
        values = data
        metadata = {}
    return ("rows", np.array(values), metadata)


def postprocess_variables(variables):
    postprocessors = {
        "sensor_acquisition_date": curry(data_astype, dtype="datetime64[ns]"),
    }

    def apply_postprocessor(name, data):
        postprocessor = postprocessors.get(name)
        if postprocessor is None:
            return data

        return postprocessor(data)

    return itemmap(juxt(first, curry(starcall, apply_postprocessor)), variables)


def rename(mapping, translations):
    return keymap(lambda k: translations.get(k, k), mapping)


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
        curry(rename, translations=to_rename),
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

    variables = postprocess_variables(valmap(transform_variable, raw_vars))
    attrs = valmap(first, raw_attrs)
    return variables, attrs
