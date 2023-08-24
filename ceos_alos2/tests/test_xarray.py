import numpy as np
import pytest
import xarray as xr

from ceos_alos2 import xarray
from ceos_alos2.hierarchy import Variable
from ceos_alos2.tests.utils import create_dummy_array


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
