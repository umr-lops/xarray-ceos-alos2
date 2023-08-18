import datetime as dt

from construct import Enum, Struct
from tlz.dicttoolz import merge_with, valmap
from tlz.functoolz import compose_left, curry, pipe
from tlz.itertoolz import cons

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString
from ceos_alos2.dicttoolz import apply_to_items, dissoc, move_items
from ceos_alos2.transformers import as_group, remove_spares, separate_attrs
from ceos_alos2.utils import rename, starcall

orbital_elements_designator = Enum(
    PaddedString(32), preliminary="0", decision="1", high_precision="2"
)
orbit_point = Struct(
    "position"
    / Struct(
        "x" / Metadata(AsciiFloat(22), units="m"),
        "y" / Metadata(AsciiFloat(22), units="m"),
        "z" / Metadata(AsciiFloat(22), units="m"),
    ),
    "velocity"
    / Struct(
        "x" / Metadata(AsciiFloat(22), units="m/s"),
        "y" / Metadata(AsciiFloat(22), units="m/s"),
        "z" / Metadata(AsciiFloat(22), units="m/s"),
    ),
)
platform_position_record = Struct(
    "preamble" / record_preamble,
    "orbital_elements_designator" / orbital_elements_designator,
    "orbital_elements"
    / Struct(
        "position"
        / Struct(
            "x" / Metadata(AsciiFloat(16), units="m"),
            "y" / Metadata(AsciiFloat(16), units="m"),
            "z" / Metadata(AsciiFloat(16), units="m"),
        ),
        "velocity"
        / Struct(
            "x" / Metadata(AsciiFloat(16), units="m/s"),
            "y" / Metadata(AsciiFloat(16), units="m/s"),
            "z" / Metadata(AsciiFloat(16), units="m/s"),
        ),
    ),
    "number_of_data_points" / AsciiInteger(4),
    "datetime_of_first_point"
    / Struct(
        "date" / PaddedString(12),
        "day_of_year" / AsciiInteger(4),
        "seconds_of_day" / AsciiFloat(22),
    ),
    "time_interval_between_data_points" / Metadata(AsciiFloat(22), units="s"),
    "reference_coordinate_system" / PaddedString(64),
    "greenwich_mean_hour_angle" / Metadata(AsciiFloat(22), units="deg"),
    "nominal_error"
    / Struct(
        "position"
        / Struct(
            "along_track" / Metadata(AsciiFloat(16), units="m"),
            "across_track" / Metadata(AsciiFloat(16), units="m"),
            "radial" / Metadata(AsciiFloat(16), units="m"),
        ),
        "velocity"
        / Struct(
            "along_track" / Metadata(AsciiFloat(16), units="m/s"),
            "across_track" / Metadata(AsciiFloat(16), units="m/s"),
            "radial" / Metadata(AsciiFloat(16), units="m/s"),
        ),
    ),
    "positions" / orbit_point[28],
    "blanks1" / PaddedString(18),
    "occurrence_flag_of_a_leap_second" / AsciiInteger(1),
    "blanks2" / PaddedString(579),
)


def transform_composite_datetime(mapping):
    date_str = "-".join(mapping["date"].split())
    date = dt.datetime.strptime(date_str, "%Y-%m-%d")
    timedelta = dt.timedelta(seconds=mapping["seconds_of_day"])

    datetime = date + timedelta

    return datetime.isoformat()


def transform_positions(elements):
    result = pipe(
        elements,
        curry(starcall, curry(merge_with, list)),
        curry(
            valmap,
            compose_left(
                curry(starcall, curry(merge_with, list)),
                curry(valmap, compose_left(separate_attrs, curry(cons, ["positions"]), tuple)),
            ),
        ),
    )
    return result


def transform_platform_position(mapping):
    ignored = ["preamble", "number_of_data_points", "greenwich_mean_hour_angle"]
    transformers = {
        "datetime_of_first_point": transform_composite_datetime,
        "positions": transform_positions,
        "occurrence_flag_of_a_leap_second": bool,
    }
    translations = {
        "occurrence_flag_of_a_leap_second": "leap_second",
        "time_interval_between_data_points": "sampling_frequency",
    }

    result = pipe(
        mapping,
        curry(dissoc, ignored),
        curry(remove_spares),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        curry(move_items, {("orbital_elements", "type"): ["orbital_elements_designator"]}),
        curry(as_group),
    )

    return result
