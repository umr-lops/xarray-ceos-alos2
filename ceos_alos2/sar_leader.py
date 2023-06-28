from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import (
    AsciiFloat,
    AsciiInteger,
    Factor,
    Metadata,
    PaddedString,
)

dataset_summary = Struct(
    "preamble" / record_preamble,
    "dataset_summary_records_sequence_number" / AsciiInteger(4),
    "sar_channel_id" / PaddedString(4),
    "scene_id" / PaddedString(32),
    "number_of_scene_reference" / PaddedString(16),
    "scene_center_time" / PaddedString(32),
    "spare1" / PaddedString(16),
    "geodetic_latitude" / Metadata(AsciiFloat(16), units="deg"),
    "geodetic_longitude" / Metadata(AsciiFloat(16), units="deg"),
    "processed_scene_center_true_heading" / Metadata(AsciiFloat(16), units="deg"),
    "ellipsoid_designator" / PaddedString(16),
    "ellipsoid_semimajor_axis" / Metadata(AsciiFloat(16), units="km"),
    "ellipsoid_semiminor_axis" / Metadata(AsciiFloat(16), units="km"),
    "earth_mass" / Metadata(Factor(AsciiFloat(16), 1e24), units="kg"),
    "gravitational_constant" / Metadata(Factor(AsciiFloat(16), 1e-14), units="m^3 / s^2"),
    "ellipsoid_j2_parameter" / AsciiFloat(16),
    "ellipsoid_j3_parameter" / AsciiFloat(16),
    "ellipsoid_j4_parameter" / AsciiFloat(16),
    "spare2" / PaddedString(16),
    "average_terrain_height_above_ellipsoid_at_scene_center" / AsciiFloat(16),
    "scene_center_line_number" / AsciiInteger(8),
    "scene_center_pixel_number" / AsciiInteger(8),
    "processing_scene_length" / Metadata(AsciiFloat(16), units="km"),
    "processing_scene_width" / Metadata(AsciiFloat(16), units="km"),
    "spare3" / PaddedString(16),
    "number_of_sar_channel" / AsciiInteger(4),
    "spare4" / PaddedString(4),
    "sensor_platform_mission_identifier" / PaddedString(16),
    "sensor_id_and_operation_mode" / PaddedString(32),
    "orbit_number_or_flight_line_indicator" / AsciiInteger(8),
    "sensor_platform_geodetic_latitude_at_nadir_corresponding_to_scene_center"
    / Metadata(AsciiFloat(8), units="deg"),
    "sensor_platform_geodetic_longitude_at_nadir_corresponding_to_scene_center"
    / Metadata(AsciiFloat(8), units="deg"),
    "sensor_platform_heading_at_nadir_corresponding_to_scene_center"
    / Metadata(AsciiFloat(8), units="deg"),
    "sensor_clock_angle_as_measured_relative_to_sensor_platform_flight_direction"
    / Metadata(AsciiFloat(8), units="deg"),
    "incidence_angle_at_scene_center" / Metadata(AsciiFloat(8), units="deg"),
    "spare5" / PaddedString(8),
    "nominal_radar_wavelength" / Metadata(AsciiFloat(16), units="m"),
    "motion_compensation_indicator" / PaddedString(2),
    "range_pulse_code" / PaddedString(16),
    "range_pulse_amplitude_coefficients"
    / Struct(
        "coefficient_1" / AsciiFloat(16),
        "coefficient_2" / AsciiFloat(16),
        "coefficient_3" / AsciiFloat(16),
        "coefficient_4" / AsciiFloat(16),
        "coefficient_5" / AsciiFloat(16),
    ),
    "range_pulse_phase_coefficients"
    / Struct(
        "coefficient_1" / AsciiFloat(16),
        "coefficient_2" / AsciiFloat(16),
        "coefficient_3" / AsciiFloat(16),
        "coefficient_4" / AsciiFloat(16),
        "coefficient_5" / AsciiFloat(16),
    ),
    "down_linked_data_chirp_extraction_index" / AsciiInteger(8),
    "spare6" / PaddedString(8),
    "sampling_rate" / Metadata(AsciiFloat(16), units="MHz"),
    "range_gate" / Metadata(AsciiFloat(16), units="µs"),
    "range_pulse_width" / Metadata(AsciiFloat(16), units="µs"),
    "base_band_conversion_flag" / PaddedString(4),
    "range_compression_flag" / PaddedString(4),
    "receiver_gain_for_like_polarized_at_early_edge_at_the_start_of_the_image" / AsciiFloat(16),
    "receiver_gain_for_cross_polarized_at_early_edge_at_the_start_of_the_image" / AsciiFloat(16),
    "quantization_in_bits_per_channel" / AsciiInteger(8),
    "quantized_descriptor" / PaddedString(12),
    "dc_bias_for_I_component" / AsciiFloat(16),
    "dc_bias_for_Q_component" / AsciiFloat(16),
    "gain_imbalance_for_I_and_Q" / AsciiFloat(16),
    "spare7" / AsciiFloat(16),
    "spare8" / AsciiFloat(16),
    "electronic_boresight" / AsciiFloat(16),
    "mechanical_boresight" / AsciiFloat(16),
    "echo_tracker_status" / PaddedString(4),
    "prf" / Metadata(AsciiFloat(16), units="mHz"),
    "two_way_antenna_beam_width_elevation" / Metadata(AsciiFloat(16), units="deg"),
    "two_way_antenna_beam_width_azimuth" / Metadata(AsciiFloat(16), units="deg"),
    "satellite_encoded_binary_time_code" / AsciiInteger(16),
    "satellite_clock_time" / PaddedString(32),
    "satellite_clock_increment" / Metadata(AsciiInteger(16), units="ns"),
    "processing_facility_id" / PaddedString(16),
    "processing_system_id" / PaddedString(8),
    "processing_version_id" / PaddedString(8),
    "processing_code_of_processing_facility" / PaddedString(16),
    "product_level_code" / PaddedString(16),
    "product_type_specifier" / PaddedString(32),
    "processing_algorithm_id" / PaddedString(32),
    "number_of_looks_in_azimuth" / AsciiFloat(16),
    "number_of_looks_in_range" / AsciiFloat(16),
    "bandwidth_per_look_in_azimuth" / Metadata(AsciiFloat(16), units="Hz"),
    "bandwidth_per_look_in_range" / Metadata(AsciiFloat(16), units="Hz"),
    "bandwidth_in_azimuth" / Metadata(AsciiFloat(16), units="Hz"),
    "bandwidth_in_range" / Metadata(AsciiFloat(16), units="kHz"),
    "weighting_function_in_azimuth" / PaddedString(32),
    "weighting_function_in_range" / PaddedString(32),
    "data_input_source" / PaddedString(16),
    "resolution_in_ground_range" / Metadata(AsciiFloat(16), units="m"),
    "resolution_in_azimuth" / Metadata(AsciiFloat(16), units="m"),
    "radiometric_bias" / AsciiFloat(16),
    "radiometric_gain" / AsciiFloat(16),
    "along_track_doppler_frequency_center"
    / Struct(
        "constant_term_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz"),
        "linear_coefficient_terms_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/px"),
        "quadratic_coefficient_terms_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/px^2"),
    ),
    "spare9" / PaddedString(16),
    "cross_track_doppler_frequency_center"
    / Struct(
        "constant_term_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz"),
        "linear_coefficient_terms_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/px"),
        "quadratic_coefficient_terms_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/px^2"),
    ),
    "time_direction_indicator_along_pixel_direction" / PaddedString(8),
    "time_direction_indicator_along_line_direction" / PaddedString(8),
    "along_track_doppler_frequency_rate"
    / Struct(
        "constant_terms_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz/s"),
        "linear_coefficient_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz/s/px"),
        "quadratic_coefficient_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/s/px^2"),
    ),
    "spare10" / PaddedString(16),
    "cross_track_doppler_frequency_rate"
    / Struct(
        "constant_terms_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz/s"),
        "linear_coefficient_at_early_edge_of_the_image" / Metadata(AsciiFloat(16), units="Hz/s/px"),
        "quadratic_coefficient_at_early_edge_of_the_image"
        / Metadata(AsciiFloat(16), units="Hz/s/px^2"),
    ),
    "spare11" / PaddedString(16),
    "line_content_indicator" / PaddedString(8),
    "clutter_lock_applied_flag" / PaddedString(4),
    "auto_focusing_applied_flag" / PaddedString(4),
    "line_spacing" / Metadata(AsciiFloat(16), units="m"),
    "pixel_spacing" / Metadata(AsciiFloat(16), units="m"),
    "processor_range_compression_designator" / PaddedString(16),
    "doppler_frequency_approximately_constant_coefficient_term"
    / Metadata(AsciiFloat(16), units="Hz"),
    "doppler_frequency_approximately_linear_coefficient_term"
    / Metadata(AsciiFloat(16), units="Hz/km"),
    "sensor_specific_local_use_segment"
    / Struct(
        "calibration_mode_data_location_flag" / AsciiInteger(4),
        "calibration_at_the_side_of_start"
        / Struct(
            "start_line_number" / AsciiInteger(8),
            "end_line_number" / AsciiInteger(8),
        ),
        "calibration_at_the_side_of_end"
        / Struct(
            "start_line_number" / AsciiInteger(8),
            "end_line_number" / AsciiInteger(8),
        ),
        "prf_switching_indicator" / AsciiInteger(4),
        "line_number_of_prf_switching" / AsciiInteger(8),
        "direction_of_a_beam_center_in_a_scene_center" / Metadata(AsciiFloat(16), units="deg"),
        "yaw_steering_mode_flag" / AsciiInteger(4),
        "parameter_table_of_automatically_setting" / AsciiInteger(4),
        "nominal_off_nadir_angle" / AsciiFloat(16),
        "antenna_beam_number" / AsciiInteger(4),
        "spare" / PaddedString(28),
    ),
    "processing_specific_local_use_segment"
    / Struct(
        "incidence_angle"
        / Struct(
            "constant_term" / Metadata(AsciiFloat(20), units="rad"),
            "linear_term" / Metadata(AsciiFloat(20), units="rad/km"),
            "quadratic_term" / Metadata(AsciiFloat(20), units="rad/km^2"),
            "cubic_term" / Metadata(AsciiFloat(20), units="rad/km^3"),
            "fourth_term" / Metadata(AsciiFloat(20), units="rad/km^4"),
            "fifth_term" / Metadata(AsciiFloat(20), units="rad/km^5"),
        ),
    ),
    "image_annotation_segment"
    / Struct(
        "number_of_annotation_points" / AsciiInteger(8),
        "spare" / PaddedString(8),
        "annotations"
        / Struct(
            "line_number_of_annotation_start" / AsciiInteger(8),
            "pixel_number_of_annotation_start" / AsciiInteger(8),
            "annotation_text" / PaddedString(16),
        )[64],
        "system_reserve" / PaddedString(26),
    ),
)

projected_map_point = Struct(
    "northing" / Metadata(AsciiFloat(16), units="km"),
    "easting" / Metadata(AsciiFloat(16), units="km"),
)
geographic_map_point = Struct(
    "latitude" / Metadata(AsciiFloat(16), units="deg"),
    "longitude" / Metadata(AsciiFloat(16), units="deg"),
)
map_projection = Struct(
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
