import operator

from construct import Struct
from tlz.dicttoolz import merge_with, valmap
from tlz.functoolz import curry, pipe
from tlz.itertoolz import cons, get, remove

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString
from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.transformers import as_group, remove_spares
from ceos_alos2.utils import rename

projected_map_point = Struct(
    "northing" / Metadata(AsciiFloat(16), units="km"),
    "easting" / Metadata(AsciiFloat(16), units="km"),
)
geographic_map_point = Struct(
    "latitude" / Metadata(AsciiFloat(16), units="deg"),
    "longitude" / Metadata(AsciiFloat(16), units="deg"),
)
map_projection_record = Struct(
    "preamble" / record_preamble,
    "blanks" / PaddedString(16),
    "map_projection_general_information"
    / Struct(
        "map_projection_type" / PaddedString(32),
        "number_of_pixels_per_line" / AsciiInteger(16),
        "number_of_lines" / AsciiInteger(16),
        "inter_line_distance_in_output_scene" / Metadata(AsciiFloat(16), units="m"),
        "inter_pixel_distance_in_output_scene" / Metadata(AsciiFloat(16), units="m"),
        "angle_between_projection_aixs_from_true_north_at_processed_scene_center"
        / Metadata(AsciiFloat(16), units="deg"),
        "actual_platform_orbital_inclination" / Metadata(AsciiFloat(16), units="deg"),
        "actual_ascending_node" / Metadata(AsciiFloat(16), units="deg"),
        "distance_of_platform_at_input_scene_center_from_geocenter"
        / Metadata(AsciiFloat(16), units="m"),
        "geodetic_altitude_of_the_platform_relative_to_the_ellipsoid"
        / Metadata(AsciiFloat(16), units="m"),
        "actual_ground_speed_at_nadir_at_input_scene_center_time"
        / Metadata(AsciiFloat(16), units="m/s"),
        "platform_headings" / Metadata(AsciiFloat(16), units="deg"),
    ),
    "map_projection_ellipsoid_parameters"
    / Struct(
        "reference_ellipsoid" / PaddedString(32),
        "semimajor_axis" / Metadata(AsciiFloat(16), units="m"),
        "semiminor_axis" / Metadata(AsciiFloat(16), units="m"),
        "datum_shift_parameters"
        / Struct(
            "dx" / Metadata(AsciiFloat(16), units="m"),
            "dy" / Metadata(AsciiFloat(16), units="m"),
            "dz" / Metadata(AsciiFloat(16), units="m"),
            "rotation_angle_1" / Metadata(AsciiFloat(16), units="deg"),
            "rotation_angle_2" / Metadata(AsciiFloat(16), units="deg"),
            "rotation_angle_3" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "scale_factor" / AsciiFloat(16),
    ),
    "map_projection_designator" / PaddedString(32),
    "utm_projection"
    / Struct(
        "type" / PaddedString(32),
        "zone_number" / PaddedString(4),
        "map_origin"
        / Struct(
            "false_easting" / Metadata(AsciiFloat(16), units="m"),
            "false_northing" / Metadata(AsciiFloat(16), units="m"),
        ),
        "center_of_projection"
        / Struct(
            "longitude" / Metadata(AsciiFloat(16), units="deg"),
            "latitude" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "blanks1" / PaddedString(16),
        "blanks2" / PaddedString(16),
        "scale_factor" / AsciiFloat(16),
    ),
    "ups_projection"
    / Struct(
        "type" / PaddedString(32),
        "center_of_projection"
        / Struct(
            "longitude" / Metadata(AsciiFloat(16), units="deg"),
            "latitude" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "scale_factor" / AsciiFloat(16),
    ),
    "national_system_projection"
    / Struct(
        "projection_descriptor" / PaddedString(32),
        "map_origin"
        / Struct(
            "false_easting" / Metadata(AsciiFloat(16), units="m"),
            "false_northing" / Metadata(AsciiFloat(16), units="m"),
        ),
        "center_of_projection"
        / Struct(
            "longitude" / Metadata(AsciiFloat(16), units="deg"),
            "latitude" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "standard_parallel"
        / Struct(
            "phi1" / Metadata(AsciiFloat(16), units="deg"),
            "phi2" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "standard_parallel2"
        / Struct(
            "param1" / Metadata(AsciiFloat(16), units="deg"),
            "param2" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "central_meridian"
        / Struct(
            "param1" / Metadata(AsciiFloat(16), units="deg"),
            "param2" / Metadata(AsciiFloat(16), units="deg"),
            "param3" / Metadata(AsciiFloat(16), units="deg"),
        ),
        "blanks" / PaddedString(64),
    ),
    "corner_points"
    / Struct(
        "projected"
        / Struct(
            "top_left_corner" / projected_map_point,
            "top_right_corner" / projected_map_point,
            "bottom_right_corner" / projected_map_point,
            "bottom_left_corner" / projected_map_point,
        ),
        "geographic"
        / Struct(
            "top_left_corner" / geographic_map_point,
            "top_right_corner" / geographic_map_point,
            "bottom_right_corner" / geographic_map_point,
            "bottom_left_corner" / geographic_map_point,
        ),
        "terrain_heights_relative_to_ellipsoid"
        / Struct(
            "top_left_corner" / Metadata(AsciiFloat(16), units="deg"),
            "top_right_corner" / Metadata(AsciiFloat(16), units="deg"),
            "bottom_right_corner" / Metadata(AsciiFloat(16), units="deg"),
            "bottom_left_corner" / Metadata(AsciiFloat(16), units="deg"),
        ),
    ),
    "conversion_coefficients"
    / Struct(
        "map_projection_to_pixels"
        / Metadata(
            Struct(
                "A11" / AsciiFloat(20),
                "A12" / AsciiFloat(20),
                "A13" / AsciiFloat(20),
                "A14" / AsciiFloat(20),
                "A21" / AsciiFloat(20),
                "A22" / AsciiFloat(20),
                "A23" / AsciiFloat(20),
                "A24" / AsciiFloat(20),
            ),
            formula=(
                "E = A11 + A12 * R + A13 * C + A14 * R * C;"
                " N = A21 + A22 * R + A23 * C + A24 * R * C"
            ),
            E="easting",
            N="northing",
            R="row (1-based)",
            C="column (1-based)",
        ),
        "pixels_to_map_projection"
        / Metadata(
            Struct(
                "B11" / AsciiFloat(20),
                "B12" / AsciiFloat(20),
                "B13" / AsciiFloat(20),
                "B14" / AsciiFloat(20),
                "B21" / AsciiFloat(20),
                "B22" / AsciiFloat(20),
                "B23" / AsciiFloat(20),
                "B24" / AsciiFloat(20),
            ),
            formula=(
                "R = B11 + B12 * E + B13 * N + B14 * E * N;"
                " C = B21 + B22 * E + B23 * N + B24 * E * N"
            ),
            E="easting",
            N="northing",
            R="row (1-based)",
            C="column (1-based)",
        ),
    ),
    "blanks" / PaddedString(36),
)


def filter_map_projection(mapping):
    all_projections = ["utm_projection", "ups_projection", "national_system_projection"]
    raw_designator = mapping.get("map_projection_designator")
    if raw_designator is None:
        return mapping

    designator, _ = raw_designator.lower().split("-", 1)

    sections = {
        "utm": "utm_projection",
        "ups": "ups_projection",
        "lcc": "national_system_projection",
        "mer": "national_system_projection",
    }
    to_keep = sections.get(designator)
    to_drop = list(
        cons("map_projection_designator", remove(lambda k: k == to_keep, all_projections))
    )

    return pipe(
        mapping,
        curry(dissoc, to_drop),
        curry(rename, translations={to_keep: "projection"}),
    )


def transform_general_info(mapping):
    translations = {
        "number_of_pixels_per_line": "n_columns",
        "number_of_lines": "n_rows",
    }

    return pipe(
        mapping,
        curry(rename, translations=translations),
    )


def transform_ellipsoid_parameters(mapping):
    # fixed to 0.0
    ignored = ["datum_shift_parameters", "scale_factor"]

    return dissoc(ignored, mapping)


def transform_projection(mapping):
    ignored = ["map_origin", "standard_parallel2", "central_meridian"]

    return dissoc(ignored, mapping)


def transform_corner_points(mapping):
    coordinate = ["top_left", "top_right", "bottom_right", "bottom_left"]
    keys = [f"{v}_corner" for v in coordinate]

    def separate_attrs(data):
        values, metadata_ = zip(*data)
        metadata = metadata_[0]

        return ["corner"], list(values), metadata

    def combine_corners(mapping):
        items = get(keys, mapping)
        merged = merge_with(list, *items)
        processed = valmap(separate_attrs, merged)

        return processed

    ignored = ["terrain_heights_relative_to_ellipsoid"]

    transformers = {
        "projected": curry(operator.or_, {"corner": (["corner"], coordinate, {})}),
        "geographic": curry(operator.or_, {"corner": (["corner"], coordinate, {})}),
    }

    result = pipe(
        mapping,
        curry(dissoc, ignored),
        curry(valmap, combine_corners),
        curry(apply_to_items, transformers),
    )
    return result


def transform_conversion_coefficients(mapping):
    def transform_coeffs(entry):
        raw_data, attrs = entry

        names, coeffs = zip(*raw_data.items())

        data = {"names": ("names", list(names), {}), "coefficients": ("names", list(coeffs), {})}
        return data, attrs

    translations = {
        "map_projection_to_pixels": "projected_to_image",
        "pixels_to_map_projection": "image_to_projected",
    }

    return pipe(
        mapping,
        curry(valmap, transform_coeffs),
        curry(rename, translations=translations),
    )


def transform_map_projection(mapping):
    ignored = ["preamble"]
    transformers = {
        "map_projection_general_information": transform_general_info,
        "map_projection_ellipsoid_parameters": transform_ellipsoid_parameters,
        "projection": transform_projection,
        "corner_points": transform_corner_points,
        "conversion_coefficients": transform_conversion_coefficients,
    }
    translations = {
        "map_projection_general_information": "general_information",
        "map_projection_ellipsoid_parameters": "ellipsoid_parameters",
    }

    result = pipe(
        mapping,
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(filter_map_projection),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        curry(as_group),
    )

    return result
