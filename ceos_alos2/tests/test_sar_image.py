import datetime as dt
from dataclasses import dataclass

import fsspec
import numpy as np
import pytest
from construct import Int8ub, Int16ub, Seek, Struct, Tell, this

from ceos_alos2 import sar_image
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_image import enums, io, metadata
from ceos_alos2.testing import assert_identical


@dataclass
class Data:
    start: int
    stop: int


@dataclass
class Record:
    record_start: int
    data: Data


dummy_record_types = {
    10: Struct("preamble" / io.record_preamble, "a" / Int8ub, "b" / Int8ub, "c" / Int16ub),
    11: Struct("preamble" / io.record_preamble, "x" / Int8ub, "y" / Int8ub),
}


class TestEnums:
    @pytest.mark.parametrize(
        ["size", "expected"],
        (
            (1, enums.Int8ub),
            (2, enums.Int16ub),
            (4, enums.Int32ub),
            (8, enums.Int64ub),
            (3, ValueError("unsupported size")),
        ),
    )
    def test_flag_init(self, size, expected):
        if isinstance(expected, Exception):
            with pytest.raises(type(expected), match=expected.args[0]):
                enums.Flag(size)

            return

        flag = enums.Flag(size)

        assert flag.subcon is expected

    @pytest.mark.parametrize(
        ["size", "data", "expected"],
        (
            (1, b"\x00", False),
            (1, b"\x0F", True),
            (2, b"\x00\x00", False),
        ),
    )
    def test_flag_decode(self, size, data, expected):
        flag = enums.Flag(size)
        actual = flag.parse(data)

        assert actual == expected

    @pytest.mark.parametrize(
        ["size", "data", "expected"],
        (
            (1, False, b"\x00"),
            (1, True, b"\x01"),
            (2, False, b"\x00\x00"),
            (2, True, b"\x00\x01"),
        ),
    )
    def test_flag_encode(self, size, data, expected):
        flag = enums.Flag(size)
        actual = flag.build(data)

        assert actual == expected


class TestMetadata:
    @pytest.mark.parametrize(
        ["header", "expected"],
        (
            ({"prefix_suffix_data_locators": {"sar_data_format_type_code": "IU2"}}, "IU2"),
            ({"prefix_suffix_data_locators": {"sar_data_format_type_code": "C*8"}}, "C*8"),
        ),
    )
    def test_extract_format_type(self, header, expected):
        actual = metadata.extract_format_type(header)

        assert actual == expected

    @pytest.mark.parametrize(
        ["header", "expected"],
        (
            (
                {
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 3,
                        "number_of_data_groups_per_line": 2,
                    }
                },
                (3, 2),
            ),
            (
                {
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 6,
                        "number_of_data_groups_per_line": 4,
                    }
                },
                (6, 4),
            ),
        ),
    )
    def test_extract_shape(self, header, expected):
        actual = metadata.extract_shape(header)

        assert actual == expected

    @pytest.mark.parametrize(
        ["header", "expected"],
        (
            pytest.param({"preamble": {}}, {}, id="preamble"),
            pytest.param(
                {
                    "interleaving_id": "BSQ",
                    "number_of_burst_data": 5,
                    "number_of_lines_per_burst": 1,
                    "number_of_overlap_lines_with_adjacent_bursts": 3,
                },
                {
                    "interleaving_id": "BSQ",
                    "number_of_burst_data": 5,
                    "number_of_lines_per_burst": 1,
                    "number_of_overlap_lines_with_adjacent_bursts": 3,
                },
                id="known_attrs",
            ),
            pytest.param(
                {"maximum_data_range_of_pixel": 27}, {"valid_range": [0, 27]}, id="transformed1"
            ),
            pytest.param({"maximum_data_range_of_pixel": float("nan")}, {}, id="transformed2"),
        ),
    )
    def test_extract_attrs(self, header, expected):
        actual = metadata.extract_attrs(header)

        assert actual == expected

    @pytest.mark.parametrize(
        "overrides",
        (
            {"a": "int8"},
            {"b": "float16"},
        ),
    )
    def test_apply_overrides(self, overrides):
        mapping = {"a": ("x", [1, 2], {}), "b": ("y", [1.0, 2.1], {})}

        applied = metadata.apply_overrides(overrides, mapping)
        actual = {k: v[1].dtype for k, v in applied.items() if hasattr(v[1], "dtype")}

        assert actual == overrides

    @pytest.mark.parametrize(
        ["known", "expected"],
        (
            (["b"], {"a": 1, "c": ("y", [2, 2], {}), "b": 1}),
            (["c"], {"a": 1, "b": ("x", [1, 1], {}), "c": 2}),
            (["b", "c"], {"a": 1, "b": 1, "c": 2}),
        ),
    )
    def test_deduplicate_attrs(self, known, expected):
        mapping = {"a": 1, "b": ("x", [1, 1], {}), "c": ("y", [2, 2], {})}

        actual = metadata.deduplicate_attrs(known, mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                [
                    {
                        "preamble": {},
                        "record_start": 1,
                        "actual_count_of_left_fill_pixels": 0,
                        "actual_count_of_right_fill_pixels": 0,
                        "actual_count_of_data_pixels": 0,
                        "palsar_auxiliary_data": b"",
                        "blanks2": "",
                        "data": {},
                    }
                ],
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                [{"a": (1, {"units": "m"})}, {"a": (2, {"units": "m"})}],
                Group(
                    path=None,
                    url=None,
                    data={"a": Variable("rows", [1, 2], {"units": "m"})},
                    attrs={},
                ),
                id="variables_transformed",
            ),
            pytest.param(
                [{"scan_id": 1}, {"scan_id": 1}],
                Group(path=None, url=None, data={}, attrs={"scan_id": 1}),
                id="deduplicated_attrs",
            ),
            pytest.param(
                [
                    {"sensor_acquisition_date": dt.datetime(2020, 10, 1, 12, 37, 42, 451000)},
                    {"sensor_acquisition_date": dt.datetime(2020, 10, 2, 12, 37, 42, 451000)},
                ],
                Group(
                    path=None,
                    url=None,
                    data={
                        "sensor_acquisition_date": Variable(
                            "rows",
                            np.array(
                                ["2020-10-01 12:37:42.451", "2020-10-02 12:37:42.451"],
                                dtype="datetime64[ns]",
                            ),
                            {},
                        )
                    },
                    attrs={},
                ),
                id="dtype_overrides",
            ),
            pytest.param(
                [{"sar_image_data_line_number": 1}, {"sar_image_data_line_number": 2}],
                Group(path=None, url=None, data={"rows": Variable("rows", [1, 2], {})}, attrs={}),
                id="renamed",
            ),
        ),
    )
    def test_transform_line_metadata(self, mapping, expected):
        actual = metadata.transform_line_metadata(mapping)

        assert_identical(actual, expected)

    @pytest.mark.parametrize(
        ["header", "mapping", "expected_group", "expected_attrs"],
        (
            pytest.param(
                {
                    "prefix_suffix_data_locators": {"sar_data_format_type_code": "IU2"},
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 2,
                        "number_of_data_groups_per_line": 4,
                    },
                },
                [{"data": {"start": 1, "stop": 5}}, {"data": {"start": 6, "stop": 10}}],
                Group(path=None, url=None, data={}, attrs={"coordinates": []}),
                {
                    "byte_ranges": [(1, 5), (6, 10)],
                    "type_code": "IU2",
                    "shape": (2, 4),
                    "dtype": "uint16",
                },
                id="array_metadata1",
            ),
            pytest.param(
                {
                    "prefix_suffix_data_locators": {"sar_data_format_type_code": "C*8"},
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 6,
                        "number_of_data_groups_per_line": 3,
                    },
                },
                [{"data": {"start": 5, "stop": 21}}, {"data": {"start": 25, "stop": 41}}],
                Group(path=None, url=None, data={}, attrs={"coordinates": []}),
                {
                    "byte_ranges": [(5, 21), (25, 41)],
                    "type_code": "C*8",
                    "shape": (6, 3),
                    "dtype": "complex64",
                },
                id="array_metadata2",
            ),
            pytest.param(
                {
                    "prefix_suffix_data_locators": {"sar_data_format_type_code": "F*4"},
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 6,
                        "number_of_data_groups_per_line": 3,
                    },
                },
                [],
                ValueError("unknown type code"),
                {},
                id="array_metadata3",
            ),
            pytest.param(
                {
                    "prefix_suffix_data_locators": {"sar_data_format_type_code": "C*8"},
                    "sar_related_data_in_the_record": {
                        "number_of_lines_per_dataset": 6,
                        "number_of_data_groups_per_line": 3,
                    },
                },
                [
                    {
                        "scan_id": 1,
                        "sar_image_data_line_number": 1,
                        "data": {"start": 5, "stop": 21},
                    },
                    {
                        "scan_id": 1,
                        "sar_image_data_line_number": 2,
                        "data": {"start": 25, "stop": 41},
                    },
                ],
                Group(
                    path=None,
                    url=None,
                    data={"rows": Variable("rows", [1, 2], {})},
                    attrs={"coordinates": ["rows"], "scan_id": 1},
                ),
                {
                    "byte_ranges": [(5, 21), (25, 41)],
                    "type_code": "C*8",
                    "shape": (6, 3),
                    "dtype": "complex64",
                },
                id="line_metadata",
            ),
        ),
    )
    def test_transform_metadata(self, header, mapping, expected_group, expected_attrs):
        if isinstance(expected_group, Exception):
            exc = expected_group
            with pytest.raises(type(exc), match=exc.args[0]):
                metadata.transform_metadata(header, mapping)

            return

        actual_group, actual_attrs = metadata.transform_metadata(header, mapping)

        assert actual_attrs == expected_attrs
        assert_identical(actual_group, expected_group)


class TestIO:
    @pytest.mark.parametrize(
        ["content", "element_size", "expected"],
        (
            pytest.param(b"\x00\x00\x00", 2, ValueError("sizes mismatch"), id="wrong_element_size"),
            pytest.param(
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                2,
                ValueError("unknown record type code"),
                id="unkown_record_type",
            ),
            pytest.param(
                (
                    b"\x00\x00\x00\x01\x00\x0A\x00\x00\x00\x00\x00\x10\x02\x03\x00\x1F"
                    + b"\x00\x00\x00\x02\x00\x0A\x00\x00\x00\x00\x00\x10\x04\x05\x00\x2F"
                ),
                16,
                [
                    {
                        "preamble": {
                            "record_sequence_number": 1,
                            "first_record_subtype": 0,
                            "record_type": 10,
                            "second_record_subtype": 0,
                            "third_record_subtype": 0,
                            "record_length": 16,
                        },
                        "a": 2,
                        "b": 3,
                        "c": 31,
                    },
                    {
                        "preamble": {
                            "record_sequence_number": 2,
                            "first_record_subtype": 0,
                            "record_type": 10,
                            "second_record_subtype": 0,
                            "third_record_subtype": 0,
                            "record_length": 16,
                        },
                        "a": 4,
                        "b": 5,
                        "c": 47,
                    },
                ],
                id="signal-2elem",
            ),
            pytest.param(
                (
                    b"\x00\x00\x00\x01\x00\x0B\x00\x00\x00\x00\x00\x0E\x03\x04"
                    + b"\x00\x00\x00\x02\x00\x0B\x00\x00\x00\x00\x00\x0E\x04\x05"
                ),
                14,
                [
                    {
                        "preamble": {
                            "record_sequence_number": 1,
                            "first_record_subtype": 0,
                            "record_type": 11,
                            "second_record_subtype": 0,
                            "third_record_subtype": 0,
                            "record_length": 14,
                        },
                        "x": 3,
                        "y": 4,
                    },
                    {
                        "preamble": {
                            "record_sequence_number": 2,
                            "first_record_subtype": 0,
                            "record_type": 11,
                            "second_record_subtype": 0,
                            "third_record_subtype": 0,
                            "record_length": 14,
                        },
                        "x": 4,
                        "y": 5,
                    },
                ],
                id="processed-2elem",
            ),
        ),
    )
    def test_parse_chunk(self, monkeypatch, content, element_size, expected):
        from ceos_alos2.utils import to_dict

        monkeypatch.setattr(io, "record_types", dummy_record_types)

        if isinstance(expected, Exception):
            with pytest.raises(type(expected), match=expected.args[0]):
                io.parse_chunk(content, element_size)

            return

        actual = to_dict(io.parse_chunk(content, element_size))
        assert actual == expected

    @pytest.mark.parametrize(
        ["records", "offset", "expected"],
        (
            pytest.param(
                [Record(1, Data(4, 6)), Record(6, Data(9, 11))],
                12,
                [Record(13, Data(16, 18)), Record(18, Data(21, 23))],
            ),
            pytest.param(
                [Record(3, Data(5, 9)), Record(9, Data(11, 15)), Record(15, Data(17, 21))],
                3,
                [Record(6, Data(8, 12)), Record(12, Data(14, 18)), Record(18, Data(20, 24))],
            ),
        ),
    )
    def test_adjust_offsets(self, records, offset, expected):
        actual = io.adjust_offsets(records, offset)

        assert actual == expected

    @pytest.mark.parametrize("rpc", [1, 2])
    def test_read_metadata(self, monkeypatch, rpc):
        dummy_header = {"number_of_sar_data_records": 3, "sar_data_record_length": 17}
        content = (
            b"\x03\x0E"
            + b"\x00\x00\x00\x01\x00\x0B\x00\x00\x00\x00\x00\x11\x03\x00\x00\x00\x00"
            + b"\x00\x00\x00\x02\x00\x0B\x00\x00\x00\x00\x00\x11\x04\x00\x00\x00\x00"
            + b"\x00\x00\x00\x03\x00\x0B\x00\x00\x00\x00\x00\x11\x05\x00\x00\x00\x00"
        )
        print(len(content))
        dummy_record_types = {
            11: Struct(
                "preamble" / io.record_preamble,
                "record_start" / Tell,
                "a" / Int8ub,
                "data" / Struct("start" / Tell, "stop" / Seek(this.start + 4)),
            ),
        }

        expected = [
            {
                "preamble": {
                    "record_sequence_number": 1,
                    "first_record_subtype": 0,
                    "record_type": 11,
                    "second_record_subtype": 0,
                    "third_record_subtype": 0,
                    "record_length": 17,
                },
                "record_start": 732,
                "a": 3,
                "data": {"start": 733, "stop": 737},
            },
            {
                "preamble": {
                    "record_sequence_number": 2,
                    "first_record_subtype": 0,
                    "record_type": 11,
                    "second_record_subtype": 0,
                    "third_record_subtype": 0,
                    "record_length": 17,
                },
                "record_start": 749,
                "a": 4,
                "data": {"start": 750, "stop": 754},
            },
            {
                "preamble": {
                    "record_sequence_number": 3,
                    "first_record_subtype": 0,
                    "record_type": 11,
                    "second_record_subtype": 0,
                    "third_record_subtype": 0,
                    "record_length": 17,
                },
                "record_start": 766,
                "a": 5,
                "data": {"start": 767, "stop": 771},
            },
        ]

        mapper = fsspec.get_mapper("memory://")
        mapper["path"] = content

        def dummy_read_file_descriptor(f):
            f.read(2)

            return dummy_header

        monkeypatch.setattr(io, "read_file_descriptor", dummy_read_file_descriptor)
        monkeypatch.setattr(io, "record_types", dummy_record_types)

        with mapper.fs.open("path", mode="rb") as f:
            header, metadata_ = io.read_metadata(f, records_per_chunk=rpc)

        assert header == dummy_header
        assert metadata_ == expected


class TestInit:
    @pytest.mark.parametrize(
        ["path", "expected"],
        (
            ("IMG-HH-ALOS2225333100-180726-WWDR1.1__D-B3", "HH_scan3"),
            ("IMG-HV-ALOS2290760600-191011-WWDR1.5RUA", "HV"),
        ),
    )
    def test_filename_to_groupname(self, path, expected):
        actual = sar_image.filename_to_groupname(path)

        assert actual == expected
