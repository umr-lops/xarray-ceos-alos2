from construct import Bytes, Computed, Int32ub, Seek, Struct, Tell, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import DatetimeYdms, Factor, Metadata, StripNullBytes
from ceos_alos2.sar_image.enums import (
    pulse_polarization,
    sar_channel_code,
    sar_channel_id,
)

processed_data_record = Struct(
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
    "slant_range_to_first_pixel" / Metadata(Int32ub, units="m"),
    "slant_range_to_mid_pixel" / Metadata(Int32ub, units="m"),
    "slant_range_to_last_pixel" / Metadata(Int32ub, units="m"),
    "doppler_centroid_value_at_first_pixel" / Metadata(Factor(Int32ub, 1e-3), units="Hz"),
    "doppler_centroid_value_at_mid_pixel" / Metadata(Factor(Int32ub, 1e-3), units="Hz"),
    "doppler_centroid_value_at_last_pixel" / Metadata(Factor(Int32ub, 1e-3), units="Hz"),
    "azimuth_fm_rate_of_first_pixel" / Metadata(Int32ub, units="Hz/ms"),
    "azimuth_fm_rate_of_mid_pixel" / Metadata(Int32ub, units="Hz/ms"),
    "azimuth_fm_rate_of_last_pixel" / Metadata(Int32ub, units="Hz/ms"),
    "look_angle_of_nadir" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "azimuth_squint_angle" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "blanks1" / StripNullBytes(Bytes(20)),
    "geographic_reference_parameter_update_flag" / Int32ub,
    "latitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "latitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "latitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_first_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_center_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "longitude_of_last_pixel" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "northing_of_first_pixel" / Metadata(Int32ub, units="m"),
    "blanks2" / StripNullBytes(Bytes(4)),
    "northing_of_last_pixel" / Metadata(Int32ub, units="m"),
    "easting_of_first_pixel" / Metadata(Int32ub, units="m"),
    "blanks3" / StripNullBytes(Bytes(4)),
    "easting_of_last_pixel" / Metadata(Int32ub, units="m"),
    "line_heading" / Metadata(Factor(Int32ub, 1e-6), units="deg"),
    "blanks4" / StripNullBytes(Bytes(8)),
    "data"
    / Struct(
        "start" / Tell,
        "size" / Computed(this._.preamble.record_length - (this.start - this._.record_start)),
        "stop" / Seek(this._.record_start + this._.preamble.record_length),
    ),
)
