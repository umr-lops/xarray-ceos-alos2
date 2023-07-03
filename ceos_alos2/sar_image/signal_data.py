from construct import Bytes, Int16ub, Int32ub, Int64ub, Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import Factor, Metadata

signal_data_record = Struct(
    "preamble" / record_preamble,
    "general_information"
    / Struct(
        "sar_image_data_line_number" / Int32ub,
        "sar_image_data_record_index" / Int32ub,
        "actual_count_of_left_fill_pixels" / Int32ub,
        "actual_count_of_data_pixels" / Int32ub,
        "actual_count_of_right_fill_pixels" / Int32ub,
    ),
    "sensor_parameters"
    / Struct(
        "sensor_parameters_update_flag" / Int32ub,
        "sensor_acquisition"
        / Struct(
            "year" / Int32ub,
            "day_of_year" / Int32ub,
            "milliseconds_of_day" / Int32ub,
        ),
        "sar_channel_id" / Int16ub,
        "sar_channel_code" / Int16ub,
        "transmitted_pulse_polarization" / Int16ub,
        "received_pulse_polarization" / Int16ub,
        "prf" / Metadata(Int32ub, units="mHz"),
        "scan_id" / Int32ub,
        "onboard_range_compressed_flag" / Int16ub,
        "chirp_type_designator" / Int16ub,
        "chirp_length" / Metadata(Int32ub, units="ns"),
        "chirp_constant_coefficient" / Metadata(Int32ub, units="Hz"),
        "chirp_linear_coefficient" / Metadata(Int32ub, units="Hz/µs"),
        "chirp_quadratic_coefficient" / Metadata(Int32ub, units="Hz/µs^2"),
        "sensor_acquisition_microseconds_of_day" / Int64ub,
        "receiver_gain" / Metadata(Int32ub, units="dB"),
        "invalid_line_flag" / Int32ub,
        "elevation_angle_at_nadir_of_antenna"
        / Struct(
            "electronic" / Metadata(Int32ub, units="deg"),
            "mechanic" / Metadata(Int32ub, units="deg"),
        ),
        "antenna_squint_angle"
        / Struct(
            "electronic" / Metadata(Int32ub, units="deg"),
            "mechanic" / Metadata(Int32ub, units="deg"),
        ),
        "slant_range_to_first_data_sample" / Metadata(Int32ub, units="m"),
        "data_record_window_position" / Metadata(Int32ub, units="ns"),
        "spare" / Int32ub,
    ),
    "platform_reference_information"
    / Struct(
        "platform_position_parameters_update_flag" / Int32ub,
        "platform_latitude" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "platform_longitude" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "platform_altitude" / Metadata(Int32ub, units="deg"),
        "platform_ground_speed" / Metadata(Int32ub, units="cm/s"),
        "platform_velocity"
        / Struct(
            "x" / Metadata(Int32ub, units="cm/s"),
            "y" / Metadata(Int32ub, units="cm/s"),
            "z" / Metadata(Int32ub, units="cm/s"),
        ),
        "platform_acceleration"
        / Struct(
            "x" / Metadata(Int32ub, units="cm/s^2"),
            "y" / Metadata(Int32ub, units="cm/s^2"),
            "z" / Metadata(Int32ub, units="cm/s^2"),
        ),
        "platform_track_angle" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "platform_true_track_angle" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "platform_attitude"
        / Struct(
            "pitch" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
            "roll" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
            "yaw" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        ),
    ),
    "sensor_facility_specific_auxiliary_data"
    / Struct(
        "latitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "latitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "latitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "longitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "longitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
        "longitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    ),
    "scansar_burst_data_parameters"
    / Struct(
        "burst_number" / Int32ub,
        "line_number_in_this_burst" / Int32ub,
        "blanks" / Bytes(60),
        "alos2_frame_number" / Int32ub,
        "palsar_auxiliary_data" / Bytes(256),
    ),
)
