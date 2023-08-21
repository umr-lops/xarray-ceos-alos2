import pytest

from ceos_alos2 import transformers
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.testing import assert_identical


@pytest.mark.parametrize(
    ["s", "expected"],
    (
        ("1990012012563297", "1990-01-20T12:56:32.970000"),
        ("2001112923595915", "2001-11-29T23:59:59.150000"),
    ),
)
def test_parse_datetime(s, expected):
    actual = transformers.normalize_datetime(s)

    assert actual == expected


@pytest.mark.parametrize(
    ["mapping", "expected"],
    (
        pytest.param({"spare1": "", "spare2": ""}, {}, id="spares"),
        pytest.param({"blanks1": "", "blanks20": "", "blanks": ""}, {}, id="blanks"),
        pytest.param(
            {"spare_values": "", "blank_page": ""},
            {"spare_values": "", "blank_page": ""},
            id="false_positives",
        ),
        pytest.param({"a": {"b": {"blanks": ""}}}, {"a": {"b": {}}}, id="nested-dict"),
        pytest.param({"a": [{"b": {"blanks": ""}}]}, {"a": [{"b": {}}]}, id="nested-list"),
    ),
)
def test_remove_spares(mapping, expected):
    actual = transformers.remove_spares(mapping)

    assert actual == expected


@pytest.mark.parametrize(
    ["value", "expected"],
    (
        pytest.param(("", ((), [])), "variable", id="variable"),
        pytest.param(("", ["abc"]), "variable", id="variable-array"),
        pytest.param(("", {}), "group", id="group"),
        pytest.param(("", ({}, {})), "group", id="group_with_attrs"),
        pytest.param(("", "abc"), "attribute", id="attribute"),
    ),
)
def test_item_type(value, expected):
    actual = transformers.item_type(value)

    assert actual == expected


@pytest.mark.parametrize(
    ["mapping", "expected"],
    (
        pytest.param(
            [{"a": {"b": 1, "c": 2}}, {"a": {"b": 2, "c": 3}}, {"a": {"b": 3, "c": 4}}],
            {"a": {"b": [1, 2, 3], "c": [2, 3, 4]}},
        ),
        pytest.param(
            [
                {"a": {"b": 1, "c": 2}, "d": {"e": 3}},
                {"a": {"b": 2, "c": 3}, "d": {"e": 4}},
                {"a": {"b": 3, "c": 4}, "d": {"e": 5}},
            ],
            {"a": {"b": [1, 2, 3], "c": [2, 3, 4]}, "d": {"e": [3, 4, 5]}},
        ),
        pytest.param([{"a": 1}, {"a": 2}, {"a": 3}], {"a": [1, 2, 3]}),
    ),
)
def test_transform_nested(mapping, expected):
    actual = transformers.transform_nested(mapping)

    assert actual == expected


@pytest.mark.parametrize(
    ["value", "expected"],
    (
        pytest.param(
            [(1, {"abc": "def"}), (2, {"abc": "def"}), (3, {"abc": "def"})],
            ([1, 2, 3], {"abc": "def"}),
        ),
        pytest.param(
            [(6, {"cba": "fed"}), (2, {"cba": "fed"}), (3, {"cba": "fed"})],
            ([6, 2, 3], {"cba": "fed"}),
        ),
        pytest.param(
            [6, 2, 3],
            ([6, 2, 3], {}),
        ),
    ),
)
def test_separate_attrs(value, expected):
    actual = transformers.separate_attrs(value)

    assert actual == expected


@pytest.mark.parametrize(
    ["value", "expected"],
    (
        pytest.param((1, {"a": 1}), Variable((), 1, {"a": 1})),
        pytest.param(("d1", [1, 2], {"b": 3}), Variable("d1", [1, 2], {"b": 3})),
    ),
)
def test_as_variable(value, expected):
    actual = transformers.as_variable(value)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["mapping", "expected"],
    (
        pytest.param(
            ({}, {"a": 1}), Group(path=None, url=None, data={}, attrs={"a": 1}), id="group_attrs"
        ),
        pytest.param(
            {"a": (1, {})},
            Group(path=None, url=None, data={"a": Variable((), 1, {})}, attrs={}),
            id="variables",
        ),
        pytest.param(
            {"a": ({}, {"b": 2})},
            Group(
                path=None,
                url=None,
                data={"a": Group(path=None, url=None, data={}, attrs={"b": 2})},
                attrs={},
            ),
            id="subgroups",
        ),
        pytest.param(
            {"a": ({"c": ("d", [1, 2], {})}, {"b": 2})},
            Group(
                path=None,
                url=None,
                data={
                    "a": Group(
                        path=None, url=None, data={"c": Variable(["d"], [1, 2], {})}, attrs={"b": 2}
                    )
                },
                attrs={},
            ),
            id="subgroups-variables",
        ),
    ),
)
def test_as_group(mapping, expected):
    actual = transformers.as_group(mapping)

    assert_identical(actual, expected)
