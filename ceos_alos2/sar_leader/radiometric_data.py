from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiComplex, AsciiFloat, AsciiInteger, PaddedString

radiometric_data_record = Struct(
    "preamble" / record_preamble,
    "radiometric_data_records_sequence_number" / AsciiInteger(4),
    "number_of_radiometric_fields" / AsciiInteger(4),
    "calibration_factor" / AsciiFloat(16),
    "transmission_distortion_matrix"
    / Struct(
        "dt11" / AsciiComplex(32),
        "dt12" / AsciiComplex(32),
        "dt21" / AsciiComplex(32),
        "dt22" / AsciiComplex(32),
    ),
    "reception_distortion_matrix"
    / Struct(
        "dr11" / AsciiComplex(32),
        "dr12" / AsciiComplex(32),
        "dr21" / AsciiComplex(32),
        "dr22" / AsciiComplex(32),
    ),
    "blanks" / PaddedString(9568),
)
