from construct import Struct, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString

attitude_point = Struct(
    "day_of_year" / AsciiInteger(4),
    "millisecond_of_day" / Metadata(AsciiInteger(8), units="ms"),
    "attitude_quality_flags"
    / Struct(
        "pitch" / AsciiInteger(4),
        "roll" / AsciiInteger(4),
        "yaw" / AsciiInteger(4),
    ),
    "attitude"
    / Struct(
        "pitch" / Metadata(AsciiFloat(14), units="deg"),
        "roll" / Metadata(AsciiFloat(14), units="deg"),
        "yaw" / Metadata(AsciiFloat(14), units="deg"),
    ),
    "rate_quality_flags"
    / Struct(
        "pitch" / AsciiInteger(4),
        "roll" / AsciiInteger(4),
        "yaw" / AsciiInteger(4),
    ),
    "rates"
    / Struct(
        "pitch" / Metadata(AsciiFloat(14), units="deg/s"),
        "roll" / Metadata(AsciiFloat(14), units="deg/s"),
        "yaw" / Metadata(AsciiFloat(14), units="deg/s"),
    ),
)

attitude_record = Struct(
    "preamble" / record_preamble,
    "number_of_points" / AsciiInteger(4),
    "data_points" / attitude_point[62],
    "blanks" / PaddedString(this.preamble.record_length - (12 + 4 + this.number_of_points * 120)),
)
