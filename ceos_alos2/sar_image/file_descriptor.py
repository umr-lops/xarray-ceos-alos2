from construct import Struct

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiInteger, PaddedString

file_descriptor_record = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_flag" / PaddedString(2),
    "blanks1" / PaddedString(2),
    "format_control_document_id" / PaddedString(12),
    "format_control_document_revision_level" / PaddedString(2),
    "file_design_descriptor_revision_letter" / PaddedString(2),
    "software_release_and_revision_number" / PaddedString(12),
    "file_number" / AsciiInteger(4),
    "file_id" / PaddedString(16),
    "record_sequence_and_location_type_flag" / PaddedString(4),
    "location_sequence_number" / AsciiInteger(8),
    "field_length_of_sequence_number" / AsciiInteger(4),
    "record_code_and_location_type_flag" / PaddedString(4),
    "record_code_location" / AsciiInteger(8),
    "record_code_field_length" / AsciiInteger(4),
    "record_length_and_location_type_flag" / PaddedString(4),
    "record_length_location" / AsciiInteger(8),
    "record_length_field_length" / AsciiInteger(4),
    "reserved1" / PaddedString(1),
    "reserved2" / PaddedString(1),
    "reserved3" / PaddedString(1),
    "reserved4" / PaddedString(1),
    "blanks6" / PaddedString(64),
    "number_of_sar_data_records" / AsciiInteger(6),
    "sar_data_record_length" / AsciiInteger(6),
    "reserved5" / PaddedString(24),
    "sample_group_data"
    / Struct(
        "bit_length_per_sample" / AsciiInteger(4),
        "number_of_samples_per_data_group" / AsciiInteger(4),
        "number_of_bytes_per_data_group" / AsciiInteger(4),
        "justification_and_order_of_samples_within_data_group" / PaddedString(4),
    ),
    "sar_related_data_in_the_record"
    / Struct(
        "number_of_sar_channels" / AsciiInteger(4),
        "number_of_lines_per_dataset" / AsciiInteger(8),
        "number_of_left_border_pixels_per_line" / AsciiInteger(4),
        "number_of_data_groups_per_line" / AsciiInteger(8),
        "number_of_right_border_pixels_per_line" / AsciiInteger(4),
        "number_of_top_border_lines" / AsciiInteger(4),
        "number_of_bottom_border_lines" / AsciiInteger(4),
        "interleaving_id" / PaddedString(4),
    ),
    "record_data_in_the_file"
    / Struct(
        "number_of_physical_records_per_line" / AsciiInteger(2),
        "number_of_physical_records_per_multichannel_line_in_this_file" / AsciiInteger(2),
        "number_of_bytes_of_prefix_data_per_record" / AsciiInteger(4),
        "number_of_bytes_of_sar_data_per_record" / AsciiInteger(8),
        "number_of_bytes_of_suffix_data_per_record" / AsciiInteger(4),
        "prefix_suffix_repeat_flag" / PaddedString(4),
    ),
    "prefix_suffix_data_locators"
    / Struct(
        "sample_data_line_number_locator" / PaddedString(8),
        "sar_channel_number_locator" / PaddedString(8),
        "time_of_sar_data_line_locator" / PaddedString(8),
        "left_fill_count_locator" / PaddedString(8),
        "right_fill_count_locator" / PaddedString(8),
        "pad_pixels_present_indicator" / PaddedString(4),
        "blanks" / PaddedString(28),
        "sar_data_line_quality_code_locator" / PaddedString(8),
        "calibration_information_field_locator" / PaddedString(8),
        "gain_values_field_locator" / PaddedString(8),
        "bias_values_field_locator" / PaddedString(8),
        "sar_data_format_type_indicator" / PaddedString(28),
        "sar_data_format_type_code" / PaddedString(4),
        "number_of_left_fill_bits_within_pixel" / AsciiInteger(4),
        "number_of_right_fill_bits_within_pixel" / AsciiInteger(4),
        "maximum_data_range_of_pixel" / AsciiInteger(8),
        "number_of_burst_data" / AsciiInteger(4),
        "number_of_lines_per_burst" / AsciiInteger(4),
    ),
    "scansar_burst_data_information"
    / Struct(
        "number_of_overlap_lines_with_adjacent_bursts" / AsciiInteger(4),
        "blanks" / PaddedString(260),
    ),
)
