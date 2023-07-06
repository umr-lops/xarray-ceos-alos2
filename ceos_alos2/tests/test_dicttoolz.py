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
