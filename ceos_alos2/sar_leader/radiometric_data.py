from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import (
    AsciiComplex,
    AsciiFloat,
    AsciiInteger,
    Metadata,
    PaddedString,
)

radiometric_data_record = Struct(
    "preamble" / record_preamble,
    "radiometric_data_records_sequence_number" / AsciiInteger(4),
    "number_of_radiometric_fields" / AsciiInteger(4),
    "calibration_factor"
    / Metadata(
        AsciiFloat(16),
        formula=(
            "σ⁰=10*log_10(I^2 + Q^2) + CF - 32.0;" " σ⁰(level1.5/level3.1)=10*log_10(DN^2) + CF"
        ),
        I="level 1.1 real pixel value",
        Q="level 1.1 imaginary pixel value",
        DN="level 1.5/3.1 pixel value",
    ),
    "distortion_matrix"
    / Metadata(
        Struct(
            "transmission"
            / Struct(
                "dt11" / AsciiComplex(32),
                "dt12" / AsciiComplex(32),
                "dt21" / AsciiComplex(32),
                "dt22" / AsciiComplex(32),
            ),
            "reception"
            / Struct(
                "dr11" / AsciiComplex(32),
                "dr12" / AsciiComplex(32),
                "dr21" / AsciiComplex(32),
                "dr22" / AsciiComplex(32),
            ),
        ),
        formula="Z = A*1/r*exp(-4πr/λ) * RST + N",
        Z="measurement matrix",
        A="amplitude",
        r="slant range",
        S="true scattering matrix",
        N="noise component",
        R="reception distortion matrix",
        T="transmission distortion matrix",
    ),
    "blanks" / PaddedString(9568),
)
