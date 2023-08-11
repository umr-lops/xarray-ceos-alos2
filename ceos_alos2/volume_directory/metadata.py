from tlz.functoolz import curry, pipe

from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.hierarchy import Group
from ceos_alos2.transformers import normalize_datetime
from ceos_alos2.utils import remove_nesting_layer, rename


def transform_volume_descriptor(mapping):
    ignored = [
        "preamble",
        "ascii_ebcdic_flag",
        "blanks",
        "spare",
        "local_use_segment",
        "total_number_of_physical_volumes_in_logical_volume",
        "physical_volume_sequence_number_of_the_first_tape",
        "physical_volume_sequence_number_of_the_last_tape",
        "physical_volume_sequence_number_of_the_current_tape",
        "file_number_in_the_logical_volume",
        "logical_volume_within_a_volume_set",
        "logical_volume_number_within_physical_volume",
        "number_of_file_pointer_records",
        "number_of_text_records_in_volume_directory",
    ]

    translations = {
        "superstructure_format_control_document_id": "control_document_id",
        "superstructure_format_control_document_revision_level": "control_document_revision_level",
        "superstructure_record_format_revision_level": "record_format_revision_level",
        "software_release_and_revision_level": "software_version",
        "logical_volume_creation_datetime": "creation_datetime",
        "logical_volume_generation_country": "creation_country",
        "logical_volume_generating_agency": "creation_agency",
        "logical_volume_generating_facility": "creation_facility",
    }

    postprocessors = {
        "creation_datetime": normalize_datetime,
    }

    return pipe(
        mapping,
        curry(dissoc, ignored),
        curry(rename, translations=translations),
        curry(apply_to_items, postprocessors),
    )


def transform_text(mapping):
    ignored = ["preamble", "ascii_ebcdic_flag", "blanks", "physical_tape_id"]

    translations = {
        "location_and_datetime_of_product_creation": "product_creation",
    }

    transformed = pipe(
        mapping,
        curry(dissoc, ignored),
        curry(rename, translations=translations),
    )

    return transformed


def transform_record(mapping):
    ignored = ["file_descriptors"]

    transformers = {
        "volume_descriptor": transform_volume_descriptor,
        "text_record": transform_text,
    }
    transformed = pipe(
        mapping,
        curry(dissoc, ignored),
        curry(apply_to_items, transformers),
        curry(remove_nesting_layer),
    )

    return Group(path=None, url=None, data={}, attrs=transformed)
