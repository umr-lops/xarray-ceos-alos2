from construct import Bytes, Computed, Int32ub, Int64ub, Seek, Struct, Tell, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import (
    DatetimeYdms,
    DatetimeYdus,
    Factor,
    Metadata,
    StripNullBytes,
)
from ceos_alos2.sar_image.enums import (
    Flag,
    chirp_type_designator,
    platform_position_parameters_update,
    pulse_polarization,
    sar_channel_code,
    sar_channel_id,
)

signal_data_record = Struct(
    "record_start" / Tell,
    "preamble" / record_preamble,
    "sar_image_data_line_number" / Int32ub,
    "sar_image_data_record_index" / Int32ub,
    "actual_count_of_left_fill_pixels" / Int32ub,
    "actual_count_of_data_pixels" / Int32ub,
    "actual_count_of_right_fill_pixels" / Int32ub,
    "sensor_parameters_update_flag" / Int32ub,
    "sensor_acquisition_date"
    / DatetimeYdms(
        Struct(
            "year" / Int32ub,
            "day_of_year" / Int32ub,
            "milliseconds" / Int32ub,
        )
    ),
    "sar_channel_id" / sar_channel_id,
    "sar_channel_code" / sar_channel_code,
    "transmitted_pulse_polarization" / pulse_polarization,
    "received_pulse_polarization" / pulse_polarization,
    "prf" / Metadata(Int32ub, units="mHz"),
    "scan_id" / Int32ub,
    "onboard_range_compressed_flag" / Flag(2),
    "chirp_type_designator" / chirp_type_designator,
    "chirp_length" / Metadata(Int32ub, units="ns"),
    "chirp_constant_coefficient" / Metadata(Int32ub, units="Hz"),
    "chirp_linear_coefficient" / Metadata(Int32ub, units="Hz/µs"),
    "chirp_quadratic_coefficient" / Metadata(Int32ub, units="Hz/µs^2"),
    "sensor_acquisition_date_microseconds" / DatetimeYdus(Int64ub, this.sensor_acquisition_date),
    "receiver_gain" / Metadata(Int32ub, units="dB"),
    "invalid_line_flag" / Flag(4),
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
    "blanks1" / Int32ub,
    "platform_position_parameters_update_flag" / platform_position_parameters_update,
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
    "latitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "latitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "latitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "burst_number" / Int32ub,
    "line_number_in_this_burst" / Int32ub,
    "blanks2" / StripNullBytes(Bytes(60)),
    "alos2_frame_number" / Int32ub,
    "palsar_auxiliary_data" / StripNullBytes(Bytes(256)),
    "data"
    / Struct(
        "start" / Tell,
        "size" / Computed(this._.preamble.record_length - (this.start - this._.record_start)),
        "stop" / Seek(this._.record_start + this._.preamble.record_length),
    ),
)
