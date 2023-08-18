from construct import Struct, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString

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
