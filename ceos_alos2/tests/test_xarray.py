import datatree
import datatree.testing
import numpy as np
import pytest
import xarray as xr
from xarray.core.indexing import BasicIndexer, VectorizedIndexer

from ceos_alos2 import xarray
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.tests.utils import create_dummy_array


class TestLazilyIndexedWrapper:
    def test_init(self):
        lock = xarray.SerializableLock()

        data = create_dummy_array()

        wrapper = xarray.LazilyIndexedWrapper(data, lock)

        assert wrapper.shape == data.shape
        assert wrapper.dtype == data.dtype
        assert wrapper.array is data
        assert wrapper.lock is lock

    @pytest.mark.parametrize(
        "indexer",
        (
            pytest.param(BasicIndexer((0, 1))),
            pytest.param(VectorizedIndexer((slice(None), slice(None)))),
        ),
    )
    def test_getitem(self, indexer):
        array = np.arange(6).reshape(2, 3)
        expected = array[indexer.tuple]

        lock = xarray.SerializableLock()
        wrapped = xarray.LazilyIndexedWrapper(array, lock)

        actual = wrapped[indexer]

        np.testing.assert_equal(actual, expected)


@pytest.mark.parametrize(
    ["var", "expected"],
    (
        pytest.param(Variable("x", np.array([1], dtype="int8"), {}), {}, id="numpy-no_chunks"),
        pytest.param(
            Variable("x", create_dummy_array(shape=(4,), records_per_chunk=2), {}),
            {"preferred_chunksizes": {"x": 2}},
            id="array-chunks1d",
        ),
        pytest.param(
            Variable(["a", "b"], create_dummy_array(shape=(4, 3), records_per_chunk=1), {}),
            {"preferred_chunksizes": {"a": 1, "b": 3}},
            id="array-chunks2d",
        ),
    ),
)
def test_extract_encoding(var, expected):
    actual = xarray.extract_encoding(var)

    assert actual == expected


@pytest.mark.parametrize(
    ["ds", "expected"],
    (
        (xr.Dataset({"a": 1, "b": 2}, attrs={}), xr.Dataset({"a": 1, "b": 2}, attrs={})),
        (
            xr.Dataset({"a": 1, "b": 2}, attrs={"coordinates": ["a"]}),
            xr.Dataset({"b": 2}, coords={"a": 1}, attrs={}),
        ),
        (
            xr.Dataset({"a": 1, "b": 2}, attrs={"coordinates": ["b"]}),
            xr.Dataset({"a": 1}, coords={"b": 2}, attrs={}),
        ),
        (
            xr.Dataset({"a": 1, "b": 2}, attrs={"coordinates": ["a", "b"]}),
            xr.Dataset({}, coords={"a": 1, "b": 2}, attrs={}),
        ),
    ),
)
def test_decode_coords(ds, expected):
    actual = xarray.decode_coords(ds)

    xr.testing.assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["var", "expected"],
    (
        pytest.param(Variable("x", np.array([1, 2], dtype="int8"), {"a": 1}), True, id="in_memory"),
        pytest.param(Variable(["x", "y"], create_dummy_array(), {"b": 3}), False, id="lazy"),
    ),
)
def test_to_variable(var, expected):
    actual = xarray.to_variable(var)

    assert actual._in_memory == expected
    assert tuple(var.dims) == actual.dims
    assert var.attrs == actual.attrs


@pytest.mark.parametrize("chunks", [None, {}, {"x": 1, "y": 2}])
@pytest.mark.parametrize(
    ["group", "expected"],
    (
        pytest.param(
            Group(path=None, url=None, data={}, attrs={"a": 1, "b": 2, "c": 3}),
            xr.Dataset(attrs={"a": 1, "b": 2, "c": 3}),
            id="attrs",
        ),
        pytest.param(
            Group(
                path=None,
                url=None,
                data={
                    "a": Variable("x", np.array([1, 2, 3], dtype="int8"), {"a": 1}),
                    "b": Variable(["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"}),
                },
                attrs={},
            ),
            xr.Dataset(
                {
                    "a": ("x", np.array([1, 2, 3], dtype="int8"), {"a": 1}),
                    "b": (["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"}),
                }
            ),
            id="variables",
        ),
        pytest.param(
            Group(
                path=None,
                url=None,
                data={
                    "c": Variable("x", np.array([1, 2, 3], dtype="int8"), {"a": 1}),
                    "d": Variable(["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"}),
                },
                attrs={"coordinates": ["d"]},
            ),
            xr.Dataset(
                {"c": ("x", np.array([1, 2, 3], dtype="int8"), {"a": 1})},
                coords={"d": (["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"})},
            ),
            id="coords",
        ),
    ),
)
def test_to_dataset(group, chunks, expected):
    actual = xarray.to_dataset(group, chunks=chunks)

    xr.testing.assert_identical(actual, expected)


@pytest.mark.parametrize("chunks", [None, {}, {"x": 1, "y": 2}])
@pytest.mark.parametrize(
    ["group", "expected"],
    (
        pytest.param(
            Group(
                path=None,
                url=None,
                data={
                    "c": Variable("x", np.array([1, 2, 3], dtype="int8"), {"a": 1}),
                    "d": Variable(["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"}),
                },
                attrs={"coordinates": ["d"]},
            ),
            datatree.DataTree.from_dict(
                {
                    "/": xr.Dataset(
                        {"c": ("x", [1, 2, 3], {"a": 1})},
                        coords={"d": (["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"})},
                    )
                }
            ),
            id="flat",
        ),
        pytest.param(
            Group(
                path=None,
                url=None,
                data={
                    "c": Variable("x", np.array([1, 2, 3], dtype="int8"), {"a": 1}),
                    "d": Group(
                        path=None,
                        url=None,
                        data={"e": Variable(["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"})},
                        attrs={},
                    ),
                },
                attrs={},
            ),
            datatree.DataTree.from_dict(
                {
                    "/": xr.Dataset({"c": ("x", [1, 2, 3], {"a": 1})}),
                    "d": xr.Dataset({"e": (["x", "y"], np.arange(12).reshape(3, 4), {"b": "abc"})}),
                }
            ),
            id="nested",
        ),
    ),
)
def test_to_datatree(group, chunks, expected):
    actual = xarray.to_datatree(group, chunks=chunks)

    datatree.testing.assert_identical(actual, expected)
