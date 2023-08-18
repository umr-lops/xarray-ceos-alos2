import numpy as np
from construct import Struct, this
from tlz.dicttoolz import assoc_in, get_in, merge_with, valmap
from tlz.functoolz import curry, pipe
from tlz.itertoolz import cons, get

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString
from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.transformers import as_group, separate_attrs

attitude_point = Struct(
    "time"
    / Struct(
        "day_of_year" / AsciiInteger(4),
        "millisecond_of_day" / AsciiInteger(8),
    ),
    "attitude"
    / Struct(
        "pitch_error" / AsciiInteger(4),
        "roll_error" / AsciiInteger(4),
        "yaw_error" / AsciiInteger(4),
        "pitch" / Metadata(AsciiFloat(14), units="deg"),
        "roll" / Metadata(AsciiFloat(14), units="deg"),
        "yaw" / Metadata(AsciiFloat(14), units="deg"),
    ),
    "rates"
    / Struct(
        "pitch_error" / AsciiInteger(4),
        "roll_error" / AsciiInteger(4),
        "yaw_error" / AsciiInteger(4),
        "pitch" / Metadata(AsciiFloat(14), units="deg/s"),
        "roll" / Metadata(AsciiFloat(14), units="deg/s"),
        "yaw" / Metadata(AsciiFloat(14), units="deg/s"),
    ),
)

attitude_record = Struct(
    "preamble" / record_preamble,
    "number_of_points" / AsciiInteger(4),
    "data_points" / attitude_point[this.number_of_points],
    "blanks" / PaddedString(this.preamble.record_length - (12 + 4 + this.number_of_points * 120)),
)


def transform_time(mapping):
    # no year information, so we have to convert to timedelta
    units = {"day_of_year": "D", "millisecond_of_day": "ms"}
    transformed = {k: np.asarray(v, dtype=f"timedelta64[{units[k]}]") for k, v in mapping.items()}

    return (transformed["day_of_year"] + transformed["millisecond_of_day"]).astype(
        "timedelta64[ns]"
    )


def transpose_nested(mapping):
    def _transpose(value):
        if not isinstance(value, list) or not value or not isinstance(value[0], dict):
            return value

        return merge_with(list, *value)

    return pipe(
        mapping,
        curry(_transpose),
        curry(valmap, _transpose),
    )


def prepend_dim(dim, var):
    if isinstance(var, dict):
        return valmap(curry(prepend_dim, dim), var)

    if not isinstance(var, tuple):
        var = (var, {})

    return tuple(cons(dim, var))


def copy(instructions, mapping):
    new = mapping
    for dest, source in instructions.items():
        new = assoc_in(new, list(dest), get_in(source, mapping))

    return new


def transform_section(mapping):
    transformers = {
        "pitch": separate_attrs,
        "roll": separate_attrs,
        "yaw": separate_attrs,
        "pitch_error": lambda arr: np.asarray(arr, dtype=bool),
        "roll_error": lambda arr: np.asarray(arr, dtype=bool),
        "yaw_error": lambda arr: np.asarray(arr, dtype=bool),
    }

    return apply_to_items(transformers, mapping)


def transform_attitude(mapping):
    transformers = {
        "time": transform_time,
        "attitude": transform_section,
        "rates": transform_section,
    }

    result = pipe(
        mapping,
        curry(get, "data_points"),
        curry(transpose_nested),
        curry(apply_to_items, transformers),
        curry(prepend_dim, "points"),
        curry(copy, {("attitude", "time"): ["time"], ("rates", "time"): ["time"]}),
        curry(dissoc, ["time"]),
        curry(valmap, lambda x: (x, {"coordinates": ["time"]})),
        curry(as_group),
    )

    return result
