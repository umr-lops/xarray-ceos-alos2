import numpy as np
from rich.console import Console
from tlz.dicttoolz import keyfilter, merge_with, valmap
from tlz.functoolz import compose_left, curry
from tlz.itertoolz import first, unique

from ceos_alos2.dicttoolz import valsplit

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


def is_variable(data):
    # "variables" are defined as one or more of:
    # - have metadata
    # - have multiple unique values (might have to adjust that)
    if not isinstance(data, list) or len(data) == 0:
        return False

    first_elem = data[0]
    if not isinstance(first_elem, tuple) and len(list(unique(data))) <= 1:
        return False

    return True


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
    ignored_fields = {
        "_io",
        "actual_count_of_left_fill_pixels",
        "actual_count_of_right_fill_pixels",
        "actual_count_of_data_pixels",
    }
    merge = compose_left(
        curry(map, curry(keyfilter, lambda k: k not in format_metadata)),
        curry(map, remove_nesting_layer),
        curry(starcall, curry(merge_with, list)),
        curry(keyfilter, lambda k: k not in ignored_fields and not k.startswith("blanks")),
    )
    merged = merge(metadata)

    # TODO split using known variable names instead?
    raw_vars, raw_attrs = valsplit(is_variable, merged)

    variables = valmap(transform_variable, raw_vars)
    attrs = valmap(first, raw_attrs)
    return variables, attrs
