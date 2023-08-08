from pathlib import Path

import numpy as np
import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_image import caching
from ceos_alos2.sar_image.caching.path import project_name
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
                    "data": {"__type__": "array", "data": [1, 2], "dtype": "int32", "encoding": {}},
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
