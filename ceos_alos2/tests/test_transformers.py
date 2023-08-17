import pytest

from ceos_alos2 import transformers


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
