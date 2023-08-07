import pytest

from ceos_alos2 import utils


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        ("aaceajde", ["a", "c", "e", "j", "d"]),
        ("baebdwea", ["b", "a", "e", "d", "w"]),
    ),
)
def test_unique(data, expected):
    actual = utils.unique(data)

    assert actual == expected
