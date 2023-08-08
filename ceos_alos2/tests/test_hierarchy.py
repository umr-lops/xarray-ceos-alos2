import posixpath

import numpy as np
import pytest

from ceos_alos2.hierarchy import Group, Variable
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
        var = Variable(dims=dims, data=data, attrs=attrs)

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
        var = Variable(dims=dims, data=data, attrs={})
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
        var = Variable(dims=dims, data=data, attrs={})
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
        var = Variable(dims=dims, data=data, attrs={})
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
        var = Variable(dims=dims, data=data, attrs={})

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
        var = Variable(dims=dims, data=data, attrs={})
        actual = var.sizes

        assert actual == expected

    @pytest.mark.parametrize(
        ["a", "b", "expected"],
        (
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={}),
                [1],
                False,
                id="type_mismatch",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={}),
                Variable(dims="x", data=np.array([1]), attrs={}),
                True,
                id="identical-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={}),
                Variable(dims="y", data=np.array([1]), attrs={}),
                False,
                id="different_dims-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={}),
                Variable(dims="x", data=np.array([2]), attrs={}),
                False,
                id="different_data-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={}),
                Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                False,
                id="different_data-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                True,
                id="identical_array-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=create_dummy_array(shape=(1,)), attrs={}),
                Variable(dims="x", data=create_dummy_array(shape=(2,)), attrs={}),
                False,
                id="different_array-without_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                True,
                id="identical-identical_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                Variable(dims="x", data=np.array([1]), attrs={"a": 2}),
                False,
                id="identical-different_attrs",
            ),
            pytest.param(
                Variable(dims="x", data=np.array([1]), attrs={"a": 1}),
                Variable(dims="x", data=np.array([1]), attrs={"a": 1, "b": 1}),
                False,
                id="identical-mismatching_attrs",
            ),
        ),
    )
    def test_equal(self, a, b, expected):
        actual = a == b

        assert actual == expected


class TestGroup:
    @pytest.mark.parametrize("attrs", [{"a": 1}, {"a": 1, "b": 2}, {"b": 3, "c": 4}])
    @pytest.mark.parametrize("data", [{"a": Variable("x", [1], {})}])
    @pytest.mark.parametrize("url", (None, "file:///a", "memory:///a"))
    @pytest.mark.parametrize("path", (None, "/", "/a/b"))
    def test_init_flat(self, path, url, data, attrs):
        group = Group(path=path, url=url, data=data, attrs=attrs)

        if path is None:
            path = "/"

        assert group.path == path
        assert group.url == url
        assert group.data == data
        assert group.attrs == attrs

    @pytest.mark.parametrize(
        ["structure"],
        (
            pytest.param(
                {
                    "a": {"path": "/a", "url": "file:///a", "data": {}, "attrs": {"a": 1}},
                    "b": {"path": "/b", "url": "file:///b", "data": {}, "attrs": {"b": 1}},
                }
            ),
            pytest.param(
                {
                    "a": {"path": None, "url": "file:///a", "data": {}, "attrs": {"a": 1}},
                    "b": {"path": None, "url": "file:///b", "data": {}, "attrs": {"b": 1}},
                }
            ),
            pytest.param(
                {
                    "a": {"path": "/a", "url": None, "data": {}, "attrs": {"a": 1}},
                    "b": {"path": "/b", "url": None, "data": {}, "attrs": {"b": 1}},
                }
            ),
        ),
    )
    @pytest.mark.parametrize("url", [None, "file:///r", "memory:///r"])
    @pytest.mark.parametrize("path", [None, "/", "/abc"])
    def test_init_nested(self, path, url, structure):
        subgroups = {name: Group(**kwargs) for name, kwargs in structure.items()}
        group = Group(path=path, url=url, data=subgroups, attrs={})

        if path is None:
            path = "/"

        assert group.path == path
        assert group.url == url

        assert all(
            subgroup.path == posixpath.join(group.path, name)
            for name, subgroup in group.data.items()
        )
        assert all(
            subgroup.url == (structure[name]["url"] or group.url)
            for name, subgroup in group.data.items()
        )

    @pytest.mark.parametrize(
        ["first", "second", "expected"],
        (
            pytest.param(
                Group(path=None, url=None, data={}, attrs={}),
                Group(path=None, url=None, data={}, attrs={}),
                True,
                id="all_equal",
            ),
            pytest.param(
                Group(path=None, url=None, data={}, attrs={}),
                1,
                False,
                id="mismatching_types",
            ),
            pytest.param(
                Group(path="a", url=None, data={}, attrs={}),
                Group(path="b", url=None, data={}, attrs={}),
                False,
                id="path",
            ),
            pytest.param(
                Group(path=None, url="a", data={}, attrs={}),
                Group(path=None, url="b", data={}, attrs={}),
                False,
                id="url",
            ),
            pytest.param(
                Group(path=None, url=None, data={}, attrs={"a": 1}),
                Group(path=None, url=None, data={}, attrs={"a": 2}),
                False,
                id="attrs",
            ),
            pytest.param(
                Group(path=None, url=None, data={"a": Variable("x", [], {})}, attrs={}),
                Group(path=None, url=None, data={}, attrs={}),
                False,
                id="variables_mismatching",
            ),
            pytest.param(
                Group(path=None, url=None, data={"a": Group(None, None, {}, {})}, attrs={}),
                Group(path=None, url=None, data={}, attrs={}),
                False,
                id="groups_mismatching",
            ),
            pytest.param(
                Group(path=None, url=None, data={"a": Variable("x", [], {})}, attrs={}),
                Group(path=None, url=None, data={"a": Variable("y", [], {})}, attrs={}),
                False,
                id="unequal_variables",
            ),
            pytest.param(
                Group(path=None, url=None, data={"a": Variable("x", [], {})}, attrs={}),
                Group(path=None, url=None, data={"a": Variable("x", [], {})}, attrs={}),
                True,
                id="equal_variables",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(None, None, {}, {"a": 1})},
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(None, None, {}, {"a": 2})},
                    attrs={},
                ),
                False,
                id="unequal_groups",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(None, None, {}, {"a": 1})},
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(None, None, {}, {"a": 1})},
                    attrs={},
                ),
                True,
                id="equal_variables",
            ),
        ),
    )
    def test_equal(self, first, second, expected):
        actual = first == second

        assert actual == expected

    @pytest.mark.parametrize("key", ["b", "c", "e"])
    def test_getitem(self, key):
        subgroups = {
            "a": Group(path=None, url=None, data={}, attrs={"a": 1}),
            "b": Group(path=None, url=None, data={}, attrs={"b": 1}),
            "c": Group(path=None, url=None, data={}, attrs={"c": 1}),
            "d": Group(path=None, url=None, data={}, attrs={"d": 1}),
        }

        group = Group(path=None, url=None, data=subgroups, attrs={})

        if key not in subgroups:
            with pytest.raises(KeyError):
                group[key]

            return

        actual = group[key]
        expected = subgroups[key]
        expected.path = f"/{key}"

        assert actual == expected

    @pytest.mark.parametrize(
        "item",
        [
            Variable("x", [], {}),
            Group(None, "abc", {}, {}),
        ],
    )
    def test_setitem(self, item):
        group = Group(None, None, {}, {})

        group["a"] = item

        if isinstance(item, Group):
            item.path = "/a"
        assert group.data["a"] == item

    @pytest.mark.parametrize(
        ["group", "expected"],
        (
            pytest.param(Group(None, None, {}, {}), 0, id="default"),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {})}, {}), 1, id="single_variable"
            ),
            pytest.param(
                Group(None, None, {"b": Group(None, None, {}, {})}, {}), 1, id="single_group"
            ),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {}), "b": Group(None, None, {}, {})}, {}),
                2,
                id="mixed",
            ),
        ),
    )
    def test_len(self, group, expected):
        actual = len(group)

        assert actual == expected

    @pytest.mark.parametrize(
        ["group", "expected"],
        (
            pytest.param(Group(None, None, {}, {}), [], id="default"),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {})}, {}), ["a"], id="single_variable"
            ),
            pytest.param(
                Group(None, None, {"b": Group(None, None, {}, {})}, {}), ["b"], id="single_group"
            ),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {}), "b": Group(None, None, {}, {})}, {}),
                ["a", "b"],
                id="mixed",
            ),
        ),
    )
    def test_iter(self, group, expected):
        actual = list(group)

        assert actual == expected

    @pytest.mark.parametrize(
        ["group", "expected"],
        (
            pytest.param(Group(None, None, {}, {}), "/", id="default"),
            pytest.param(Group("/", None, {}, {}), "/", id="root"),
            pytest.param(Group("abc", None, {}, {}), "abc", id="name"),
            pytest.param(Group("a/b", None, {}, {}), "b", id="relative"),
            pytest.param(Group("/a/abc", None, {}, {}), "abc", id="absolute"),
        ),
    )
    def test_name(self, group, expected):
        actual = group.name

        assert actual == expected

    @pytest.mark.parametrize(
        "group",
        (
            pytest.param(Group(None, None, {}, {}), id="default"),
            pytest.param(Group(None, None, {"a": Variable("x", [], {})}, {}), id="single_variable"),
            pytest.param(
                Group(None, None, {"b": Group(None, None, {}, {})}, {}), id="single_group"
            ),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {}), "b": Group(None, None, {}, {})}, {}),
                id="mixed",
            ),
        ),
    )
    def test_groups(self, group):
        actual = group.groups

        assert all(isinstance(item, Group) for item in actual.values())

    @pytest.mark.parametrize(
        "group",
        (
            pytest.param(Group(None, None, {}, {}), id="default"),
            pytest.param(Group(None, None, {"a": Variable("x", [], {})}, {}), id="single_variable"),
            pytest.param(
                Group(None, None, {"b": Group(None, None, {}, {})}, {}), id="single_group"
            ),
            pytest.param(
                Group(None, None, {"a": Variable("x", [], {}), "b": Group(None, None, {}, {})}, {}),
                id="mixed",
            ),
        ),
    )
    def test_variables(self, group):
        actual = group.variables

        assert all(isinstance(item, Variable) for item in actual.values())

    def test_decouple(self):
        subgroups = {
            "a": Group("a", None, {}, {}),
            "b": Group("b", None, {}, {}),
        }
        variables = {
            "v1": Variable(["x"], [], {}),
            "v2": Variable(["y"], [], {}),
        }
        group = Group("a", None, data=subgroups | variables, attrs={})

        actual = group.decouple()

        assert actual.groups == {}
        assert actual.variables == variables
        assert actual.path == group.path
        assert actual.url == group.url
        assert actual.attrs == group.attrs

    def test_subtree(self):
        group = Group(
            "/",
            None,
            {
                "a": Group(
                    "a",
                    None,
                    {
                        "aa": Group("aa", None, {}, {"n": "aa"}),
                        "ab": Group("ab", None, {}, {"n": "ab"}),
                    },
                    {"n": "a"},
                ),
                "b": Group(
                    "b",
                    None,
                    {
                        "ba": Group("ba", None, {}, {"n": "ba"}),
                        "bb": Group("bb", None, {}, {"n": "bb"}),
                    },
                    {"n": "b"},
                ),
                "v": Variable("x", [], {}),
            },
            {"n": ""},
        )

        expected = {
            "/": Group("/", None, {"v": Variable("x", [], {})}, {"n": ""}),
            "/a": Group("/a", None, {}, {"n": "a"}),
            "/a/aa": Group("/a/aa", None, {}, {"n": "aa"}),
            "/a/ab": Group("/a/ab", None, {}, {"n": "ab"}),
            "/b": Group("/b", None, {}, {"n": "b"}),
            "/b/ba": Group("/b/ba", None, {}, {"n": "ba"}),
            "/b/bb": Group("/b/bb", None, {}, {"n": "bb"}),
        }

        actual = dict(group.subtree)

        assert actual == expected
