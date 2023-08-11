import fsspec
import pytest

from ceos_alos2.hierarchy import Group
from ceos_alos2.testing import assert_identical
from ceos_alos2.volume_directory import io, metadata


class TestMetadata:
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

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "volume_descriptor": {"a": 1},
                    "file_descriptors": [{"b": 2}, {"c": 3}],
                    "text_record": {"d": 4},
                },
                Group(path=None, url=None, data={}, attrs={"a": 1, "d": 4}),
                id="ignored",
            ),
            pytest.param(
                {
                    "volume_descriptor": {
                        "preamble": "a",
                        "logical_volume_generation_country": "a",
                    },
                    "text_record": {"blanks": "", "location_and_datetime_of_product_creation": "b"},
                },
                Group(
                    path=None,
                    url=None,
                    data={},
                    attrs={"creation_country": "a", "product_creation": "b"},
                ),
                id="transformers",
            ),
            pytest.param(
                {"volume_descriptor": {"a": 1, "b": 2}, "text_record": {"c": 3, "d": 4}},
                Group(path=None, url=None, data={}, attrs={"a": 1, "b": 2, "c": 3, "d": 4}),
                id="flattened",
            ),
        ),
    )
    def test_transform_record(self, mapping, expected):
        actual = metadata.transform_record(mapping)

        assert_identical(actual, expected)


class TestHighLevel:
    @pytest.mark.skip(reason="need actual data")
    def test_parse_data(self):
        data = b""

        actual = io.parse_data(data)

        # no need to verify the result, just make sure we get something usable
        assert isinstance(actual, dict)
        assert list(actual) == ["volume_descriptor", "file_descriptors", "text_record"]

    @pytest.mark.parametrize(
        ["path", "expected"],
        (
            pytest.param("vol1", FileNotFoundError("Cannot open .+"), id="not-existing"),
            pytest.param(
                "vol2",
                Group(
                    path=None,
                    url=None,
                    data={},
                    attrs={"creation_agency": "b", "product_creation": "c"},
                ),
                id="existing",
            ),
        ),
    )
    def test_open_volume_directory(self, monkeypatch, path, expected):
        binary = b"\x01\x02"
        recorded_binary = []
        mapping = {
            "volume_descriptor": {"preamble": "a", "logical_volume_generating_agency": "b"},
            "file_descriptors": [],
            "text_record": {
                "physical_tape_id": 2,
                "location_and_datetime_of_product_creation": "c",
            },
        }

        def fake_parse_data(data):
            recorded_binary.append(data)

            return mapping

        monkeypatch.setattr(io, "parse_data", fake_parse_data)

        mapper = fsspec.get_mapper("memory://")
        mapper["vol2"] = binary

        if isinstance(expected, Exception):
            with pytest.raises(type(expected), match=expected.args[0]):
                io.open_volume_directory(mapper, path)

            return

        actual = io.open_volume_directory(mapper, path)

        assert_identical(actual, expected)
