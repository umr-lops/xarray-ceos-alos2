from construct import Struct, this

from ceos_alos2.common import record_preamble
from ceos_alos2.datatypes import AsciiInteger, PaddedString

volume_descriptor = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_flag" / PaddedString(2),
    "blanks" / PaddedString(2),
    "superstructure_format_control_document_id" / PaddedString(12),
    "superstructure_format_control_document_revision_level" / PaddedString(2),
    "superstructure_record_format_revision_level" / PaddedString(2),
    "software_release_and_revision_level" / PaddedString(12),
    "physical_volume_id" / PaddedString(16),
    "logical_volume_id" / PaddedString(16),
    "volume_set_id" / PaddedString(16),
    "total_number_of_physical_volumes_in_logical_volume" / AsciiInteger(2),
    "physical_volume_sequence_number_of_the_first_tape" / AsciiInteger(2),
    "physical_volume_sequence_number_of_the_last_tape" / AsciiInteger(2),
    "physical_volume_sequence_number_of_the_current_tape" / AsciiInteger(2),
    "file_number_in_the_logical_volume" / AsciiInteger(4),
    "logical_volume_within_a_volume_set" / AsciiInteger(4),
    "logical_volume_number_within_physical_volume" / AsciiInteger(4),
    "logical_volume_creation_datetime" / PaddedString(16),  # merged two entries
    "logical_volume_generation_country" / PaddedString(12),
    "logical_volume_generating_agency" / PaddedString(8),
    "logical_volume_generating_facility" / PaddedString(12),
    "number_of_file_pointer_records" / AsciiInteger(4),
    "number_of_text_records_in_volume_directory" / AsciiInteger(4),
    "spare" / PaddedString(92),
    "local_use_segment" / PaddedString(100),
)

file_descriptor = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_flag" / PaddedString(2),
    "blanks" / PaddedString(2),
    "referenced_file_number" / AsciiInteger(4),
    "referenced_file_name_id" / PaddedString(16),
    "referenced_file_class" / PaddedString(28),
    "referenced_file_class_code" / PaddedString(4),
    "referenced_file_data_type" / PaddedString(28),
    "referenced_file_data_type_code" / PaddedString(4),
    "number_of_records_in_referenced_file" / AsciiInteger(8),
    "length_of_the_first_record_in_referenced_file" / AsciiInteger(8),
    "maximum_record_length_in_referenced_file" / AsciiInteger(8),
    "referenced_file_record_length_type" / PaddedString(12),
    "referenced_file_record_length_type_code" / PaddedString(4),
    "number_of_the_physical_volume_set_containing_the_first_record_of_the_file" / AsciiInteger(2),
    "number_of_the_physical_volume_set_containing_the_last_record_of_the_file" / AsciiInteger(2),
    "record_number_of_the_first_record_appearing_on_this_physical_volume" / AsciiInteger(8),
    "record_number_of_the_last_record_appearing_on_this_physical_volume" / AsciiInteger(8),
    "spare" / PaddedString(100),
    "local_use_segment" / PaddedString(100),
)

text_record = Struct(
    "preamble" / record_preamble,
    "ascii_ebcdic_flag" / PaddedString(2),
    "blanks" / PaddedString(2),
    "product_id" / PaddedString(40),
    "location_and_datetime_of_product_creation" / PaddedString(60),
    "physical_tape_id" / PaddedString(40),
    "scene_id" / PaddedString(40),
    "scene_location_id" / PaddedString(40),
    "blanks" / PaddedString(124),
)

volume_directory_record = Struct(
    "volume_descriptor" / volume_descriptor,
    "file_descriptors" / file_descriptor[this.volume_descriptor.number_of_file_pointer_records],
    "text_record" / text_record,
)
