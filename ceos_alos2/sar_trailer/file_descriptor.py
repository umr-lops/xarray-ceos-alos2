from construct import Struct, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiInteger, PaddedString

small_record_info = Struct(
    "number_of_records" / AsciiInteger(6),
    "record_length" / AsciiInteger(6),
)
big_record_info = Struct(
    "number_of_records" / AsciiInteger(6),
    "record_length" / AsciiInteger(8),
)
low_res_image_size = Struct(
    "record_length" / AsciiInteger(8),
    "number_of_pixels" / AsciiInteger(6),
    "number_of_lines" / AsciiInteger(6),
    "number_of_bytes_per_one_sample" / AsciiInteger(6),
)
file_descriptor_record = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_code" / PaddedString(2),
    "blanks1" / PaddedString(2),
    "format_control_document_id" / PaddedString(12),
    "format_control_document_revision_number" / PaddedString(2),
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
    "map_projection" / small_record_info,
    "platform_position" / small_record_info,
    "attitude" / small_record_info,
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
    "facility_related_data_1" / big_record_info,
    "facility_related_data_2" / big_record_info,
    "facility_related_data_3" / big_record_info,
    "facility_related_data_4" / big_record_info,
    "facility_related_data_5" / big_record_info,
    "number_of_low_resolution_images" / AsciiInteger(6),
    "low_resolution_image_sizes" / low_res_image_size[this.number_of_low_resolution_images],
    "blanks"
    / PaddedString(720 - 522 - this.number_of_low_resolution_images * low_res_image_size.sizeof()),
)
