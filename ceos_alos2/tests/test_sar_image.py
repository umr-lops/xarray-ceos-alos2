import datetime as dt

import numpy as np
import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_image import enums, metadata
from ceos_alos2.testing import assert_identical


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
