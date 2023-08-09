import json
from pathlib import Path

import fsspec
import numpy as np
import pytest

from ceos_alos2.array import Array
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_image import caching
from ceos_alos2.sar_image.caching.path import project_name
from ceos_alos2.testing import assert_identical
from ceos_alos2.tests.utils import create_dummy_array


def test_hashsum():
    # no need to verify the external library extensively
    data = "ddeeaaddbbeeeeff"
    expected = "b8be84665c5cd09ec19677ce9714bcd987422de886ac2e8432a3e2311b5f0cde"

    actual = caching.path.hashsum(data)

    assert actual == expected


@pytest.mark.parametrize(
    "cache_dir",
    [
        Path("/path/to/cache1") / project_name,
        Path("/path/to/cache2") / project_name,
    ],
)
@pytest.mark.parametrize(
    ["remote_root", "path", "expected"],
    (
        pytest.param(
            "http://127.0.0.1/path/to/data",
            "image1",
            Path("c9db4f27e586452c6517524752dc472863ee42230ba98e83a346b8da94a33235/image1.index"),
        ),
        pytest.param(
            "s3://bucket/path/to/data",
            "image1",
            Path("04391cfcf37045b78e7b4793392821b5b4c84591edfcb475954130eb34b87366/image1.index"),
        ),
        pytest.param(
            "file:///path/to/data",
            "image1",
            Path("9506f2b2ddfa8498bc4c1d3cc50d02ee5f799f6716710ff4dd31a9f6e41eac45/image1.index"),
        ),
        pytest.param(
            "/path/to/data",
            "image2",
            Path("7b405676e8ed8556a3f4f98f4dc5b6df940f3a5ce48674046eebda551e335b37/image2.index"),
        ),
    ),
)
def test_local_cache_location(monkeypatch, cache_dir, remote_root, path, expected):
    monkeypatch.setattr(caching.path, "cache_root", cache_dir)

    actual = caching.path.local_cache_location(remote_root, path)

    assert cache_dir in actual.parents
    assert actual.relative_to(cache_dir) == expected


@pytest.mark.parametrize(
    "remote_root", ("http://127.0.0.1/path/to/data", "s3://bucket/path/to/data")
)
@pytest.mark.parametrize(
    ["path", "expected"],
    (
        ("image1", "image1.index"),
        ("image7", "image7.index"),
    ),
)
def test_remote_cache_location(remote_root, path, expected):
    actual = caching.path.remote_cache_location(remote_root, path)

    assert actual == expected


class TestEncoders:
    @pytest.mark.parametrize(
        ["arr", "expected_data", "expected_attrs"],
        (
            pytest.param(
                np.array([0, 10, 20, 30], dtype="timedelta64[ms]"),
                np.array([0, 10, 20, 30]),
                {"units": "ms"},
            ),
            pytest.param(
                np.array([0, 1, 7, 12, 13], dtype="timedelta64[s]"),
                np.array([0, 1, 7, 12, 13]),
                {"units": "s"},
            ),
        ),
    )
    def test_encode_timedelta(self, arr, expected_data, expected_attrs):
        actual_data, actual_attrs = caching.encoders.encode_timedelta(arr)

        np.testing.assert_equal(actual_data, expected_data)
        assert actual_attrs == expected_attrs

    @pytest.mark.parametrize(
        ["arr", "expected_data", "expected_attrs"],
        (
            pytest.param(
                np.array(["2019-01-01 00:01:00", "2019-01-02 00:02:00"], dtype="datetime64[ms]"),
                [0, 86460000],
                {"units": "ms", "reference": "2019-01-01T00:01:00.000"},
            ),
            pytest.param(
                np.array(["2019-01-01 00:00:00"], dtype="datetime64[ns]"),
                np.array([0]),
                {"units": "ns", "reference": "2019-01-01T00:00:00.000000000"},
            ),
            pytest.param(
                np.array(["2019-01-01 00:00:00", "2020-01-01 00:00:00"], dtype="datetime64[s]"),
                [0, 31536000],
                {"units": "s", "reference": "2019-01-01T00:00:00"},
            ),
        ),
    )
    def test_encode_datetime(self, arr, expected_data, expected_attrs):
        actual_data, actual_attrs = caching.encoders.encode_datetime(arr)

        assert actual_data == expected_data
        assert actual_attrs == expected_attrs

    @pytest.mark.parametrize(
        ["arr", "expected"],
        (
            pytest.param(
                np.array([0, 1, 2], dtype="int32"),
                {"__type__": "array", "dtype": "int32", "data": [0, 1, 2], "encoding": {}},
                id="int32-array",
            ),
            pytest.param(
                np.array([0.0, 1.0, 2.0], dtype="float16"),
                {"__type__": "array", "dtype": "float16", "data": [0.0, 1.0, 2.0], "encoding": {}},
                id="float16-array",
            ),
            pytest.param(
                np.array([0, 1, 2], dtype="timedelta64[s]"),
                {
                    "__type__": "array",
                    "dtype": "timedelta64[s]",
                    "data": [0, 1, 2],
                    "encoding": {"units": "s"},
                },
                id="timedelta64-array",
            ),
            pytest.param(
                np.array(
                    ["2019-01-01", "2020-01-01", "2021-01-01", "2022-01-01"], dtype="datetime64[ns]"
                ),
                {
                    "__type__": "array",
                    "dtype": "datetime64[ns]",
                    "data": [0, 31536000000000000, 63158400000000000, 94694400000000000],
                    "encoding": {"units": "ns", "reference": "2019-01-01T00:00:00.000000000"},
                },
                id="datetime64-array",
            ),
            pytest.param(
                create_dummy_array(shape=(4, 3), dtype="int16"),
                {
                    "__type__": "backend_array",
                    "root": "/path/to",
                    "url": "file",
                    "shape": (4, 3),
                    "dtype": "int16",
                    "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                    "type_code": "IU2",
                },
                id="int16-backend_array",
            ),
        ),
    )
    def test_encode_array(self, arr, expected):
        actual = caching.encoders.encode_array(arr)

        assert actual == expected

    @pytest.mark.parametrize(
        ["var", "expected"],
        (
            pytest.param(
                Variable("x", np.array([1, 2], dtype="int32"), {}),
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "data": [1, 2], "dtype": "int32", "encoding": {}},
                    "attrs": {},
                },
                id="1d-array-no_attrs",
            ),
            pytest.param(
                Variable(["x", "y"], np.array([[1, 2], [2, 3], [3, 4]], dtype="int32"), {}),
                {
                    "__type__": "variable",
                    "dims": ["x", "y"],
                    "data": {
                        "__type__": "array",
                        "data": [[1, 2], [2, 3], [3, 4]],
                        "dtype": "int32",
                        "encoding": {},
                    },
                    "attrs": {},
                },
                id="2d-array-no_attrs",
            ),
            pytest.param(
                Variable("x", create_dummy_array(shape=(4,), dtype="int8"), {}),
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {
                        "__type__": "backend_array",
                        "root": "/path/to",
                        "url": "file",
                        "shape": (4,),
                        "dtype": "int8",
                        "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                        "type_code": "IU2",
                    },
                    "attrs": {},
                },
                id="1d-backend_array-no_attrs",
            ),
            pytest.param(
                Variable("x", np.array([1, 2], dtype="int32"), {"a": "a", "b": 1, "c": 1.5}),
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "data": [1, 2], "dtype": "int32", "encoding": {}},
                    "attrs": {"a": "a", "b": 1, "c": 1.5},
                },
                id="1d-array-attrs",
            ),
        ),
    )
    def test_encode_variable(self, var, expected):
        actual = caching.encoders.encode_variable(var)

        assert actual == expected

    @pytest.mark.parametrize(
        ["group", "expected"],
        (
            pytest.param(
                Group(path="path", url="abc", data={}, attrs={"abc": "def"}),
                {
                    "__type__": "group",
                    "path": "path",
                    "url": "abc",
                    "data": {},
                    "attrs": {"abc": "def"},
                },
                id="no_variables-no_subgroups",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"v": Variable("x", np.array([1, 2], dtype="int8"), {})},
                    attrs={},
                ),
                {
                    "__type__": "group",
                    "path": "/",
                    "url": None,
                    "data": {
                        "v": {
                            "__type__": "variable",
                            "dims": ["x"],
                            "data": {
                                "__type__": "array",
                                "data": [1, 2],
                                "dtype": "int8",
                                "encoding": {},
                            },
                            "attrs": {},
                        }
                    },
                    "attrs": {},
                },
                id="variables-no_subgroups",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"g": Group(path=None, url=None, data={}, attrs={"n": "g"})},
                    attrs={},
                ),
                {
                    "__type__": "group",
                    "path": "/",
                    "url": None,
                    "data": {
                        "g": {
                            "__type__": "group",
                            "path": "/g",
                            "url": None,
                            "data": {},
                            "attrs": {"n": "g"},
                        }
                    },
                    "attrs": {},
                },
                id="no_variables-subgroups",
            ),
        ),
    )
    def test_encode_group(self, group, expected):
        actual = caching.encoders.encode_group(group)

        assert actual == expected

    @pytest.mark.parametrize(
        ["obj", "expected"],
        (
            pytest.param(
                Group(path=None, url=None, data={}, attrs={"a": 1}),
                {"__type__": "group", "path": "/", "url": None, "data": {}, "attrs": {"a": 1}},
                id="group",
            ),
            pytest.param(
                Variable("x", np.array([1, 2], dtype="int64"), {}),
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "data": [1, 2], "dtype": "int64", "encoding": {}},
                    "attrs": {},
                },
                id="variable",
            ),
            pytest.param(1, 1, id="other"),
        ),
    )
    def test_encode_hierarchy(self, obj, expected):
        actual = caching.encoders.encode_hierarchy(obj)

        assert actual == expected

    @pytest.mark.parametrize(
        ["data", "expected"],
        (
            pytest.param(1, 1, id="other"),
            pytest.param((2, 3), {"__type__": "tuple", "data": [2, 3]}, id="tuple"),
            pytest.param([2, 3], [2, 3], id="list"),
            pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 2}, id="dict"),
            pytest.param(
                ({"a": 1}, 2), {"__type__": "tuple", "data": [{"a": 1}, 2]}, id="nested_tuple"
            ),
            pytest.param(
                [(2, 3), (3, 4)],
                [{"__type__": "tuple", "data": [2, 3]}, {"__type__": "tuple", "data": [3, 4]}],
                id="nested_list",
            ),
            pytest.param(
                {"a": (2, 3), "b": [{"c": 1}]},
                {"a": {"__type__": "tuple", "data": [2, 3]}, "b": [{"c": 1}]},
                id="nested_dict",
            ),
        ),
    )
    def test_preprocess(self, data, expected):
        actual = caching.encoders.preprocess(data)

        assert actual == expected


class TestDecoders:
    @pytest.mark.parametrize(
        ["data", "expected"],
        (
            pytest.param({}, {}, id="empty"),
            pytest.param({"a": 1}, {"a": 1}, id="default"),
            pytest.param({"__type__": "tuple", "data": [2, 3]}, (2, 3), id="tuple"),
            pytest.param(
                {"__type__": "array", "data": [1, 2], "dtype": "int8", "encoding": {}},
                {"__type__": "array", "data": [1, 2], "dtype": "int8", "encoding": {}},
                id="array",
            ),
        ),
    )
    def test_postprocess(self, data, expected):
        actual = caching.decoders.postprocess(data)

        assert actual == expected

    @pytest.mark.parametrize(
        ["data", "expected"],
        (
            pytest.param(
                {
                    "__type__": "array",
                    "data": [0, 3600],
                    "dtype": "datetime64[s]",
                    "encoding": {"units": "s", "reference": "2020-01-01T00:00:00"},
                },
                np.array(["2020-01-01 00:00:00", "2020-01-01 01:00:00"], dtype="datetime64[s]"),
                id="datetime-s",
            ),
            pytest.param(
                {
                    "__type__": "array",
                    "data": [0, 60000],
                    "dtype": "datetime64[ms]",
                    "encoding": {"units": "ms", "reference": "2021-01-01T00:00:00"},
                },
                np.array(["2021-01-01 00:00:00", "2021-01-01 00:01:00"], dtype="datetime64[ms]"),
                id="datetime-ms",
            ),
        ),
    )
    def test_decode_datetime(self, data, expected):
        actual = caching.decoders.decode_datetime(data)

        np.testing.assert_equal(actual, expected)

    @pytest.mark.parametrize(
        ["data", "records_per_chunk", "expected"],
        (
            pytest.param(
                {"__type__": "array", "dtype": "int8", "data": [1, 2], "encoding": {}},
                2,
                np.array([1, 2], dtype="int8"),
                id="array-int8",
            ),
            pytest.param(
                {
                    "__type__": "array",
                    "dtype": "timedelta64[s]",
                    "data": [1, 2],
                    "encoding": {"units": "s"},
                },
                2,
                np.array([1, 2], dtype="timedelta64[s]"),
                id="array-timedelta64",
            ),
            pytest.param(
                {
                    "__type__": "array",
                    "dtype": "datetime64[s]",
                    "data": [0, 120000],
                    "encoding": {"units": "ms", "reference": "1997-05-27T00:00:00.000"},
                },
                2,
                np.array(["1997-05-27 00:00:00", "1997-05-27 00:02:00"], dtype="datetime64[s]"),
                id="array-datetime64",
            ),
            pytest.param(
                {
                    "__type__": "backend_array",
                    "root": "memory:///path/to",
                    "url": "file",
                    "shape": (4, 3),
                    "dtype": "int16",
                    "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                    "type_code": "IU2",
                },
                1,
                create_dummy_array(shape=(4, 3), dtype="int16", records_per_chunk=1),
                id="backend_array-int16",
            ),
        ),
    )
    def test_decode_array(self, data, records_per_chunk, expected):
        actual = caching.decoders.decode_array(data, records_per_chunk)
        if isinstance(expected, Array):
            assert_identical(actual, expected)
        else:
            np.testing.assert_equal(actual, expected)

    @pytest.mark.parametrize(
        ["data", "rpc", "expected"],
        (
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "dtype": "int8", "data": [1, 2], "encoding": {}},
                    "attrs": {},
                },
                2,
                Variable("x", np.array([1, 2], dtype="int8"), attrs={}),
                id="array2-no_attrs",
            ),
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {
                        "__type__": "array",
                        "dtype": "float16",
                        "data": [1.5, 2.5],
                        "encoding": {},
                    },
                    "attrs": {},
                },
                3,
                Variable("x", np.array([1.5, 2.5], dtype="float16"), attrs={}),
                id="array2-no_attrs",
            ),
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "dtype": "int8", "data": [1, 2], "encoding": {}},
                    "attrs": {"a": 1},
                },
                1,
                Variable("x", np.array([1, 2], dtype="int8"), attrs={"a": 1}),
                id="array1-attrs",
            ),
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x", "y"],
                    "data": {
                        "__type__": "backend_array",
                        "root": "memory:///path/to",
                        "url": "file",
                        "shape": (4, 3),
                        "dtype": "complex64",
                        "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                        "type_code": "C*8",
                    },
                    "attrs": {},
                },
                2,
                Variable(
                    ["x", "y"],
                    create_dummy_array(
                        shape=(4, 3), dtype="complex64", records_per_chunk=2, type_code="C*8"
                    ),
                    attrs={},
                ),
                id="backend_array1-no_attrs",
            ),
        ),
    )
    def test_decode_variable(self, data, rpc, expected):
        actual = caching.decoders.decode_variable(data, records_per_chunk=rpc)

        assert_identical(actual, expected)

    @pytest.mark.parametrize(
        ["data", "rpc", "expected"],
        (
            pytest.param(
                {
                    "__type__": "group",
                    "path": "path",
                    "url": "abc",
                    "data": {},
                    "attrs": {"abc": "def"},
                },
                2,
                Group(path="path", url="abc", data={}, attrs={"abc": "def"}),
                id="no_variables-no_subgroups",
            ),
            pytest.param(
                {
                    "__type__": "group",
                    "path": "/",
                    "url": None,
                    "data": {
                        "v": {
                            "__type__": "variable",
                            "dims": ["x"],
                            "data": {
                                "__type__": "array",
                                "data": [1, 2],
                                "dtype": "int8",
                                "encoding": {},
                            },
                            "attrs": {},
                        }
                    },
                    "attrs": {},
                },
                2,
                Group(
                    path=None,
                    url=None,
                    data={"v": Variable("x", np.array([1, 2], dtype="int8"), {})},
                    attrs={},
                ),
                id="variables-no_subgroups",
            ),
            pytest.param(
                {
                    "__type__": "group",
                    "path": "/",
                    "url": None,
                    "data": {
                        "v": {
                            "__type__": "variable",
                            "dims": ["x"],
                            "data": {
                                "__type__": "backend_array",
                                "root": "memory:///path/to",
                                "url": "file",
                                "shape": (4, 3),
                                "dtype": "complex64",
                                "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                                "type_code": "C*8",
                            },
                            "attrs": {},
                        }
                    },
                    "attrs": {},
                },
                4,
                Group(
                    path=None,
                    url=None,
                    data={
                        "v": Variable(
                            "x",
                            create_dummy_array(
                                shape=(4, 3),
                                dtype="complex64",
                                type_code="C*8",
                                records_per_chunk=4,
                            ),
                            {},
                        )
                    },
                    attrs={},
                ),
                id="variables-backend_array-no_subgroups",
            ),
            pytest.param(
                {
                    "__type__": "group",
                    "path": "/",
                    "url": None,
                    "data": {
                        "g": {
                            "__type__": "group",
                            "path": "/g",
                            "url": None,
                            "data": {},
                            "attrs": {"n": "g"},
                        }
                    },
                    "attrs": {},
                },
                2,
                Group(
                    path=None,
                    url=None,
                    data={"g": Group(path=None, url=None, data={}, attrs={"n": "g"})},
                    attrs={},
                ),
                id="no_variables-subgroups",
            ),
        ),
    )
    def test_decode_group(self, data, rpc, expected):
        actual = caching.decoders.decode_group(data, records_per_chunk=rpc)

        assert_identical(actual, expected)

    @pytest.mark.parametrize(
        ["obj", "rpc", "expected"],
        (
            pytest.param(
                {"__type__": "group", "path": "/", "url": None, "data": {}, "attrs": {"a": 1}},
                2,
                Group(path=None, url=None, data={}, attrs={"a": 1}),
                id="group",
            ),
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x"],
                    "data": {"__type__": "array", "data": [1, 2], "dtype": "int64", "encoding": {}},
                    "attrs": {},
                },
                3,
                Variable("x", np.array([1, 2], dtype="int64"), {}),
                id="variable",
            ),
            pytest.param(
                {
                    "__type__": "variable",
                    "dims": ["x", "y"],
                    "data": {
                        "__type__": "backend_array",
                        "root": "memory:///path/to",
                        "url": "file",
                        "shape": (4, 3),
                        "dtype": "complex64",
                        "byte_ranges": [(5, 10), (15, 20), (25, 30), (35, 40)],
                        "type_code": "C*8",
                    },
                    "attrs": {},
                },
                4,
                Variable(
                    ["x", "y"],
                    create_dummy_array(
                        shape=(4, 3), dtype="complex64", records_per_chunk=4, type_code="C*8"
                    ),
                    attrs={},
                ),
                id="variable-backend_array",
            ),
            pytest.param({"a": 1}, 1, {"a": 1}, id="other"),
        ),
    )
    def test_decode_hierarchy(self, obj, rpc, expected):
        actual = caching.decoders.decode_hierarchy(obj, records_per_chunk=rpc)

        if not isinstance(expected, (Variable, Group)):
            assert actual == expected
        else:
            assert_identical(actual, expected)


class TestHighLevel:
    @pytest.mark.parametrize(
        ["obj", "expected"],
        (
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"v": Variable("x", np.array([1, 2], dtype="int16"), attrs={})},
                    attrs={"a": (1, 2)},
                ),
                " ".join(
                    [
                        '{"__type__": "group", "url": null, "data": {"v":',
                        '{"__type__": "variable", "dims": ["x"], "data":',
                        '{"__type__": "array", "dtype": "int16", "data": [1, 2], "encoding": {}},',
                        '"attrs": {}}}, "path": "/",',
                        '"attrs": {"a": {"__type__": "tuple", "data": [1, 2]}}}',
                    ]
                ),
                id="variables",
            ),
            pytest.param(
                Group(
                    path=None,
                    url="s3://bucket/data",
                    data={"g": Group(path=None, url=None, data={}, attrs={"g": 1})},
                    attrs={},
                ),
                " ".join(
                    [
                        '{"__type__": "group", "url": "s3://bucket/data", "data": {"g":',
                        '{"__type__": "group", "url": "s3://bucket/data", "data": {},',
                        '"path": "/g", "attrs": {"g": 1}}},',
                        '"path": "/", "attrs": {}}',
                    ]
                ),
                id="subgroups",
            ),
        ),
    )
    def test_encode(self, obj, expected):
        actual = caching.encode(obj)

        assert actual == expected

    @pytest.mark.parametrize(
        ["data", "rpc", "expected"],
        (
            pytest.param(
                " ".join(
                    [
                        '{"__type__": "group", "url": null, "data": {"v":',
                        '{"__type__": "variable", "dims": ["x"], "data":',
                        '{"__type__": "array", "dtype": "int16", "data": [1, 2], "encoding": {}},',
                        '"attrs": {}}}, "path": "/",',
                        '"attrs": {"a": {"__type__": "tuple", "data": [1, 2]}}}',
                    ]
                ),
                2,
                Group(
                    path=None,
                    url=None,
                    data={"v": Variable("x", np.array([1, 2], dtype="int16"), attrs={})},
                    attrs={"a": (1, 2)},
                ),
                id="variable",
            ),
            pytest.param(
                " ".join(
                    [
                        '{"__type__": "group", "url": "s3://bucket/data", "data": {"g":',
                        '{"__type__": "group", "url": "s3://bucket/data", "data": {},',
                        '"path": "/g", "attrs": {"g": 1}}},',
                        '"path": "/", "attrs": {}}',
                    ]
                ),
                1,
                Group(
                    path=None,
                    url="s3://bucket/data",
                    data={"g": Group(path=None, url=None, data={}, attrs={"g": 1})},
                    attrs={},
                ),
                id="subgroup",
            ),
        ),
    )
    def test_decode(self, data, rpc, expected):
        actual = caching.decode(data, records_per_chunk=rpc)

        assert_identical(actual, expected)

    @pytest.mark.parametrize(
        ["path", "rpc", "expected"],
        (
            pytest.param(
                "not-a-cache", 2, caching.CachingError("no cache found for .+"), id="not-a-cache"
            ),
            pytest.param(
                "image1",
                3,
                Group(
                    path=None,
                    url=None,
                    data={
                        "v": Variable(
                            ["x", "y"],
                            create_dummy_array(
                                shape=(4, 3),
                                dtype="complex64",
                                type_code="C*8",
                                records_per_chunk=3,
                            ),
                            {},
                        )
                    },
                    attrs={},
                ),
                id="remote_cache",
            ),
            pytest.param(
                "image2",
                4,
                Group(
                    path=None,
                    url=None,
                    data={
                        "v": Variable(
                            ["x", "y"],
                            create_dummy_array(
                                shape=(4, 3),
                                dtype="complex64",
                                type_code="C*8",
                                records_per_chunk=4,
                            ),
                            {},
                        )
                    },
                    attrs={},
                ),
                id="local_cache",
            ),
        ),
    )
    def test_read_cache(self, monkeypatch, path, rpc, expected):
        mapper = fsspec.get_mapper("memory://cache")
        data = json.dumps(
            {
                "__type__": "group",
                "url": None,
                "data": {
                    "v": {
                        "__type__": "variable",
                        "dims": ["x", "y"],
                        "data": {
                            "__type__": "backend_array",
                            "root": "memory:///path/to",
                            "url": "file",
                            "shape": {"__type__": "tuple", "data": [4, 3]},
                            "dtype": "complex64",
                            "byte_ranges": [
                                {"__type__": "tuple", "data": [5, 10]},
                                {"__type__": "tuple", "data": [15, 20]},
                                {"__type__": "tuple", "data": [25, 30]},
                                {"__type__": "tuple", "data": [35, 40]},
                            ],
                            "type_code": "C*8",
                        },
                        "attrs": {},
                    }
                },
                "path": "/",
                "attrs": {},
            }
        )
        mapper["image1.index"] = data.encode()

        def fake_is_file(self):
            return self.name == "image2.index"

        def fake_read_text(self):
            if self.name == "image2.index":
                return data
            else:
                raise IOError

        monkeypatch.setattr(Path, "is_file", fake_is_file)
        monkeypatch.setattr(Path, "read_text", fake_read_text)

        if isinstance(expected, Exception):
            with pytest.raises(type(expected), match=expected.args[0]):
                caching.read_cache(mapper, path, records_per_chunk=rpc)

            return

        actual = caching.read_cache(mapper, path, records_per_chunk=rpc)

        assert_identical(actual, expected)

    def test_create_cache(self, monkeypatch):
        monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)

        parameters = []

        def recorder(*args):
            nonlocal parameters
            parameters.append(args)

        monkeypatch.setattr(Path, "write_text", recorder)

        mapper = fsspec.get_mapper("memory://")
        path = "image"
        data = Group(path="/", url="s3://bucket/data", data={}, attrs={})

        expected = (
            '{"__type__": "group", "url": "s3://bucket/data",'
            ' "data": {}, "path": "/", "attrs": {}}'
        )

        caching.create_cache(mapper, path, data)

        actual_path, actual_data = parameters[0]

        assert actual_path.name == f"{path}.index"
        assert actual_data == expected
