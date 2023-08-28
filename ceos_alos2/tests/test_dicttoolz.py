import copy

import pytest
from tlz.functoolz import identity

from ceos_alos2 import dicttoolz


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        pytest.param(
            {1: 0, 2: 1, 3: 2},
            ({3: 2}, {1: 0, 2: 1}),
        ),
        pytest.param(
            {1: 0, 3: 0, 2: 1},
            ({}, {1: 0, 3: 0, 2: 1}),
        ),
    ),
)
def test_itemsplit(data, expected):
    predicate = lambda item: item[0] % 2 == 1 and item[1] != 0

    actual = dicttoolz.itemsplit(predicate, data)
    assert actual == expected


def test_valsplit():
    data = {0: 1, 1: 0, 2: 2}
    actual = dicttoolz.valsplit(lambda v: v != 0, data)
    expected = ({0: 1, 2: 2}, {1: 0})

    assert actual == expected


def test_keysplit():
    data = {0: 1, 1: 0, 2: 2}
    actual = dicttoolz.keysplit(lambda k: k % 2 == 0, data)
    expected = ({0: 1, 2: 2}, {1: 0})

    assert actual == expected


@pytest.mark.parametrize("default", [False, None, object()])
@pytest.mark.parametrize(
    "mappings",
    (
        [{}, {}],
        [{"a": 1}, {}],
        [{}, {"a": 1}],
        [{"a": 1}, {"a": 1}],
        [{"a": 1}, {"b": 1}],
    ),
)
def test_zip_default(mappings, default):
    zipped = dicttoolz.zip_default(*mappings, default=default)

    assert all(
        key not in mappings[index]
        for key, seq in zipped.items()
        for index, value in enumerate(seq)
        if value is default
    )


@pytest.mark.parametrize("keys", (list("ce"), list("af")))
def test_dissoc(keys):
    mapping = {"a": 1, "b": 2, "c": 3, "e": 4, "f": 5}

    actual = dicttoolz.dissoc(keys, mapping)
    expected = {k: v for k, v in mapping.items() if k not in keys}

    assert actual == expected


@pytest.mark.parametrize(
    ["key", "value", "expected"],
    (
        pytest.param("b", "abc", {"a": 1, "b": "abc"}),
        pytest.param("c", 2, {"a": 1, "c": 2}),
    ),
)
def test_assoc(key, value, expected):
    mapping = {"a": 1}
    actual = dicttoolz.assoc(key, value, mapping)

    assert actual == expected


@pytest.mark.parametrize(
    ["funcs", "default", "expected"],
    (
        pytest.param({"a": int, "b": str, "c": float}, identity, {"a": 1, "b": "6.4", "c": 4.0}),
        pytest.param({"a": int, "c": float}, identity, {"a": 1, "b": 6.4, "c": 4.0}),
        pytest.param({"b": str}, lambda x: x * 2, {"a": "11", "b": "6.4", "c": 8}),
    ),
)
def test_apply_to_items(funcs, default, expected):
    mapping = {"a": "1", "b": 6.4, "c": 4}

    actual = dicttoolz.apply_to_items(funcs, mapping, default=default)

    assert actual == expected


@pytest.mark.parametrize(
    ["instructions", "expected"],
    (
        pytest.param({("b", "d"): ["a"]}, {"a": 1, "b": {"c": 2, "d": 1}}, id="multiple_dest"),
        pytest.param({("d",): ["b", "c"]}, {"a": 1, "b": {"c": 2}, "d": 2}, id="multiple_src"),
        pytest.param({("d",): ["e"]}, {"a": 1, "b": {"c": 2}}, id="missing"),
        pytest.param({("d",): ["e", "f"]}, {"a": 1, "b": {"c": 2}}, id="missing_multiple"),
    ),
)
def test_copy_items(instructions, expected):
    mapping = {"a": 1, "b": {"c": 2}}
    copied = copy.deepcopy(mapping)

    actual = dicttoolz.copy_items(instructions, mapping)

    assert mapping == copied
    assert actual == expected


@pytest.mark.parametrize(
    ["instructions", "expected"],
    (
        pytest.param({("b", "d"): ["a"]}, {"b": {"c": 2, "d": 1}}, id="multiple_dest"),
        pytest.param({("d",): ["b", "c"]}, {"a": 1, "b": {}, "d": 2}, id="multiple_src"),
        pytest.param({("d",): ["e"]}, {"a": 1, "b": {"c": 2}}, id="missing"),
        pytest.param({("d",): ["e", "f"]}, {"a": 1, "b": {"c": 2}}, id="missing_multiple"),
    ),
)
def test_move_items(instructions, expected):
    mapping = {"a": 1, "b": {"c": 2}}
    copied = copy.deepcopy(mapping)

    actual = dicttoolz.move_items(instructions, mapping)

    assert mapping == copied
    assert actual == expected


@pytest.mark.parametrize(
    ["key", "expected"],
    (
        pytest.param("a", True, id="flat-existing"),
        pytest.param("z", False, id="flat-missing"),
        pytest.param("b.c", True, id="nested_dot-existing"),
        pytest.param("a.b", False, id="nested_dot-missing"),
        pytest.param(["b", "d", "e"], True, id="nested_list-existing"),
        pytest.param(["a", "b"], False, id="nested_list-missing"),
    ),
)
def test_key_exists(key, expected):
    mapping = {"a": 1, "b": {"c": 2, "d": {"e": 4}}}

    actual = dicttoolz.key_exists(key, mapping)
    assert actual == expected
