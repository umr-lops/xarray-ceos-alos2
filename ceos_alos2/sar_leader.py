from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import (
    AsciiFloat,
    AsciiInteger,
    Factor,
    Metadata,
    PaddedString,
)

record_types = {
    "dataset_summary": (18, 10, 18, 20),
    "map_projection_data": (18, 20, 18, 20),
    "platform_position_data": (18, 30, 18, 20),
    "attitude_data": (18, 40, 18, 20),
    "radiometric_data": (18, 50, 18, 20),
    "radiometric_compensation": (18, 51, 18, 20),
    "data_quality_summary": (18, 60, 18, 20),
    "data_histograms": (18, 70, 18, 20),
    "range_spectra": (18, 80, 18, 20),
    "digital_elevation_model_descriptor": (18, 90, 18, 20),
    "radar_parameter_data_update": (18, 100, 18, 20),
    "annotation_data": (18, 110, 18, 20),
    "detailed_processing_parameters": (18, 120, 18, 20),
    "calibration_data": (18, 130, 18, 20),
    "ground_control_points": (18, 140, 18, 20),
    "facility_related_data": (18, 200, 18, 20),
}

small_record_info = Struct(
    "number_of_records" / AsciiInteger(6),
    "record_length" / AsciiInteger(6),
)
big_record_info = Struct(
    "number_of_records" / AsciiInteger(6),
    "record_length" / AsciiInteger(8),
)
sar_leader_file_descriptor = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_flag" / PaddedString(2),
    "blanks" / PaddedString(2),
    "format_control_document_id" / PaddedString(12),
    "format_control_document_revision_level" / PaddedString(2),
    "record_format_revision_level" / PaddedString(2),
    "software_release_and_revision_number" / PaddedString(12),
    "file_number" / AsciiInteger(4),
    "file_id" / PaddedString(16),
    "record_sequence_and_location_type_flag" / PaddedString(4),
    "sequence_number_of_location" / AsciiInteger(8),
    "field_length_of_sequence_number" / AsciiInteger(4),
    "record_code_and_location_type_flag" / PaddedString(4),
    "location_of_record_code" / AsciiInteger(8),
    "field_length_of_record_code" / AsciiInteger(4),
    "record_length_and_location_type_flag" / PaddedString(4),
    "location_of_record_length" / AsciiInteger(8),
    "field_length_of_record_length" / AsciiInteger(4),
    "blanks1" / PaddedString(68),
    "dataset_summary" / small_record_info,
    "map_projection_data" / small_record_info,
    "platform_position" / small_record_info,
    "attitude_data" / small_record_info,
    "radiometric_data" / small_record_info,
    "radiometric_compensation" / small_record_info,
    "data_quality_summary" / small_record_info,
    "data_histogram" / small_record_info,
    "range_spectra" / small_record_info,
    "dem_descriptor" / small_record_info,
    "radar_parameter_update" / small_record_info,
    "annotation_data" / small_record_info,
    "detail_processing" / small_record_info,
    "calibration" / small_record_info,
    "gcp" / small_record_info,
    "spare" / PaddedString(60),
    "facility_data_1" / big_record_info,
    "facility_data_2" / big_record_info,
    "facility_data_3" / big_record_info,
    "facility_data_4" / big_record_info,
    "facility_data_5" / big_record_info,
    "blanks2" / PaddedString(230),
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
