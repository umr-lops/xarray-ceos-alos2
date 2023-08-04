import numpy as np
import pytest

from ceos_alos2 import hierarchy
from ceos_alos2.tests.utils import create_dummy_array


class TestVariable:
    @pytest.mark.parametrize(
        ["dims", "data"],
        (
            pytest.param("x", np.arange(5), id="str-1d"),
            pytest.param(["x"], np.arange(5), id="list-1d"),
            pytest.param(["x", "y"], np.arange(6).reshape(3, 2), id="list-2d"),
        ),
    )
    @pytest.mark.parametrize(
        "attrs",
        (
            {},
            {"a": 1},
        ),
    )
    def test_init(self, dims, data, attrs):
        var = hierarchy.Variable(dims=dims, data=data, attrs=attrs)

        if isinstance(dims, str):
            dims = [dims]

        assert var.dims == dims
        assert type(var.data) is type(data) and np.all(var.data == data)
        assert var.attrs == attrs

    @pytest.mark.parametrize(
        ["dims", "data", "expected"],
        (
            pytest.param(["x"], np.arange(5), 1, id="1d"),
            pytest.param(["x", "y"], np.arange(6).reshape(3, 2), 2, id="2d"),
        ),
    )
    def test_ndim(self, dims, data, expected):
        var = hierarchy.Variable(dims=dims, data=data, attrs={})
        actual = var.ndim

        assert actual == expected

    @pytest.mark.parametrize(
        ["dims", "data", "expected"],
        (
            pytest.param(["x"], np.arange(5), (5,), id="1d"),
            pytest.param(["x", "y"], np.arange(6).reshape(3, 2), (3, 2), id="2d"),
        ),
    )
    def test_shape(self, dims, data, expected):
        var = hierarchy.Variable(dims=dims, data=data, attrs={})
        actual = var.shape

        assert actual == expected

    @pytest.mark.parametrize(
        ["dims", "data", "expected"],
        (
            pytest.param(["x"], np.arange(5, dtype="int8"), "int8", id="int"),
            pytest.param(["x"], np.arange(5, dtype="float16"), "float16", id="int"),
            pytest.param(["x"], np.arange(5, dtype="complex64"), "complex64", id="int"),
        ),
    )
    def test_dtype(self, dims, data, expected):
        var = hierarchy.Variable(dims=dims, data=data, attrs={})
        actual = var.dtype

        assert actual == expected

    @pytest.mark.parametrize(
        ["data", "expected"],
        (
            pytest.param(np.arange(12).reshape(3, 4), {}, id="numpy"),
            pytest.param(create_dummy_array(shape=(4, 3)), {"rows": 2, "cols": 3}, id="array"),
        ),
    )
    def test_chunks(self, data, expected):
        dims = ["rows", "cols"]
        var = hierarchy.Variable(dims=dims, data=data, attrs={})

        actual = var.chunks

        assert actual == expected

    @pytest.mark.parametrize(
        ["dims", "data", "expected"],
        (
            pytest.param(["x"], np.arange(5), {"x": 5}, id="1d"),
            pytest.param(["x", "y"], np.arange(6).reshape(3, 2), {"x": 3, "y": 2}, id="2d"),
            pytest.param(
                ["y", "x"], np.arange(6).reshape(3, 2), {"y": 3, "x": 2}, id="2d-switched"
            ),
        ),
    )
    def test_sizes(self, dims, data, expected):
        var = hierarchy.Variable(dims=dims, data=data, attrs={})
        actual = var.sizes

        assert actual == expected

    @pytest.mark.parametrize(
        ["a", "b", "expected"],
        (
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                [1],
                False,
                id="type_mismatch",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                True,
                id="identical-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                hierarchy.Variable(dims="y", data=np.array([1]), attrs={}),
                False,
                id="different_dims-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                hierarchy.Variable(dims="x", data=np.array([2]), attrs={}),
                False,
                id="different_data-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={}),
                hierarchy.Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                False,
                id="different_data-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                hierarchy.Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                True,
                id="identical_array-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                hierarchy.Variable(dims="x", data=create_dummy_array(shape=(2,)), attrs={}),
                False,
                id="different_array-without_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                True,
                id="identical-identical_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 2}),
                False,
                id="identical-different_attrs",
            ),
            pytest.param(
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                hierarchy.Variable(dims="x", data=np.array([1]), attrs={"a": 1, "b": 1}),
                False,
                id="identical-mismatching_attrs",
            ),
        ),
    )
    def test_identical(self, a, b, expected):
        actual = a.identical(b)

        assert actual == expected
