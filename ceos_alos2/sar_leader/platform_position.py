from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString

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
platform_position_data = Struct(
    "preamble" / record_preamble,
    "orbital_elements_designator" / PaddedString(32),
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
    "date_of_first_point" / PaddedString(12),
    "day_of_year_of_first_point" / AsciiInteger(4),
    "seconds_of_day_of_first_point" / AsciiFloat(22),
    "time_interval_between_data_points" / Metadata(AsciiFloat(22), units="s"),
    "reference_coordinate_system" / PaddedString(64),
    "greenwich_mean_hour_angle" / Metadata(AsciiFloat(22), units="deg"),
    "nominal_position_error"
    / Struct(
        "along_track" / Metadata(AsciiFloat(16), units="m"),
        "across_track" / Metadata(AsciiFloat(16), units="m"),
        "radial" / Metadata(AsciiFloat(16), units="m"),
    ),
    "nominal_velocity_error"
    / Struct(
        "along_track" / Metadata(AsciiFloat(16), units="m/s"),
        "across_track" / Metadata(AsciiFloat(16), units="m/s"),
        "radial" / Metadata(AsciiFloat(16), units="m/s"),
    ),
    "data_points" / orbit_point[28],
    "blanks1" / PaddedString(18),
    "occurrence_flag_of_a_leap_second" / AsciiInteger(1),
    "blanks2" / PaddedString(579),
)
