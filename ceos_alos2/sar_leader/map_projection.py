from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiFloat, AsciiInteger, Metadata, PaddedString

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
        "reference_ellipsoid_name" / PaddedString(32),
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
    "map_projection_description" / PaddedString(32),
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
            "top_left_corder" / projected_map_point,
            "top_right_corner" / projected_map_point,
            "bottom_right_corner" / projected_map_point,
            "bottom_left_corner" / projected_map_point,
        ),
        "geographic"
        / Struct(
            "top_left_corder" / geographic_map_point,
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
                "A11" / AsciiFloat(16),
                "A12" / AsciiFloat(16),
                "A13" / AsciiFloat(16),
                "A14" / AsciiFloat(16),
                "A21" / AsciiFloat(16),
                "A22" / AsciiFloat(16),
                "A23" / AsciiFloat(16),
                "A24" / AsciiFloat(16),
            ),
            formula=(
                "E = A11 + A12 * L + A13 * P + A14 * L * P;"
                " N = A21 + A22 * L + A23 * P + A24 * L * P"
            ),
        ),
        "pixels_to_map_projection"
        / Metadata(
            Struct(
                "B11" / AsciiFloat(16),
                "B12" / AsciiFloat(16),
                "B13" / AsciiFloat(16),
                "B14" / AsciiFloat(16),
                "B21" / AsciiFloat(16),
                "B22" / AsciiFloat(16),
                "B23" / AsciiFloat(16),
                "B24" / AsciiFloat(16),
            ),
            formula=(
                "L = B11 + B12 * E + B13 * N + B14 * E * N;"
                " P = B21 + B22 * E + B23 * N + B24 * E * N",
            ),
        ),
    ),
    "blanks" / PaddedString(36),
)
