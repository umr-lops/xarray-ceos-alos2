from construct import Struct, this
from tlz.dicttoolz import valmap
from tlz.functoolz import compose_left, curry, pipe
from tlz.itertoolz import cons, get

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString
from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.transformers import (
    as_group,
    remove_spares,
    separate_attrs,
    transform_nested,
)

calibration_uncertainty = Struct(
    "magnitude" / Metadata(AsciiFloat(16), units="dB"),
    "phase" / Metadata(AsciiFloat(16), units="deg"),
)
misregistration_error = Struct(
    "along_track" / Metadata(AsciiFloat(16), units="m"),
    "across_track" / Metadata(AsciiFloat(16), units="m"),
)
data_quality_summary_record = Struct(
    "preamble" / record_preamble,
    "record_number" / AsciiInteger(4),
    "sar_channel_id" / PaddedString(4),
    "date_of_the_last_calibration_update" / PaddedString(6),
    "number_of_channels" / AsciiInteger(4),
    "absolute_radiometric_data_quality"
    / Struct(
        "islr" / Metadata(AsciiFloat(16), units="dB"),
        "pslr" / Metadata(AsciiFloat(16), units="dB"),
        "azimuth_ambiguity_rate" / AsciiFloat(16),
        "range_ambiguity_rate" / AsciiFloat(16),
        "estimate_of_snr" / Metadata(AsciiFloat(16), units="dB"),
        "ber" / Metadata(AsciiFloat(16), units="dB"),
        "slant_range_resolution" / Metadata(AsciiFloat(16), units="m"),
        "azimuth_resolution" / Metadata(AsciiFloat(16), units="m"),
        "radiometric_resolution" / Metadata(AsciiFloat(16), units="dB"),
        "instantaneous_dynamic_range" / Metadata(AsciiFloat(16), units="dB"),
        "nominal_absolute_radiometric_calibration_uncertainty" / calibration_uncertainty,
    ),
    "relative_radiometric_quality"
    / Struct(
        # TODO: does that actually make sense?
        "nominal_relative_radiometric_calibration_uncertainty"
        / calibration_uncertainty[this._.number_of_channels],
        "blanks" / PaddedString(512 - this._.number_of_channels * 32),
    ),
    "absolute_geometric_quality"
    / Struct(
        "absolute_location_error"
        / Struct(
            "along_track" / Metadata(AsciiFloat(16), units="m"),
            "across_track" / Metadata(AsciiFloat(16), units="m"),
        ),
        "geometric_distortion_scale"
        / Struct(
            "line_direction" / AsciiFloat(16),
            "pixel_direction" / AsciiFloat(16),
        ),
        "geometric_distortion_skew" / AsciiFloat(16),
        "scene_orientation_error" / AsciiFloat(16),
    ),
    "relative_geometric_quality"
    / Struct(
        # TODO: does that actually make sense?
        "relative_misregistration_error" / misregistration_error[this._.number_of_channels],
        # TODO: 534 is 16 more than stated in the reference... is this on us or on JAXA?
        "blanks" / PaddedString(534 + (8 - this._.number_of_channels) * 32),
    ),
)


def transform_relative(mapping, key):
    return pipe(
        mapping,
        curry(get, key),
        curry(transform_nested),
        curry(valmap, compose_left(separate_attrs, curry(cons, "channel"), tuple)),
    )


def transform_data_quality_summary(mapping):
    ignored = ["preamble", "record_number"]
    transformers = {
        "relative_radiometric_quality": curry(
            transform_relative, key="nominal_relative_radiometric_calibration_uncertainty"
        ),
        "relative_geometric_quality": curry(
            transform_relative, key="relative_misregistration_error"
        ),
    }

    result = pipe(
        mapping,
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(apply_to_items, transformers),
        curry(as_group),
    )

    return result
