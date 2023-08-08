import pytest

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
