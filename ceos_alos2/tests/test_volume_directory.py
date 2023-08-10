import pytest

from ceos_alos2.volume_directory import metadata


class TestMetadata:
    @pytest.mark.parametrize(
        ["s", "expected"],
        (
            ("1990012012563297", "1990-01-20T12:56:32.970000"),
            ("2001112923595915", "2001-11-29T23:59:59.150000"),
        ),
    )
    def test_parse_datetime(self, s, expected):
        actual = metadata.normalize_datetime(s)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "preamble": {"a": 1},
                    "ascii_ebcdic_flag": "A",
                    "blanks": "",
                    "spare": "",
                    "local_use_segment": "",
                    "total_number_of_physical_volumes_in_logical_volume": 1,
                    "physical_volume_sequence_number_of_the_first_tape": 1,
                    "physical_volume_sequence_number_of_the_last_tape": 1,
                    "physical_volume_sequence_number_of_the_current_tape": 1,
                    "file_number_in_the_logical_volume": 2,
                    "logical_volume_within_a_volume_set": "a",
                    "logical_volume_number_within_physical_volume": 4,
                    "number_of_file_pointer_records": 4,
                    "number_of_text_records_in_volume_directory": 1,
                },
                {},
                id="ignored1",
            ),
            pytest.param(
                {"number_of_file_pointer_records": 4, "volume_set_id": "abc"},
                {"volume_set_id": "abc"},
                id="ignored2",
            ),
            pytest.param(
                {
                    "superstructure_format_control_document_id": "a",
                    "superstructure_format_control_document_revision_level": "a",
                    "superstructure_record_format_revision_level": "a",
                    "software_release_and_revision_level": "001.001",
                    "logical_volume_generation_country": "a",
                    "logical_volume_generating_agency": "a",
                    "logical_volume_generating_facility": "a",
                },
                {
                    "control_document_id": "a",
                    "control_document_revision_level": "a",
                    "record_format_revision_level": "a",
                    "software_version": "001.001",
                    "creation_country": "a",
                    "creation_agency": "a",
                    "creation_facility": "a",
                },
                id="translations1",
            ),
            pytest.param(
                {"logical_volume_creation_datetime": "2020101117233798"},
                {"creation_datetime": "2020-10-11T17:23:37.980000"},
                id="translations2",
            ),
            pytest.param(
                {"creation_datetime": "2020101117233798"},
                {"creation_datetime": "2020-10-11T17:23:37.980000"},
                id="postprocessing",
            ),
        ),
    )
    def test_transform_volume_descriptor(self, mapping, expected):
        actual = metadata.transform_volume_descriptor(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"preamble": {}, "ascii_ebcdic_flag": "a", "blanks": "", "physical_tape_id": 1},
                {},
                id="ignored1",
            ),
            pytest.param(
                {"blanks": "", "product_id": "PRODUCT:WWDR1.5RUA"},
                {"product_id": "PRODUCT:WWDR1.5RUA"},
                id="ignored2",
            ),
            pytest.param(
                {"product_id": "b", "location_and_datetime_of_product_creation": "a"},
                {"product_id": "b", "product_creation": "a"},
                id="translations",
            ),
        ),
    )
    def test_transform_text(self, mapping, expected):
        actual = metadata.transform_text(mapping)

        assert actual == expected
