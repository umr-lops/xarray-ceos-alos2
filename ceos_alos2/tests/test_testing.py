import numpy as np
import pytest

from ceos_alos2 import testing
from ceos_alos2.hierarchy import Variable
from ceos_alos2.tests.utils import create_dummy_array


@pytest.mark.parametrize("b", ({"a": 1}, {"c": 1}, {"a": 1, "c": 1}))
@pytest.mark.parametrize("a", ({"a": 1}, {"b": 1}, {"a": 1, "b": 1}))
def test_dict_overlap(a, b):
    missing_left, common, missing_right = testing.dict_overlap(a, b)

    assert set(a) == set(missing_right) | set(common)
    assert set(b) == set(missing_left) | set(common)

    assert all(k in a and k in b for k in common)
    assert all(k not in a and k in b for k in missing_left)
    assert all(k in a and k not in b for k in missing_right)


@pytest.mark.parametrize(
    ["item", "expected"],
    (
        (np.int16(1), "1"),
        (np.float16(3.5), "3.5"),
        (np.complex64(1.5 + 1.5j), "(1.5+1.5j)"),
        (np.str_("abc"), "'abc'"),
        (np.datetime64("2011-04-27 00:00:00.0", "ms"), "2011-04-27T00:00:00.000"),
        (np.timedelta64(201, "s"), "201 seconds"),
    ),
)
def test_format_item(item, expected):
    actual = testing.format_item(item)

    assert actual == expected


@pytest.mark.parametrize(
    ["arr", "expected"],
    (
        (np.array([0, 1], dtype="int8"), "int8  0 1"),
        (np.arange(10, dtype="int32"), "int32  0 1 2 ... 8 9"),
        (
            create_dummy_array(shape=(4, 3)),
            "\n".join(
                ["Array(shape=(4, 3), dtype=int16, rpc=2)", "    url: memory:///path/to/file"]
            ),
        ),
    ),
)
def test_format_array(arr, expected):
    actual = testing.format_array(arr)

    assert actual == expected


@pytest.mark.parametrize(
    ["var", "expected"],
    (
        (Variable("x", np.array([0, 1], dtype="int8"), {}), "(x)    int8  0 1"),
        (Variable(["x"], np.array([0, 1], dtype="int16"), {}), "(x)    int16  0 1"),
        (
            Variable(["x", "y"], np.array([[0, 1], [2, 3]], dtype="int32"), {}),
            "(x, y)    int32  0 1 2 3",
        ),
        (
            Variable("x", np.array([0, 1], dtype="int8"), {"a": 1}),
            "\n".join(["(x)    int8  0 1", "    a: 1"]),
        ),
        (
            Variable("x", np.array([0, 1], dtype="int64"), {"a": 1, "b": "b"}),
            "\n".join(["(x)    int64  0 1", "    a: 1", "    b: b"]),
        ),
    ),
)
def test_format_variable(var, expected):
    actual = testing.format_variable(var)

    assert actual == expected


@pytest.mark.parametrize("keys", (["ab"], ["ab", "cd"]))
@pytest.mark.parametrize("side", ("left", "right"))
def test_diff_mapping_missing(keys, side):
    diff = testing.diff_mapping_missing(keys, side)

    assert side in diff
    assert all(f"- {key}" in diff for key in keys)


@pytest.mark.parametrize("name", ("attributes", "variables", "groups"))
@pytest.mark.parametrize(
    ["left", "right", "unequal"],
    (
        pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 3}, ["b"]),
        pytest.param({"a": 2, "b": 2}, {"a": 1, "b": 3}, ["a", "b"]),
        pytest.param({"c": 1, "e": 5}, {"c": 2, "e": 2}, ["c", "e"]),
        pytest.param({"c": Variable("x", 1, {})}, {"c": Variable("y", 1, {})}, ["c"]),
    ),
)
def test_diff_mapping_not_equal(left, right, unequal, name):
    actual = testing.diff_mapping_not_equal(left, right, name=name)

    assert actual.startswith(f"Differing {name}")
    assert all(f"L {k} " in actual and f"R {k} " in actual for k in unequal)


@pytest.mark.parametrize("name", ("Attributes", "Variables", "Groups"))
@pytest.mark.parametrize(
    ["left", "right", "missing_left", "common_unequal", "missing_right"],
    (
        pytest.param({"b": 2}, {"b": 2, "c": 3}, True, False, False, id="missing_left"),
        pytest.param({"a": 1, "b": 2}, {"b": 2}, False, False, True, id="missing_right"),
        pytest.param({"b": 2}, {"b": 3}, False, True, False, id="unequal_common"),
        pytest.param({"b": 2}, {"b": 2}, False, False, False, id="all_equal"),
        pytest.param(
            {"b": 2}, {"b": 3, "c": 3}, True, True, False, id="unequal_common-missing_left"
        ),
        pytest.param(
            {"a": 1, "b": 2}, {"b": 3}, False, True, True, id="unequal_common-missing_right"
        ),
        pytest.param({"a": 1}, {"c": 3}, True, False, True, id="disjoint"),
        pytest.param({"a": 1, "b": 2}, {"b": 3, "c": 3}, True, True, True, id="all_different"),
    ),
)
def test_diff_mapping(left, right, missing_left, common_unequal, missing_right, name):
    actual = testing.diff_mapping(left, right, name=name)

    assert actual.startswith(name)
    assert not missing_left or "Missing left" in actual
    assert not common_unequal or f"Differing {name.lower()}" in actual
    assert not missing_right or "Missing right" in actual


@pytest.mark.parametrize("name", ["name1", "Name2"])
@pytest.mark.parametrize(["left", "right"], [(1, 2), ("a", "b")])
def test_diff_scalar(left, right, name):
    actual = testing.diff_scalar(left, right, name=name)

    assert name.title() in actual
    assert f"L  {left}" in actual
    assert f"R  {right}" in actual


@pytest.mark.parametrize(
    ["left", "right", "expected"],
    (
        pytest.param(
            np.array([1], dtype="int32"), create_dummy_array(), False, id="different_types"
        ),
        pytest.param(
            np.array([1, 2], dtype="int64"), np.array([1, 2], dtype="int64"), True, id="numpy-equal"
        ),
        pytest.param(
            np.array([1], dtype="int32"),
            np.array([2, 2], dtype="int32"),
            False,
            id="numpy-different_shapes",
        ),
        pytest.param(
            np.array([1], dtype="int32"),
            np.array([2], dtype="float32"),
            False,
            id="numpy-different_values",
        ),
        pytest.param(
            create_dummy_array(dtype="int32"),
            create_dummy_array(dtype="float64"),
            False,
            id="array-different_dtypes",
        ),
        pytest.param(create_dummy_array(), create_dummy_array(), True, id="array-equal"),
    ),
)
def test_compare_data(left, right, expected):
    actual = testing.compare_data(left, right)

    assert actual == expected


@pytest.mark.parametrize(
    ["left", "right", "expected"],
    (
        pytest.param(
            np.array([1], dtype="int32"),
            np.array([2, 3], dtype="int8"),
            "\n".join(["  L int32  1", "  R int8  2 3"]),
            id="numpy",
        ),
        pytest.param(
            create_dummy_array(protocol="memory"),
            create_dummy_array(protocol="file"),
            "\n".join(
                [
                    "Differing filesystem:",
                    "  L protocol  memory",
                    "  R protocol  file",
                ]
            ),
            id="array-fs-protocol",
        ),
        pytest.param(
            create_dummy_array(path="/path/to1"),
            create_dummy_array(path="/path/to2"),
            "\n".join(
                [
                    "Differing filesystem:",
                    "  L path  /path/to1",
                    "  R path  /path/to2",
                ]
            ),
            id="array-fs-path",
        ),
        pytest.param(
            create_dummy_array(url="file1"),
            create_dummy_array(url="file2"),
            "\n".join(
                [
                    "Differing urls:",
                    "  L url  file1",
                    "  R url  file2",
                ]
            ),
            id="array-url",
        ),
        pytest.param(
            create_dummy_array(byte_ranges=[(0, 1), (2, 3), (3, 4), (4, 5)]),
            create_dummy_array(byte_ranges=[(0, 2), (2, 3), (3, 4), (4, 5)]),
            "\n".join(
                [
                    "Differing byte ranges:",
                    "  L line 1  (0, 1)",
                    "  R line 1  (0, 2)",
                ]
            ),
            id="array-byte_ranges",
        ),
        pytest.param(
            create_dummy_array(shape=(4, 3), byte_ranges=[]),
            create_dummy_array(shape=(6, 3), byte_ranges=[]),
            "\n".join(
                [
                    "Differing shapes:",
                    "  (4, 3) != (6, 3)",
                ]
            ),
            id="array-shape",
        ),
        pytest.param(
            create_dummy_array(dtype="int8"),
            create_dummy_array(dtype="int16"),
            "\n".join(
                [
                    "Differing dtypes:",
                    "  int8 != int16",
                ]
            ),
            id="array-dtype",
        ),
        pytest.param(
            create_dummy_array(type_code="IU2"),
            create_dummy_array(type_code="C*8"),
            "\n".join(
                [
                    "Differing type code:",
                    "  L type_code  IU2",
                    "  R type_code  C*8",
                ]
            ),
            id="array-type_code",
        ),
        pytest.param(
            create_dummy_array(records_per_chunk=2),
            create_dummy_array(records_per_chunk=1),
            "\n".join(
                [
                    "Differing chunksizes:",
                    "  L records_per_chunk  2",
                    "  R records_per_chunk  1",
                ]
            ),
            id="array-rpc",
        ),
    ),
)
def test_diff_array(left, right, expected):
    actual = testing.diff_array(left, right)

    assert actual == expected
