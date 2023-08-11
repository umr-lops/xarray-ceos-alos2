from construct import Enum, Struct
from tlz.functoolz import curry, pipe

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import (
    AsciiFloat,
    AsciiInteger,
    Factor,
    Metadata,
    PaddedString,
)
from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.transformers import as_group, normalize_datetime, remove_spares
from ceos_alos2.utils import rename

motion_compensation = Enum(
    AsciiInteger(2),
    no_compensation=0,
    on_board_compensation=1,
    in_processor_compensation=10,
    both=11,
)
chirp_extraction_index = Enum(AsciiInteger(8), linear_up=0, linear_down=1, linear_up_and_down=2)
flag = Enum(PaddedString(4), yes="YES", no="NO", on="ON", off="OFF")
weighting_functions = Enum(PaddedString(32), rectangle="1")

dataset_summary_record = Struct(
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
    "motion_compensation_indicator" / motion_compensation,
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
    "base_band_conversion_flag" / flag,
    "range_compression_flag" / flag,
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
    "echo_tracker_status" / flag,
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
    "weighting_function_in_azimuth" / weighting_functions,
    "weighting_function_in_range" / weighting_functions,
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
    "clutter_lock_applied_flag" / flag,
    "auto_focusing_applied_flag" / flag,
    "line_spacing" / Metadata(AsciiFloat(16), units="m"),
    "pixel_spacing" / Metadata(AsciiFloat(16), units="m"),
    "processor_range_compression_designator" / PaddedString(16),
    "doppler_frequency_approximately_constant_coefficient_term"
    / Metadata(AsciiFloat(16), units="Hz"),
    "doppler_frequency_approximately_linear_coefficient_term"
    / Metadata(AsciiFloat(16), units="Hz/km"),
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
    "parameter_table_number_of_automatically_setting" / AsciiInteger(4),
    "nominal_off_nadir_angle" / AsciiFloat(16),
    "antenna_beam_number" / AsciiInteger(4),
    "spare12" / PaddedString(28),
    "incidence_angle"
    / Metadata(
        Struct(
            "constant_term" / Metadata(AsciiFloat(20), units="rad"),
            "linear_term" / Metadata(AsciiFloat(20), units="rad/km"),
            "quadratic_term" / Metadata(AsciiFloat(20), units="rad/km^2"),
            "cubic_term" / Metadata(AsciiFloat(20), units="rad/km^3"),
            "fourth_term" / Metadata(AsciiFloat(20), units="rad/km^4"),
            "fifth_term" / Metadata(AsciiFloat(20), units="rad/km^5"),
        ),
        formula="θ = a0 + a1*R + a2*R^2 + a3*R^3 + a4*R^4 + a5*R^5",
        theta="incidence angle",
        r="slant range",
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


def transform_dataset_summary(mapping):
    ignored = [
        "preamble",
        "dataset_summary_records_sequence_number",
        "sar_channel_id",
        "number_of_scene_reference",
        "average_terrain_height_above_ellipsoid_at_scene_center",
        "processing_scene_length",
        "processing_scene_width",
        "range_pulse_phase_coefficients",
        "processing_code_of_processing_facility",
        "processing_algorithm_id",
        "radiometric_bias",
        "radiometric_gain",
        "time_direction_indicator_along_pixel_direction",
        "parameter_table_number_of_automatically_setting",
        "image_annotation_segment",
    ]
    transformers = {
        "scene_center_time": normalize_datetime,
    }
    translations = {}

    result = pipe(
        mapping,
        curry(remove_spares),
        curry(dissoc, ignored),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        curry(as_group),
    )

    return result
