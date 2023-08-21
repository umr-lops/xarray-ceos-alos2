from construct import Enum, Struct, this
from tlz.dicttoolz import valmap
from tlz.functoolz import curry, pipe

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString
from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.transformers import as_group, remove_spares
from ceos_alos2.utils import rename

facility_related_data_record = Struct(
    "preamble" / record_preamble,
    "record_sequence_number" / AsciiInteger(4),
    "blanks" / PaddedString(50),
    "raw_file_data" / PaddedString(this.preamble.record_length - 12 - 4 - 50),
)
facility_related_data_5_record = Struct(
    "preamble" / record_preamble,
    "record_sequence_number" / AsciiInteger(4),
    "conversion_from_map_projection_to_pixel"
    / Metadata(
        Struct(
            "a" / AsciiFloat(20)[10],
            "b" / AsciiFloat(20)[10],
        ),
        formula=(
            "P = a0 + a1*φ + a2*λ + a3*φ*λ + a4*φ^2 + a5*λ^2 + a6*φ^2*λ + a7*φ*λ^2 + a8*φ^3 + a9*λ^3;"
            " L = b0 + b1*φ + b2*λ + b3*φ*λ + b4*φ^2 + b5*λ^2 + b6*φ^2*λ + b7*φ*λ^2 + b8*φ^3 + b9*λ^3"
        ),
    ),
    "calibration_mode_data_location_flag"
    / Enum(
        AsciiInteger(4),
        no_calibration=0,
        side_of_observation_start=1,
        side_of_observation_end=2,
        side_of_observation_start_and_end=3,
    ),
    "calibration_at_upper_image"
    / Struct(
        "start_line_number" / AsciiInteger(8),
        "end_line_number" / AsciiInteger(8),
    ),
    "calibration_at_bottom_image"
    / Struct(
        "start_line_number" / AsciiInteger(8),
        "end_line_number" / AsciiInteger(8),
    ),
    "prf_switching_flag" / AsciiInteger(4),
    "start_line_number_of_prf_switching" / AsciiInteger(8),
    "blanks1" / PaddedString(8),
    "number_of_loss_lines"
    / Struct(
        "level1.0" / AsciiInteger(8),
        "others" / AsciiInteger(8),
    ),
    "blanks2" / PaddedString(312),
    "system_reserve" / PaddedString(224),
    "conversion_from_pixel_to_geographic"
    / Metadata(
        Struct(
            "a" / AsciiFloat(20)[25],
            "b" / AsciiFloat(20)[25],
            "origin_pixel" / AsciiFloat(20),
            "origin_line" / AsciiFloat(20),
        ),
        formula=(
            (
                "φ = a0*L^4*P^4 + a1*L^3*P^4 + a2*L^2*P^4 + a3*L*P^4 + a4*P^4"
                " + a5*L^4*P^3 + a6*L^3*P^3 + a7*L^2*P^3 + a8*L*P^3 + a9*P^3"
                " + a10*L^4*P^2 + a11*L^3*P^2 + a12*L^2*P^2 + a13*L*P^2 + a14*P^2"
                " + a15*L^4*P + a16*L^3*P + a17*L^2*P + a18*L*P + a19*P"
                " + a20*L^4 + a21*L^3 + a22*L^2 + a23*L + a24"
            )
            + "; "
            + (
                "λ = b0*L^4*P^4 + b1*L^3*P^4 + b2*L^2*P^4 + b3*L*P^4 + b4*P^4"
                " + b5*L^4*P^3 + b6*L^3*P^3 + b7*L^2*P^3 + b8*L*P^3 + b9*P^3"
                " + b10*L^4*P^2 + b11*L^3*P^2 + b12*L^2*P^2 + b13*L*P^2 + b14*P^2"
                " + b15*L^4*P + b16*L^3*P + b17*L^2*P + b18*L*P + b19*P"
                " + b20*L^4 + b21*L^3 + b22*L^2 + b23*L + b24"
            )
        ),
    ),
    "conversion_from_geographic_to_pixel"
    / Metadata(
        Struct(
            "c" / AsciiFloat(20)[25],
            "d" / AsciiFloat(20)[25],
            "origin_latitude" / AsciiFloat(20),
            "origin_longitude" / AsciiFloat(20),
        ),
        formula=(
            (
                "p = c0*Λ^4*Φ^4 + c1*Λ^3*Φ^4 + c2*Λ^2*Φ^4 + c3*Λ*Φ^4 + c4*Φ^4"
                " + c5*Λ^4*Φ^3 + c6*Λ^3*Φ^3 + c7*Λ^2*Φ^3 + c8*Λ*Φ^3 + c9*Φ^3"
                " + c10*Λ^4*Φ^2 + c11*Λ^3*Φ^2 + c12*Λ^2*Φ^2 + c13*Λ*Φ^2 + c14*Φ^2"
                " + c15*Λ^4*Φ + c16*Λ^3*Φ + c17*Λ^2*Φ + c18*Λ*Φ + c19*Φ"
            )
            + "; "
            + (
                "l = d0*Λ^4*Φ^4 + d1*Λ^3*Φ^4 + d2*Λ^2*Φ^4 + d3*Λ*Φ^4 + d4*Φ^4"
                " + d5*Λ^4*Φ^3 + d6*Λ^3*Φ^3 + d7*Λ^2*Φ^3 + d8*Λ*Φ^3 + d9*Φ^3"
                " + d10*Λ^4*Φ^2 + d11*Λ^3*Φ^2 + d12*Λ^2*Φ^2 + d13*Λ*Φ^2 + d14*Φ^2"
                " + d15*Λ^4*Φ + d16*Λ^3*Φ + d17*Λ^2*Φ + d18*Λ*Φ + d19*Φ"
                " + d20*Λ^4 + d21*Λ^3 + d22*Λ^2 + d23*Λ + d24"
            )
        ),
    ),
    "blanks" / PaddedString(1896),
)


def transform_auxiliary_file(mapping):
    ignored = ["preamble"]

    data_types = {
        1: "dummy data",
        2: "determined ephemeris",
        3: "time error information",
        4: "coordinate conversion information",
    }
    transformers = {"record_sequence_number": data_types.get}
    translations = {"record_sequence_number": "data_type"}

    return pipe(
        mapping,
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
    )


def transform_group(mapping, dim):
    def attach_dim(value):
        if not isinstance(value, list):
            return (), value, {}
        return dim, value, {}

    mapping, attrs = mapping

    return valmap(attach_dim, mapping), attrs


def transform_record5(mapping):
    ignored = ["preamble", "record_sequence_number", "system_reserve"]

    transformers = {
        "prf_switching_flag": bool,
        "conversion_from_map_projection_to_pixel": curry(
            transform_group, dim="mid_precision_coeffs"
        ),
        "conversion_from_pixel_to_geographic": curry(transform_group, dim="high_precision_coeffs"),
        "conversion_from_geographic_to_pixel": curry(transform_group, dim="high_precision_coeffs"),
    }

    translations = {
        "conversion_from_map_projection_to_pixel": "projected_to_image",
        "conversion_from_pixel_to_geographic": "image_to_geographic",
        "conversion_from_geographic_to_pixel": "geographic_to_image",
        "prf_switching_flag": "prf_switching",
    }

    return pipe(
        mapping,
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        curry(as_group),
    )
